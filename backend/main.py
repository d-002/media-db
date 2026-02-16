from src.api import setup_api

origins = [
    "http://127.0.0.1:8080",
    "http://localhost:8080",
]

db_path = 'db.db'
images_path = '/mnt/nas/PHOTOS'
app = setup_api(db_path, images_path, origins)
