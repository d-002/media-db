import os
import re
import shutil
import numpy as np
from sys import stderr
from fastapi import UploadFile, HTTPException

from .sql_wrapper import DataBase
from .files import FilePath, list_files
from .model import Model

class Persistence(DataBase):
    def __init__(self, db_file: str, images_dir: str, model: Model,
                 verbose: bool = False):
        super().__init__(db_file, model, verbose)
        self.images_dir = images_dir

    def _error(self, error_code: int, msg: str):
        print(f'Error: {msg}', file=stderr)
        raise HTTPException(error_code, msg)

    def sync(self):
        self._log('Syncing images.')

        total = 0
        added = 0
        deleted = 0

        present = list_files(self.images_dir)
        for file in present:
            if self._get_image_from_path(file.path) is None:
                self._new_image(file, None)
                added += 1
            total += 1

        present_paths = [file.path for file in present]
        for file in self._all_images():
            path = file['path']
            if path not in present_paths:
                self._remove_image(path)
                deleted += 1

        self._log(f'Sync summary: {total} total, {added} additions, '
                  f'{deleted} deletions.')

    def all_images(self) -> list[int]:
        return [image['id'] for image in self._all_images()]

    def all_tags(self) -> list[int]:
        return [tag['id'] for tag in self._all_tags()]

    def get_tagname_from_id(self, id: int) -> str:
        tag = self._get_tag_from_id(id)
        if tag is None:
            self._error(404, 'Tag not found.')

        return tag['name']

    def add_image_everywhere(self, name, timestamp: float,
                             upload_file: UploadFile) -> int:
        if upload_file.filename is None:
            self._error(400, 'Incorrect file name.')

        # sanitize filename
        name = re.sub('[^\\w\\s\\-+=_!,;.\'"]+', '_', name)
        path = os.path.join(self.images_dir, name)

        # add to disk
        with open(path, 'wb') as f:
            shutil.copyfileobj(upload_file.file, f)
        # alter metadata
        os.utime(path, (timestamp, timestamp))

        # add to database
        file = FilePath(upload_file.filename)
        return self._new_image(file, timestamp)

    def _new_image(self, file: FilePath, timestamp: float | None) -> int:
        if self._get_image_from_path(file.path) is not None:
            self._error(409, f'{file.path} already present.')

        print(f'-> Adding new image \'{file.path}\'.')

        self._log('Generating new tags from file path.')
        for dirname in file.dirs:
            if dirname not in self.all_tags():
                self.add_tag(dirname, True)

        self._log('Automatically assigning tags in new image.')
        if timestamp is None:
            timestamp = os.path.getmtime(file.path)
        id = self._add_image(file.path, timestamp)
        if id is None:
            self._error(500, 'Failed to add image.')

        self._log('Generating tags for new image.')
        self._try_assign_tags(id)

        self._log()
        return id

    def add_tag(self, name: str, silent: bool = False) -> int:
        if self._get_tag_from_name(name) is not None:
            if silent:
                return -1
            self._error(409, 'Tag already present.')

        print(f'-> Adding new tag {name}')
        id = self._add_tag(name)
        if id is None:
            self._error(500, 'Failed to create tag.')

        self._log('Updating tags for all images.')
        for image_id in self.all_images():
            self._try_assign_tags(image_id)

        self._log()
        return id

    def remove_image_everywhere(self, id: int) -> None:
        image = self._get_image_from_id(id)
        if image is None:
            self._error(404, 'Image not present.')

        path = image['path']
        print(f'Removing image {path}')

        # remove from database
        self._remove_image(image['id'])
        # remove from disk
        os.remove(path)

    def remove_tag_everywhere(self, id: int) -> None:
        tag = self._get_tag_from_id(id)
        if tag is None:
            self._error(404, 'Tag not present.')

        id = tag['id']
        self._remove_tag(id)

    def assign_tag(self, image_id: int, tag_id: int) -> None:
        image = self._get_image_from_id(image_id)
        tag = self._get_tag_from_id(tag_id)
        if image is None or tag is None:
            self._error(404, 'Image or tag not present.')

        join = self._get_join_from_ids(image_id, tag_id)
        if join is not None:
            self._error(409, 'Image already has this tag.')

        self._assign_tag(image_id, tag_id)

    def unassign_tag(self, image_id: int, tag_id: int) -> None:
        image = self._get_image_from_id(image_id)
        tag = self._get_tag_from_id(tag_id)
        if image is None or tag is None:
            self._error(404, 'Image or tag not present.')

        join = self._get_join_from_ids(image_id, tag_id)
        if join is None:
            self._error(404, 'Image does not have this tag.')

        self._unassign_tag(image_id, tag_id)

    def get_image_path_for_data(self, image_id: int) -> str:
        image = self._get_image_from_id(image_id)
        if image is None:
            self._error(404, 'Image not present.')

        return image['path']

    def prompt_n_best(self, prompt: str, n: int) -> list[int]:
        l: list[tuple[int, float]] = []
        prompt_embedding = self.model.embed_text(prompt)

        for image in self._all_images():
            img_embedding = np.frombuffer(image['embedding'], dtype=np.float32)
            score = self.model.sim_score(img_embedding, prompt_embedding)[0]
            l.append((image['id'], score))

        return list(map(lambda t: t[0], sorted(l, key=lambda t: -t[1])[:n]))

    def filter_around(self, image_id: int, tag_ids: list[int],
                      n: int) -> list[int]:
        image = self._get_image_from_id(image_id)
        if image is None:
            self._error(404, 'Image not present.')

        return self._filter_around(image['timestamp'], tag_ids, n)
