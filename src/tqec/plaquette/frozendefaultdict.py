from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Callable, Generic, Iterable, Iterator, TypeVar

from typing_extensions import override

from tqec.exceptions import TQECException

K = TypeVar("K")
V = TypeVar("V")


class FrozenException(TQECException):
    pass


class FrozenDefaultDict(Generic[K, V], Mapping[K, V]):
    """A defaultdict implementation that cannot be mutated.

    This class re-defines all the mutating methods of `defaultdict` (i.e., all
    the mutating methods of `dict` and `__missing__`) in order to make any
    instance immutable.

    Note on re-defining `__missing__`:

    The standard `defaultdict` implementation is entirely based on the
    `__missing__` method (described here
    https://docs.python.org/3/library/collections.html#collections.defaultdict.__missing__)
    that is called when a user-provided key was not found in the defined keys.
    This `__missing__` method try to use `self.default_factory` to create a new
    value and inserts that new value in the dictionary. That last part is
    problematic for :class:`Plaquettes` and in particular to compare collections
    of :class:`Plaquettes` through `__hash__` and `__eq__`.
    """

    def __init__(
        self,
        arg: Mapping[K, V] | Iterable[tuple[K, V]] | None = None,
        *,
        default_factory: Callable[[], V] | None = None,
    ) -> None:
        super().__init__()
        self._dict: dict[K, V] = dict(arg) if arg is not None else dict()
        self._default_factory = default_factory

    def __missing__(self, key: K) -> V:
        if self._default_factory is None:
            raise KeyError(key)
        return self._default_factory()

    @override
    def __getitem__(self, key: K) -> V:
        try:
            return self._dict[key]
        except KeyError:
            return self.__missing__(key)

    @override
    def __iter__(self) -> Iterator[K]:
        return iter(self._dict)

    @override
    def __len__(self) -> int:
        return len(self._dict)

    @override
    def __contains__(self, key: object) -> bool:
        return self._dict.__contains__(key)

    def __or__(self, other: Mapping[K, V]) -> FrozenDefaultDict[K, V]:
        mapping = deepcopy(self._dict)
        mapping.update(other)
        return FrozenDefaultDict(mapping, default_factory=self._default_factory)

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.items())))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, FrozenDefaultDict)
            and (self._default_factory == other._default_factory)
            and (
                self._default_factory is not None
                and other._default_factory is not None
                and (self._default_factory() == other._default_factory())
            )
            and self._dict == other._dict
        )

    def has_default_factory(self) -> bool:
        return self._default_factory is not None
