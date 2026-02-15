from src.model import Model
from src.persistence import Persistence

if __name__ == '__main__':
    model = Model()

    db_path = 'db.db'
    images_path = 'Images'

    db = Persistence(db_path, images_path, model, verbose=True)
    try:
        db.sync()
    except KeyboardInterrupt:
        print('Keyboard interrupt, stopping.')
    finally:
        db.close()
