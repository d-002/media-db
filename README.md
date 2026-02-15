# media-db
Image indexing and retrieval with CLIP.

Backend features:
- Run CLIP locally to generate an embedding and tags for an image.
  These tags, as well as extra ones for the date and subfolders, are stored
  inside a database and associated with the image.
- Add an image to the list of images, generate its tags and insert it into the
  database.
- Update the list of tags, which will remove or potentially add related tags
  inside the database.
- Manually associate tags for an image.
- Search for an image using tags.
- Search for image matches using text prompts.

## Roadmap

**Done**

**To do**

- Set up CLIP
- Set up Python and database in backend
- Set up tests, CI?
- Yaml roadmap for restful api
- Implement all endpoints

- Frontend

- Videos?
