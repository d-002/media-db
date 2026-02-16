from contextlib import asynccontextmanager
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .model import Model
from .persistence import Persistence

def setup_api(db_path: str, images_path: str,
              cross_origin: list[str] | None = None):
    model = Model()
    db = Persistence(db_path, images_path, model, verbose=True)
    db.sync()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield

        db.close()

    app = FastAPI(lifespan=lifespan)

    if cross_origin is not None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cross_origin,
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )

    @app.get('/image/{image_id}/data',
             summary='Get image data',
             description='Retrieve an image\'s data from its id.')
    async def image_data_from_id(image_id: int) -> FileResponse:
        res = db.get_image_path_for_data(image_id)
        return FileResponse(res)

    @app.get('/image/{image_id}/info',
             summary='Get image info',
             description='Retrieve image id, name and timestamp from its id.')
    async def image_info_from_id(image_id: int) -> dict:
        return db.safe_image(db.image_info_from_id(image_id))

    @app.delete('/image/{image_id}/delete',
                summary='Delete image',
                description='Delete image from the database and the local '
                            'files from its id.')
    async def delete_image(image_id: int) -> None:
        db.delete_image_everywhere(image_id)

    @app.get('/image/{image_id}/tags',
             summary='Get image tags',
             description='Get a list of all the target image\'s tags id+name.')
    async def get_image_tags(image_id: int) -> list[dict]:
        return [db.safe_tag(tag) for tag in db.get_image_tags(image_id)]

    @app.get('/images/list-ids',
             summary='Get all image ids',
             description='Get a list with the ids of all the images in the '
                         'database.')
    async def all_image_ids() -> list[int]:
        return db.all_image_ids()

    @app.post('/images/new',
              summary='Add an image',
              description='Upload an image with its name, creation or '
                          'modification timestamp and raw data to the '
                          'database. The image is also written as a file.')
    async def add_image(name: str = Form(...), timestamp: float = Form(...),
                        file: UploadFile = File(...)) -> dict[str, int]:
        image_id = db.add_image_everywhere(name, timestamp, file)
        return {'image_id': image_id}

    @app.post('/images/filter',
              summary='Filter all images with tags',
              description='Get images id+name for all the images that are '
                          'associated with all the given tags.')
    async def filter_all_images(tag_ids: list[int]) -> list[dict]:
        return [db.safe_image(image) for image in db.filter_all_images(tag_ids)]

    @app.post('/images/around',
              summary='Get images around chronologically',
              description='Get a list of 2n-1 images chronologically closest '
                          'to the target image, n-1 before and after.')
    async def filter_around(image_id: int, tag_ids: list[int],
                            n: int) -> list[dict]:
        return [db.safe_image(image)
                for image in db.filter_around(image_id, tag_ids, n)]

    @app.get('/images/date',
             summary='Get closest image to timestamp',
             description='Get the image whose date is the closest to the given '
                     'timestamp.')
    async def closest_to_date(timestamp: int) -> dict:
        return db.safe_image(db.closest_to_date(timestamp))

    @app.get('/images/prompt',
             summary='Prompt matching images with AI',
             description='Match images inside the database whose embeddings '
                         'match that of the supplied prompt.')
    async def prompt_n_best(prompt: str, n: int) -> list[dict]:
        return [{'score': score, **db.safe_image(image)}
                for score, image in db.prompt_n_best(prompt, n)]

    @app.delete('/tag/{tag_id}/delete',
                summary='Delete tag',
                description='Delete tag from the database by id. '
                            'Any assignation of it will be discarded.')
    async def delete_tag(tag_id: int) -> None:
        db.delete_tag_everywhere(tag_id)

    @app.get('/tags/list',
             summary='List tags',
             description='Get a list of id+name for all the tags.')
    async def all_tags() -> list[dict]:
        return [db.safe_tag(tag) for tag in db.all_tags()]

    @app.post('/tags/new',
              summary='Create new tag',
              description='Create a new tag with the specified name.')
    async def add_tag(tag_name: str) -> dict[str, int]:
        tag_id = db.new_tag(tag_name)
        return {'tag_id': tag_id}

    @app.post('/assign/{image_id}/{tag_id}',
              summary='Assign tag to image',
              description='Assign a tag to an image. Both must be present.')
    async def assign(image_id: int, tag_id: int) -> None:
        db.assign_tag(image_id, tag_id)

    @app.post('/unassign/{image_id}/{tag_id}',
              summary='Unassign tag',
              description='Unassign a tag to an image.')
    async def unassign(image_id: int, tag_id: int) -> None:
        db.unassign_tag(image_id, tag_id)

    @app.delete('/reset',
                summary='Reset database',
                description='Reset the entire database and parse images from '
                            'disk again with the set of default tags.')
    async def reset() -> dict[str, int]:
        db.reset_db()
        return db.sync()

    @app.get('/sync',
             summary='Sync database',
             description='Sync the database for added image files.')
    async def sync() -> dict[str, int]:
        return db.sync()

    return app
