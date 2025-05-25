from .storage import ItemStorage
from ..string_database.interface import StringDatabaseInterface
from contextlib import contextmanager
import json

from typing import Set


class LazyItemStorage(ItemStorage):
    def __init__(self, storage: StringDatabaseInterface, batch_size=1):
        self.__dirty_keys: Set[int] = set()
        self.__flush_disabled = 0
        self.__dirty_count = 0
        self.__batch_size = batch_size
        super().__init__(storage)

    def _update(self, key: int) -> None:
        if key not in self._cache:
            raise ValueError(f"Item(key={key}) Not Found, Possibly Deleted Already")
        self.__dirty_keys.add(key)
        self.__dirty_count += 1

        if self.__flush_disabled == 0 and self.__dirty_count >= self.__batch_size:
            self.flush()
            self.__dirty_count = 0

    def flush(self) -> None:
        for key in self.__dirty_keys:
            if key in self._cache:
                self._storage.update(key, json.dumps(self._cache[key]))
        self.__dirty_keys.clear()

    @contextmanager
    def no_flush(self):
        self.__flush_disabled += 1
        try:
            yield
        finally:
            self.__flush_disabled -= 1

    def __del__(self):
        self.flush()
