from .interface import StringDatabaseInterface
from typing import Iterable


class PlainStringDatabase(StringDatabaseInterface):
    def __init__(self):
        self.data = {}
        self.length = 0
        self.current_id = 0

    def indexes(self) -> Iterable[int]:
        return list(self.data.keys())

    def query(self, index: int) -> str:
        return self.data.get(index, "")

    def add(self, content: str) -> int:
        self.data[self.current_id] = content
        self.length += 1
        self.current_id += 1
        return self.current_id - 1

    def update(self, index: int, content: str) -> None:
        self.data[index] = content

    def delete(self, index: int) -> None:
        del self.data[index]
        self.length -= 1

    def __len__(self) -> int:
        return self.length
