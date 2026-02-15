# media-db
Image indexing and retrieval with CLIP.

## Backend

### Features
- Run CLIP locally to generate an embedding and tags for an image.
  These tags, as well as extra ones for the date and subfolders, are stored
  inside a database and associated with the image.
- Add an image to the list of images, generate its tags and insert it into the
  database.
- Update the list of tags, which will remove or potentially add related tags
  and their usages inside the database.
- Manually add and remove an image's tags.
- Search for an image using tags.
- Search for image matches using text prompts.

### Running the backend

- Install Python3
- `pip install -r requirements.txt`
- Run `main.py` with Python3

## Roadmap

- Yaml roadmap for restful api
- Implement all endpoints
- Frontend
- Videos?
