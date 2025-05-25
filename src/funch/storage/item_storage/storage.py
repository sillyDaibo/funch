from ..string_database.interface import StringDatabaseInterface
import json

from typing import Any, Iterable, Dict


class ItemStorage:
    class _Item:
        def __init__(self, storage_ref: "ItemStorage", key: int):
            self.__dict__["storage_ref"] = storage_ref
            self.__dict__["key"] = key

        def __getattr__(self, name: str) -> Any:
            if name in self.__dict__:
                return self.__dict__[name]
            return self.__dict__["storage_ref"]._data(self.key).get(name)

        def __getitem__(self, name: str) -> Any:
            return self.__getattr__(name)

        def __setitem__(self, name: str, value: Any) -> None:
            return self.__setattr__(name, value)

        def __setattr__(self, name: str, value: Any) -> None:
            if name in self.__dict__:
                return
            ref = self.__dict__["storage_ref"]
            data = ref._data(self.key)
            data[name] = value
            ref._update(self.key)

        def __delattr__(self, name: str) -> None:
            if name in self.__dict__:
                return
            ref = self.__dict__["storage_ref"]
            data = ref._data(self.key)
            del data[name]
            ref._update(self.key, data)

        def keys(self) -> Iterable[str]:
            ref = self.__dict__["storage_ref"]
            data = ref._data(self.key)
            return data.keys()

        def delete(self) -> None:
            self.__dict__["storage_ref"]._delete(self.key)

    def __init__(self, storage: StringDatabaseInterface):
        self._storage = storage
        self._cache: Dict[int, Dict] = {}

    def new(self) -> _Item:
        data: Dict[str, Any] = {}
        key = self._storage.add(json.dumps(data))
        self._cache[key] = data
        return self._Item(self, key)

    def items(self) -> Iterable[_Item]:
        for key in self._storage.indexes():
            if key not in self._cache:
                data = json.loads(self._storage.query(key))
                self._cache[key] = data
            yield self._Item(self, key)

    def _data(self, key: int) -> Dict:
        if key not in self._cache:
            raise ValueError(f"Item(key={key}) Not Found, Possibly Deleted Already")
        return self._cache[key]

    def _update(self, key: int) -> None:
        self._storage.update(key, json.dumps(self._data(key)))

    def _delete(self, key: int) -> None:
        self._cache.pop(key)
        self._storage.delete(key)

    def __len__(self) -> int:
        return len(self._storage)
