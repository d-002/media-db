import os

class FilePath:
    def __init__(self, path: str):
        self.dirs = []
        self.name = os.path.basename(path)
        self.path = path

        for dir in path.split(os.sep)[:-1]:
            if len(dir) > 0:
                self.dirs.append(dir)

    def __repr__(self):
        return f'FilePath({self.dirs} / {self.name})'

def list_files(path) -> list[FilePath]:
    l = [] # using a list to avoid cache issues on database sync for clients

    for f in os.listdir(path):
        full = os.path.join(path, f)

        if os.path.isdir(full):
            l += list_files(full)
        else:
            l.append(FilePath(full))

    return l
