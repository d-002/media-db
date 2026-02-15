import sqlite3
import numpy as np

from .model import Model

class DataBase:
    basic_tags = [
            'person', 'animal', 'landscape', 'winter', 'spring', 'summer',
            'autumn', 'day', 'night', 'red', 'orange', 'yellow', 'green',
            'blue', 'purple', 'brown', 'black', 'gray', 'white']

    # minimum sim score (0 to 1) to automatically assign a tag to an image
    min_sim_score = .25

    def __init__(self, db_file: str, model: Model, verbose: bool = False):
        self.db_file = db_file
        self.model = model
        self.verbose = verbose

        self._log('Connecting to database.')

        self.con = sqlite3.connect(db_file)
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()

        #self.reset_db()
        self.init_db()

        self._log()

    def _log(self, *args, **kwargs) -> None:
        if self.verbose:
            print(*args, **kwargs)

    def close(self) -> None:
        self._log('Closing database connection.')
        self.con.close()

    def init_db(self) -> None:
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='images'")
        exists = self.cur.fetchone()

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY,
            hash TEXT,
            path TEXT,
            embedding BLOB
        )""")
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY,
            name TEXT,
            embedding BLOB
        )
        """)
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS tags_join (
            id INTEGER PRIMARY KEY,
            image_id INTEGER,
            tag_id INTEGER,
            FOREIGN KEY(image_id) REFERENCES images(id),
            FOREIGN KEY(tag_id) REFERENCES tags(id)
        )
        """)

        self.con.commit()

        if not exists:
            self._log('Adding basic tags because there are none.')

            for tag in DataBase.basic_tags:
                self.add_tag(tag)

        self.add_tag('minecraft')

    def reset_db(self) -> None:
        self._log('Resetting database.')
        self.cur.execute('DROP TABLE IF EXISTS images')
        self.cur.execute('DROP TABLE IF EXISTS tags')
        self.cur.execute('DROP TABLE IF EXISTS tags_join')
        self.con.commit()

        self.init_db()

    def contains_image_hash(self, h: str) -> bool:
        self.cur.execute("""
        SELECT images.id
        FROM images
        WHERE images.hash = ?
        """, [h])
        return self.cur.fetchone() is not None

    def contains_tag(self, name: str) -> bool:
        self.cur.execute("""
        SELECT tags.id
        FROM tags
        WHERE tags.name = ?
        """, [name])
        return self.cur.fetchone() is not None

    def add_image(self, h: str, path: str) -> int | None:
        embedding = self.model.embed_image(path)
        embedding_blob = embedding.tobytes()

        self.cur.execute("""
        INSERT INTO images (hash, path, embedding)
        VALUES (?, ?, ?)""", [h, path, embedding_blob])
        self.con.commit()

        return self.cur.lastrowid

    def add_tag(self, name: str) -> int | None:
        embedding = self.model.embed_tag(name)
        embedding_blob = embedding.tobytes()

        self.cur.execute("""
        INSERT INTO tags (name, embedding)
        VALUES (?, ?)""", [name, embedding_blob])
        self.con.commit()

        return self.cur.lastrowid

    def assign_tag(self, image_id: int, hash_id: int) -> int | None:
        self.cur.execute("""
        INSERT INTO tags_join (image_id, tag_id)
        VALUES (?, ?)
        """, [image_id, hash_id])
        self.con.commit()

        return self.cur.lastrowid

    def try_assign_tags(self, img_id: int):
        self.cur.execute("""
        SELECT images.*
        FROM images
        WHERE images.id = ?
        """, [img_id])

        img = self.cur.fetchone()

        self.cur.execute("""
        SELECT tags.*
        FROM tags
        JOIN tags_join
        WHERE tags_join.image_id = ?
        """, [img_id])
        assigned_tags = self.cur.fetchall()
        assigned_tag_ids = [tag['id'] for tag in assigned_tags]

        for tag in self.all_tags():
            tag_id = tag['id']
            if tag_id in assigned_tag_ids:
                continue

            img_embedding = np.frombuffer(img['embedding'], dtype=np.float32)
            tag_embedding = np.frombuffer(tag['embedding'], dtype=np.float32)

            score = self.model.sim_score(img_embedding, tag_embedding)[0]

            if score > DataBase.min_sim_score:
                self._log(f'- Adding tag {tag['name']} ({int(score * 100)}%).')
                self.assign_tag(img_id, tag_id)

    def all_images(self) -> list[dict]:
        self.cur.execute("""
        SELECT images.*
        FROM images
        """)
        return self.cur.fetchall()

    def all_tags(self) -> list[dict]:
        self.cur.execute("""
        SELECT tags.*
        FROM tags
        """)
        return self.cur.fetchall()

    def remove_image(self, id: int) -> None:
        self.cur.execute("""
        DELETE FROM images
        WHERE images.id = ?
        """, [id])
        self.cur.execute("""
        DELE FROM tags_join
        WHERE tags_join.image_id = ?
        """, [id])
        self.con.commit()

    def remove_tag(self, id: int) -> None:
        self.cur.execute("""
        DELETE FROM tags
        WHERE tags.id = ?
        """, [id])
        self.cur.execute("""
        DELE FROM tags_join
        WHERE tags_join.tag_id = ?
        """, [id])
        self.con.commit()
