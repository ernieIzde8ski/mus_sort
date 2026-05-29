from collections import deque
from collections.abc import Iterable, Iterator
from typing import override


class MutChain[T](Iterator[T]):
    """Lazily-evaluating, mutation-safe chains of iterables

    >>> chain = MutChain(range(2, 4), range(6, 8))
    >>> next(chain)
    2
    >>> next(chain)
    3
    >>> chain.aftlay(5)
    >>> [*chain]
    [6, 7, 5]
    >>> [*chain]
    []
    """

    def __init__(self, *links: Iterable[T]) -> None:
        self.__links = deque(links)

    def forelay(self, chip: T) -> None:
        self.__links.appendleft((chip,))

    def aftlay(self, chip: T) -> None:
        self.__links.append((chip,))

    def forespread(self, link: Iterable[T]) -> None:
        self.__links.appendleft(link)

    def aftspread(self, link: Iterable[T]) -> None:
        self.__links.append(link)

    @override
    def __next__(self) -> T:
        while self.__links:
            left = self.__links.popleft()
            if not isinstance(left, Iterator):
                left = iter(left)

            try:
                res = next(left)
            except StopIteration:
                continue
            else:
                self.__links.appendleft(left)
                return res

        raise StopIteration
