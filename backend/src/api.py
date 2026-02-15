from contextlib import asynccontextmanager
from fastapi import FastAPI, File, Form, UploadFile, responses

from .model import Model
from .persistence import Persistence

def setup_api(db_path: str, images_path: str):
    model = Model()
    db = Persistence(db_path, images_path, model, verbose=True)
    db.sync()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield

        app.state.db.close()
        print('Database connection closed.')

    app = FastAPI(lifespan=lifespan)

    @app.get("/image/{image_id}/data")
    async def image_data_from_id(image_id: int):
        res = db.get_image_path_for_data(image_id)
        return responses.FileResponse(res)

    @app.get("/image/{image_id}/info")
    async def image_info_from_id(image_id: int):
        return db.image_info_from_id(image_id)

    @app.delete("/image/{image_id}/delete")
    async def remove_image(image_id: int):
        db.remove_image_everywhere(image_id)

    @app.get("/image/{image_id}/tags")
    async def get_image_tags(image_id: int):
        tag_ids = db.get_image_tags(image_id)
        return {'tag_ids': tag_ids}

    @app.get("/images/list")
    async def all_images():
        image_ids = db.all_images()
        return {'image_ids': image_ids}

    @app.post("/images/add")
    async def add_image(path: str = Form(...), date: float = Form(...),
                        file: UploadFile = File(...)):
        image_id = db.add_image_everywhere(path, date, file)
        return {'image_id': image_id}

    @app.post("/images/filter")
    async def filter_images(tag_ids: list[int]):
        image_ids = db.filter_images(tag_ids)
        return {'image_ids': image_ids}

    @app.post("/images/around")
    async def filter_around(image_id: int, tag_ids: list[int], n: int):
        image_ids = db.filter_around(image_id, tag_ids, n)
        return {'image_ids': image_ids}

    @app.get("/images/best")
    async def prompt_n_best(prompt: str, n: int):
        image_ids = db.prompt_n_best(prompt, n)
        return {'image_ids': image_ids}

    @app.get("/tag/{tag_id}/info")
    async def tag_info_from_id(tag_id: int):
        return db.tag_info_from_id(tag_id)

    @app.delete("/tag/{tag_id}/remove")
    async def remove_tag(tag_id: int):
        db.remove_tag_everywhere(tag_id)

    @app.get("/tags/list")
    async def all_tags():
        tag_ids = db.all_tags()
        return {'tag_ids': tag_ids}

    @app.post("/tags/add/{tag_name}")
    async def add_tag(tag_name: str):
        tag_id = db.add_tag(tag_name)
        return {'tag_id': tag_id}

    @app.post("/assign/{image_id}/{tag_id}")
    async def assign(image_id: int, tag_id: int):
        db.assign_tag(image_id, tag_id)

    @app.post("/unassign/{image_id}/{tag_id}")
    async def unassign(image_id: int, tag_id: int):
        db.unassign_tag(image_id, tag_id)

    @app.delete("/empty")
    async def reset():
        db.reset_db()

    return app
