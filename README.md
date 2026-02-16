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
- Search for the n best image matches from a text prompt.
- Query n images around (timewise) an image, matching specific tags

### Running the backend

- Install Python3
- `pip install -r requirements.txt`
- Run `main.py` with Python3

## Runnign the frontend

- Run or host the files in `frontend/`
- Select the __full__ URL (including the protocol) to the backend.
  You can change this later via a setting in the dashboard.
- Press buttons idk

## Possible future improvements

- Backend: force local model
- Videos support?
