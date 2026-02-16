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
        self._init_db()

        self._log()

    def _log(self, *args, **kwargs) -> None:
        if self.verbose:
            print(*args, **kwargs)

    def close(self) -> None:
        self._log('Closing database connection.')
        self.con.close()

    def _init_db(self) -> None:
        self.cur.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name='images'""")
        exists = self.cur.fetchone()

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY,
            path TEXT,
            timestamp REAL,
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
                self._add_tag(tag)

            self._add_tag('minecraft')

    def reset_db(self) -> None:
        self._log('Resetting database.')
        self.cur.execute('DROP TABLE IF EXISTS images')
        self.cur.execute('DROP TABLE IF EXISTS tags')
        self.cur.execute('DROP TABLE IF EXISTS tags_join')
        self.con.commit()

        self._init_db()

    def _get_image_from_id(self, id: int) -> dict | None:
        self.cur.execute("""
        SELECT images.*
        FROM images
        WHERE images.id = ?
        """, [id])
        return self.cur.fetchone()

    def _get_image_from_path(self, path: str) -> dict:
        self.cur.execute("""
        SELECT images.*
        FROM images
        WHERE images.path = ?
        """, [path])
        return self.cur.fetchone()

    def _get_tag_from_id(self, id: int) -> dict | None:
        self.cur.execute("""
        SELECT tags.*
        FROM tags
        WHERE tags.id = ?
        """, [id])
        return self.cur.fetchone()

    def _get_tag_from_name(self, name: str) -> dict:
        self.cur.execute("""
        SELECT tags.id
        FROM tags
        WHERE tags.name = ?
        """, [name])
        return self.cur.fetchone()

    def _add_image(self, path: str, timestamp: float) -> int | None:
        embedding = self.model.embed_image(path)
        embedding_blob = embedding.tobytes()

        self.cur.execute("""
        INSERT INTO images (path, timestamp, embedding)
        VALUES (?, ?, ?)""", [path, timestamp, embedding_blob])
        self.con.commit()

        return self.cur.lastrowid

    def _add_tag(self, name: str) -> int | None:
        embedding = self.model.embed_text(name)
        embedding_blob = embedding.tobytes()

        self.cur.execute("""
        INSERT INTO tags (name, embedding)
        VALUES (?, ?)""", [name, embedding_blob])
        self.con.commit()

        return self.cur.lastrowid

    def _assign_tag(self, image_id: int, tag_id: int) -> int | None:
        self.cur.execute("""
        INSERT INTO tags_join (image_id, tag_id)
        VALUES (?, ?)
        """, [image_id, tag_id])
        self.con.commit()

        return self.cur.lastrowid

    def _unassign_tag(self, image_id: int, tag_id: int) -> None:
        self.cur.execute("""
        DELETE FROM tags_join
        WHERE tags_join.image_id = ?
        AND tags_join.tag_id = ?
        """, [image_id, tag_id])
        self.con.commit()

    def _get_join_from_ids(self, image_id: int, tag_id: int) -> dict:
        self.cur.execute("""
        SELECT tags_join.id
        FROM tags_join
        WHERE tags_join.image_id = ?
        AND tags_join.tag_id = ?
        """, [image_id, tag_id])
        return self.cur.fetchone()

    def _try_assign_tags(self, img_id: int):
        self.cur.execute("""
        SELECT images.*
        FROM images
        WHERE images.id = ?
        """, [img_id])

        img = self.cur.fetchone()

        self.cur.execute("""
        SELECT DISTINCT tags.*
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
                self._assign_tag(img_id, tag_id)

    def get_image_tags(self, image_id: int) -> list[dict]:
        self.cur.execute("""
        SELECT DISTINCT
            tags.*
        FROM tags
        JOIN tags_join
        ON tags.id = tags_join.tag_id
        WHERE tags_join.image_id = ?
        """, [image_id])
        return self.cur.fetchall()

    def _all_images(self) -> list[dict]:
        self.cur.execute("""
        SELECT images.*
        FROM images
        ORDER BY images.timestamp DESC
        """)
        return self.cur.fetchall()

    def all_tags(self) -> list[dict]:
        self.cur.execute("""
        SELECT tags.*
        FROM tags
        """)
        return self.cur.fetchall()

    def _delete_image(self, id: int) -> None:
        self.cur.execute("""
        DELETE FROM images
        WHERE images.id = ?
        """, [id])
        self.cur.execute("""
        DELETE FROM tags_join
        WHERE tags_join.image_id = ?
        """, [id])
        self.con.commit()

    def _delete_tag(self, id: int) -> None:
        self.cur.execute("""
        DELETE FROM tags
        WHERE tags.id = ?
        """, [id])
        self.cur.execute("""
        DELETE FROM tags_join
        WHERE tags_join.tag_id = ?
        """, [id])
        self.con.commit()

    def filter_all_images(self, tag_ids: list[int]) -> list[dict]:
        if not tag_ids:
            return self._all_images()

        num_tags = len(tag_ids)
        placeholders = ', '.join(['?'] * num_tags)

        self.cur.execute(f"""
        SELECT images.*
        FROM images
        JOIN tags_join
        ON images.id = tags_join.image_id
        WHERE tags_join.tag_id in ({placeholders})
        GROUP BY images.id
        HAVING COUNT(DISTINCT tags_join.tag_id) = ?
        """, tag_ids + [num_tags])
        return self.cur.fetchall()

    def _filter_around(self, timestamp: float, tag_ids: list[int],
                       n: int, search_after: bool) -> list[dict]:
        if search_after:
            comp = '>='
            order = 'ASC'
        else:
            comp = '<='
            order = 'DESC'

        if not tag_ids:
            self.cur.execute(f"""
            SELECT images.*
            FROM images
            WHERE images.timestamp {comp} ?
            ORDER BY images.timestamp {order}
            LIMIT ?
            """, [timestamp, n])
            return self.cur.fetchall()

        num_tags = len(tag_ids)
        placeholders = ', '.join(['?'] * num_tags)

        self.cur.execute(f"""
        SELECT images.*
        FROM images
        JOIN tags_join
        ON images.id = tags_join.image_id
        WHERE tags_join.tag_id IN ({placeholders})
        AND images.timestamp {comp} ?
        GROUP BY images.id
        HAVING COUNT(DISTINCT tags_join.tag_id) = ?
        ORDER BY images.timestamp {order}
        LIMIT ?
        """, tag_ids + [timestamp, num_tags, n])
        return self.cur.fetchall()

    def closest_to_date(self, timestamp: float) -> dict:
        self.cur.execute("""
        SELECT
            images.*,
            ABS(images.timestamp - ?) AS distance
        FROM images
        ORDER BY distance ASC
        LIMIT 1
        """, [timestamp])
        return self.cur.fetchone()
