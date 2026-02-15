import sqlite3

class DataBase:
    db_file = 'db.db'

    def __init__(self):
        self.con = sqlite3.connect(DataBase.db_file)
        self.cur = self.con.cursor()

    def close(self) -> None:
        self.con.close()
