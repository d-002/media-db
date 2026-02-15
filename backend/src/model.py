from PIL import Image
from torch import Tensor
from sentence_transformers import SentenceTransformer, util

class Model:
    model_name = 'clip-ViT-B-32'

    def __init__(self):
        self.model = SentenceTransformer(Model.model_name)

    def embed_tag(self, tag: str) -> Tensor:
        return self.model.encode(tag)

    def embed_image(self, path: str) -> Tensor:
        return self.model.encode(Image.open(path))

    def sim_score(self, t1: Tensor, t2: Tensor) -> Tensor:
        return util.cos_sim(t1, t2)[0]
