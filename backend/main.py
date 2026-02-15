from src.api import setup_api

db_path = 'db.db'
images_path = 'Images'
app = setup_api(db_path, images_path)
