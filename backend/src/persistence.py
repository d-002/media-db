import os
import re
import numpy as np
from sys import stderr

from .sql_wrapper import DataBase
from .files import FilePath, list_files
from .model import Model

class Persistence(DataBase):
    def __init__(self, db_file: str, images_dir: str, model: Model,
                 verbose: bool = False):
        super().__init__(db_file, model, verbose)
        self.images_dir = images_dir
        self.last_error = None

    def _error(self, msg: str):
        self.last_error = msg
        print(f'Error: {msg}', file=stderr)

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
        for file in self.all_images():
            path = file['path']
            if path not in present_paths:
                self._remove_image(path)
                deleted += 1

        self._log(f'Sync summary: {total} total, {added} additions, '
                  f'{deleted} deletions.')

    def add_image_everywhere(self, name, data: bytes,
                             timestamp: float) -> int | None:
        # sanitize filename
        name = re.sub('[^\\w\\s\\-+=_!,;.\'"]+', '_', name)
        path = os.path.join(self.images_dir, name)

        # add to disk
        with open(path, 'wb') as f:
            f.write(data)
        # alter metadata
        os.utime(path, (timestamp, timestamp))

        # add to database
        file = FilePath(path)
        return self._new_image(file, timestamp)

    def _new_image(self, file: FilePath, timestamp: float | None) -> int | None:
        if self._get_image_from_path(file.path) is not None:
            self._error(f'{file.path} already present.')
            return None

        print(f'-> Adding new image \'{file.path}\'.')

        existing_tag_names = [tag['name'] for tag in self.all_tags()]
        self._log('Generating new tags from file path.')
        for dirname in file.dirs:
            if dirname not in existing_tag_names:
                self.new_tag(dirname)

        self._log('Automatically assigning tags in new image.')
        if timestamp is None:
            timestamp = os.path.getmtime(file.path)
        id = self._add_image(file.path, timestamp)
        if id is None:
            print('Failed to add image.', file=stderr)
            return None

        self._log('Generating tags for new image.')
        self._try_assign_tags(id)

        self._log()
        return id

    def new_tag(self, name: str) -> int | None:
        if self._get_tag_from_name(name) is not None:
            self._error('Tag already present.')
            return None

        print(f'-> Adding new tag {name}')
        id = self._add_tag(name)

        self._log('Updating tags for all images.')
        for image in self.all_images():
            self._try_assign_tags(image['id'])

        self._log()
        return id

    def remove_image_everywhere(self, id: int) -> bool:
        image = self.get_image_from_id(id)
        if image is None:
            self._error('Image not present.')
            return False

        path = image['path']
        print(f'Removing image {path}')

        # remove from database
        self._remove_image(image['id'])
        # remove from disk
        os.remove(path)

        return True

    def remove_tag_everywhere(self, id: int) -> bool:
        tag = self.get_tag_from_id(id)
        if tag is None:
            self._error('Tag not present.')
            return False

        id = tag['id']
        self._remove_tag(id)
        return True

    def assign_tag(self, image_id: int, tag_id: int) -> bool:
        image = self.get_image_from_id(image_id)
        tag = self.get_tag_from_id(tag_id)
        if image is None or tag is None:
            self._error('Image or tag not present.')
            return False

        self._assign_tag(image_id, tag_id)
        return True

    def get_image_data(self, image_id: int) -> bytes | None:
        image = self.get_image_from_id(image_id)
        if image is None:
            self._error('Image not present.')
            return None

        with open(image['path'], 'rb') as f:
            content = f.read()

        return content

    def prompt_n_best(self, prompt: str, n: int) -> list[int]:
        l: list[tuple[int, float]] = []
        prompt_embedding = self.model.embed_text(prompt)

        for image in self.all_images():
            img_embedding = np.frombuffer(image['embedding'], dtype=np.float32)
            score = self.model.sim_score(img_embedding, prompt_embedding)[0]
            l.append((image['id'], score))

        return list(map(lambda t: t[0], sorted(l, key=lambda t: -t[1])[:n]))

    def filter_around(self, image_id: int, tag_ids: list[int], n: int) -> list[int] | None:
        image = self.get_image_from_id(image_id)
        if image is None:
            self._error('Image not present.')
            return None

        return self._filter_around(image['timestamp'], tag_ids, n)
