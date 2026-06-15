from collections.abc import Set
from typing import TYPE_CHECKING, Literal, Never, Protocol, override

__all__ = ["EMPTY_MAP", "EmptyMap", "SupportsItems"]


if TYPE_CHECKING:
    from _typeshed import SupportsItems
else:

    class SupportsItems[A, B](Protocol): ...


class EmptyMap(SupportsItems[Never, Never]):
    @override
    def items(self) -> Set[Never]:
        return set()

    def __bool__(self) -> Literal[False]:
        return False


EMPTY_MAP = EmptyMap()
