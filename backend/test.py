from sentence_transformers import SentenceTransformer, util
from PIL import Image

print('Loading transformer...')
model = SentenceTransformer('clip-ViT-B-32')
print('Transformer loaded.')

candidate_tags = ["abstract", "orange", "leaves", "light", "sunset", "dog", "forest", "city skyline", "food", "portrait", "ocean", "person", "persons", "sdlfksjdflkj", "minecraft"]
tag_embeddings = model.encode(candidate_tags)

img_path = "Images/mc.png"
image_embedding = model.encode(Image.open(img_path))

cos_scores = util.cos_sim(image_embedding, tag_embeddings)[0]

print(util.cos_sim(image_embedding, tag_embeddings))

print(cos_scores)

top_results = cos_scores.topk(k=3)

print(f"Tags for {img_path}:")
for score, idx in zip(top_results[0], top_results[1]):
    print(f"- {candidate_tags[idx]} ({score:.2f} confidence)")
