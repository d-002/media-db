from PIL import Image
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, util

class Model:
    model_name = 'clip-ViT-B-32'

    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(Model.model_name, device=device)

    def embed_tag(self, tag: str) -> np.ndarray:
        return self.model.encode(tag)

    def embed_image(self, path: str) -> np.ndarray:
        return self.model.encode(Image.open(path))

    def sim_score(self, t1: np.ndarray, t2: np.ndarray) -> np.ndarray:
        return util.cos_sim(t1, t2)[0]
