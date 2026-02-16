import os

class FilePath:
    def __init__(self, path: str):
        self.dirs = []
        self.name = os.path.basename(path)
        self.path = path

        for dir in os.path.split(path)[:-1]:
            if len(dir) > 0:
                self.dirs.append(dir)

    def __repr__(self):
        return f'FilePath({self.dirs} / {self.name})'

def list_files(path) -> set[FilePath]:
    l = set()

    for f in os.listdir(path):
        full = os.path.join(path, f)

        if os.path.isdir(full):
            l = l.union(list_files(full))
        else:
            l.add(FilePath(full))

    return l
