from sys import stderr
from hashlib import sha256

from .sql_wrapper import DataBase
from .files import FilePath, list_files
from .model import Model

class Persistence(DataBase):
    def __init__(self, db_file: str, images_dir: str, model: Model,
                 verbose: bool = False):
        super().__init__(db_file, model, verbose)
        self.images_dir = images_dir

    def myhash(self, file: FilePath):
        return sha256(file.path.encode()).hexdigest()

    def sync(self):
        self._log('Syncing images.')

        total = 0
        added = 0
        for file in list_files(self.images_dir):
            h = self.myhash(file)
            if not self.contains_image_hash(h):
                self.new_image(file)
                added += 1
            total += 1

        self._log(f'Sync summary: {total} total, including {added} additions.')

    def new_image(self, file: FilePath) -> bool:
        h = self.myhash(file)
        if self.contains_image_hash(h):
            print(f'Error: {file.path} already present.', file=stderr)
            return False

        print(f'-> Adding new image \'{file.path}\'.')

        existing_tag_names = [tag['name'] for tag in self.all_tags()]
        self._log('Generating new tags from file path.')
        for dirname in file.dirs:
            if dirname not in existing_tag_names:
                self.new_tag(dirname)

        self._log('Automatically assigning tags in new image.')
        id = self.add_image(h, file.path)
        if id is None:
            print('Failed to add image.', file=stderr)
            return False

        self._log('Generating tags for new image.')
        self.try_assign_tags(id)

        self._log()
        return True

    def new_tag(self, name: str) -> bool:
        if self.contains_tag(name):
            print('Error: tag already present.')
            return False

        print(f'-> Adding new tag {name}')
        self.add_tag(name)

        self._log('Updating tags for all images.')
        for image in self.all_images():
            self.try_assign_tags(image['id'])

        self._log()
        return True
