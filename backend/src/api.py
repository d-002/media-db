from .persistence import Persistence

class Api:
    def __init__(self, persistence: Persistence):
        self.persistence = persistence

    def reset(self):
        self.persistence.reset_db()

    def image_data_from_id(self, id: int):
        res = self.persistence.get_image_data(id)

    def tag_from_id(self, id: int):
        res = self.persistence.get_tag_from_id(id)

    def all_images(self):
        res = self.persistence.all_images()

    def all_tags(self):
        res = self.persistence.all_tags()

    def add_image(self, path: str, data: bytes, date: int):
        id = self.persistence.add_image_everywhere(path, data, date)

    def remove_image(self, id: int):
        ok = self.persistence.remove_image_everywhere(id)

    def add_tag(self, name: str):
        id = self.persistence.new_tag(name)

    def remove_tag(self, id: int):
        ok = self.persistence.remove_tag_everywhere(id)

    def assign(self, image_id: int, tag_id: int):
        ok = self.persistence.assign_tag(image_id, tag_id)

    def get_image_tags(self, image_id: int):
        res = self.persistence.get_image_tags(image_id)

    def filter_images(self, tag_ids: list[int]):
        res = self.persistence.filter_images(tag_ids)

    def filter_around(self, image_id: int, tag_ids: list[int], n: int):
        res = self.persistence.filter_around(image_id, tag_ids, n)

    def prompt_n_best(self, prompt: str, n: int):
        res = self.persistence.prompt_n_best(prompt, n)
