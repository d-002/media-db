import os
import re
import shutil
import numpy as np
from sys import stderr
from fastapi import UploadFile, HTTPException

from .sql_wrapper import DataBase
from .files import FilePath, list_files
from .model import Model

extensions = ['jpg', 'jpeg', 'jfif', 'png', 'bmp', 'gif']

def is_image(path: str) -> bool:
    ext = os.path.splitext(path)[-1].lower().strip()
    while ext.startswith('.'):
        ext = ext[1:]

    return len(ext) > 0 and ext in extensions

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

        added = 0
        deleted = 0

        present = list_files(self.images_dir)
        total = len(present)
        for i, file in enumerate(present):
            if not is_image(file.path):
                self._log(f'Skipping {file.name}')
                continue

            if self._get_image_from_path(file.path) is None:
                self._new_image(file, None)
                added += 1

            print(f'Indexing {(i + 1) / total * 100:.2f}% complete.')

        present_paths = [file.path for file in present]
        for file in self._all_images():
            path = file['path']
            if path not in present_paths:
                self._delete_image(path)
                deleted += 1

        self._log(f'Sync summary: {total} total, {added} additions, '
                  f'{deleted} deletions.')

        return {'total': total, 'added': added, 'deleted': deleted}

    def all_image_ids(self) -> list[int]:
        return [image['id'] for image in self._all_images()]

    def safe_image(self, image: dict) -> dict:
        return {'id': image['id'], 'path': image['path'],
                 'timestamp': image['timestamp']}

    def safe_tag(self, tag: dict) -> dict:
        return {'id': tag['id'], 'name': tag['name']}

    def image_info_from_id(self, id: int) -> dict:
        image = self._get_image_from_id(id)
        if image is None:
            self._error(404, 'Image not found.')

        return image

    def add_image_everywhere(self, name: str, timestamp: float,
                             upload_file: UploadFile) -> int:
        if upload_file.filename is None:
            self._error(400, 'Incorrect file name.')

        if not is_image(upload_file.filename):
            self._error(400, 'File type is not supported.')

        # sanitize filename
        name = re.sub('[^\\w\\s\\-+=_!,;.\'"]+', '_', name)
        path = os.path.join(self.images_dir, name)

        # add to disk
        with open(path, 'wb') as f:
            shutil.copyfileobj(upload_file.file, f)
        # alter metadata
        os.utime(path, (timestamp, timestamp))

        # add to database
        file = FilePath(path)
        return self._new_image(file, timestamp)

    def _new_image(self, file: FilePath, timestamp: float | None) -> int:
        print(f'-> Adding new image \'{file.path}\'.')
        if timestamp is None:
            timestamp = os.path.getmtime(file.path)
        image_id = self._add_image(file.path, timestamp)
        if image_id is None:
            self._error(500, 'Failed to add image.')

        self._log('Generating tags for new image.')
        self._try_assign_tags(image_id)

        self._log('Generating new tags from file path and assigning.')
        for dirname in file.dirs:
            tag_id = self._get_tag_from_name(dirname)
            if tag_id is None:
                tag_id = self.new_tag(dirname, True)
            else:
                tag_id = tag_id['id']
            self._assign_tag(image_id, tag_id)

        self._log()
        return image_id

    def new_tag(self, name: str, silent: bool = False) -> int:
        # sanitize tag name
        name = re.sub('[^\\w\\s\\-+=_!,;.\'"]+', '_', name)
        name = name.strip()
        if not name:
            self._error(400, "Invalid tag name.");

        if self._get_tag_from_name(name) is not None:
            if silent:
                return -1
            self._error(409, 'Tag already present.')

        print(f'-> Adding new tag \'{name}\'')
        id = self._add_tag(name)
        if id is None:
            self._error(500, 'Failed to create tag.')

        self._log('Updating tags for all images.')
        for image in self._all_images():
            self._try_assign_tags(image['id'])

        return id

    def delete_image_everywhere(self, id: int) -> None:
        image = self._get_image_from_id(id)
        if image is None:
            self._error(404, 'Image not present.')

        path = image['path']
        print(f'Removing image {path}')

        # remove from database
        self._delete_image(image['id'])
        # remove from disk
        os.remove(path)

    def delete_tag_everywhere(self, id: int) -> None:
        tag = self._get_tag_from_id(id)
        if tag is None:
            self._error(404, 'Tag not present.')

        id = tag['id']
        self._delete_tag(id)

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

    def prompt_n_best(self, prompt: str, n: int) -> list[tuple[float, dict]]:
        l = []
        prompt_embedding = self.model.embed_text(prompt)

        for image in self._all_images():
            img_embedding = np.frombuffer(image['embedding'], dtype=np.float32)
            score = self.model.sim_score(img_embedding, prompt_embedding)[0]
            l.append((float(score), image))

        return sorted(l, key=lambda t: -t[0])[:n]

    def filter_around(self, image_id: int, tag_ids: list[int],
                      n: int) -> list[dict]:
        image = self._get_image_from_id(image_id)
        if image is None:
            self._error(404, 'Image not present.')

        before = self._filter_around(image['timestamp'], tag_ids, n, False)
        after = self._filter_around(image['timestamp'], tag_ids, n, True)

        return before + after[1:]
