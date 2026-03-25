import os
from src.api import setup_api

origins = [
    "http://127.0.0.1:8080",
    "http://localhost:8080",
]

db_path = 'db.db'
images_path = os.getenv('IMAGES_PATH')
if not images_path or not os.path.isdir(images_path):
    print('Please provide a valid IMAGES_PATH environment variable')
    exit(1)

app = setup_api(db_path, images_path, origins)
