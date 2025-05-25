from abc import ABC, abstractmethod

from typing import Iterable


class StringDatabaseInterface(ABC):
    @abstractmethod
    def indexes(self) -> Iterable[int]:
        """Return a list of all indexes in the storage.

        Returns:
            list[int]: list of indexes
        """
        pass

    @abstractmethod
    def query(self, index: int) -> str:
        """Look up the given key in the storage.

        Returns:
            str: the content of the key; empty string if not found
        """
        pass

    @abstractmethod
    def add(self, content: str) -> int:
        """Add the given content to the storage.

        Returns:
            int: the index of the added content.
        """
        pass

    @abstractmethod
    def update(self, index: int, content: str) -> None:
        """Update the content of the given index."""
        pass

    @abstractmethod
    def delete(self, index: int) -> None:
        """Delete the content of the given index."""
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass
