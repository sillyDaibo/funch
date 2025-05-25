from .storage import ItemStorage

from typing import Iterable, Optional, Dict, List


class ItemStorageSplit(ItemStorage):
    def __init__(
        self,
        storage: ItemStorage,
        split_id: Optional[int],
        split_key_name: str = "_split_id",
    ):
        self.__storage = storage
        self.__split_id = split_id
        self.__split_key_name = split_key_name

    def id(self) -> Optional[int]:
        return self.__split_id

    def new(self) -> ItemStorage._Item:
        item = self.__storage.new()
        item[self.__split_key_name] = self.id()
        return item

    def items(self) -> Iterable[ItemStorage._Item]:
        for item in self.__storage.items():
            if item[self.__split_key_name] == self.id():
                yield item

    def _data(self, key: int) -> Dict:
        return self.__storage._data(key)

    def _update(self, key: int) -> None:
        return self.__storage._update(key)

    def _delete(self, key: int) -> None:
        return self.__storage._delete(key)

    def __len__(self) -> int:
        return len(list(self.items()))


def split_item_storage(
    storage: ItemStorage, num_splits: int, split_key_name: str
) -> List[ItemStorageSplit]:
    result = [ItemStorageSplit(storage, i, split_key_name) for i in range(1, num_splits)]
    result.append(ItemStorageSplit(storage, None, split_key_name))
    return result
