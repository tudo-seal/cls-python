from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from functools import cache, reduce
import itertools
from typing import Any, reveal_type


@dataclass(frozen=True)
class _Type(ABC):
    is_omega: bool = field(init=True, kw_only=True, compare=False)
    size: int = field(init=True, kw_only=True, compare=False)
    organized: Type = field(init=True, kw_only=True, compare=False)

    def __str__(self) -> str:
        return self._str_prec(0)

    @abstractmethod
    def _organized(self) -> Type:
        pass

    @abstractmethod
    def _size(self) -> int:
        pass

    @abstractmethod
    def _is_omega(self) -> bool:
        pass

    @abstractmethod
    def _str_prec(self, prec: int) -> str:
        pass

    @staticmethod
    def _parens(s: str) -> str:
        return f"({s})"

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        del state["is_omega"]
        del state["size"]
        del state["organized"]
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.__dict__.update(state)
        self.__dict__["is_omega"] = self._is_omega()
        self.__dict__["size"] = self._size()
        self.__dict__["organized"] = self._organized()


# @dataclass(frozen=True)
# class Omega(Type):
#     is_omega: bool = field(init=False, compare=False)
#     size: bool = field(init=False, compare=False)
#     organized: set[Type] = field(init=False, compare=False)
#
#     def __post_init__(self) -> None:
#         super().__init__(
#             is_omega=self._is_omega(),
#             size=self._size(),
#             organized=self._organized(),
#         )
#
#     def _is_omega(self) -> bool:
#         return True
#
#     def _size(self) -> int:
#         return 1
#
#     def _organized(self) -> set[Type]:
#         return set()
#
#     def _str_prec(self, prec: int) -> str:
#         return "omega"


class Type(frozenset[_Type]):
    def __new__(cls, iterablke: Iterable[_Type] = frozenset(), recustion_break=False):
        return super().__new__(cls, iterablke)
        # return Type.__init__(iterablke, recustion_break)

    def __init__(self, iterable: Iterable[_Type] = frozenset(), recustion_break=False):
        super().__new__(frozenset, iterable)
        # self.len = len(self)
        self.is_omega = len(self) == 0
        if not recustion_break:
            self._organized = Type(
                itertools.chain(*(ty.organized for ty in iterable)), True
            )
        else:
            self._organized = self

    @staticmethod
    def intersect(types: Iterable[Type]) -> Type:
        return Type(itertools.chain(*types))
        # try:
        #     return Type(itertools.chain(*types))
        # except TypeError:
        #     return Type()

    @staticmethod
    def arrows(types: Sequence[Type]) -> Type:
        return reduce(lambda t, s: Arrow(s, t), reversed(types))

    @property
    def organized(self):
        return self._organized
        # return Type.intersect(ty.organized for ty in self)

    # @property
    # def is_omega(self):
    #     return len(self) == 0

    def __mul__(self, other):
        return Product(self, other)


def Constructor(name: str, arg: Type = Type()) -> Type:
    return Type((_Constructor(name, arg),))


def Arrow(source: Type, target: Type) -> Type:
    return Type((_Arrow(source, target),))


def Omega() -> Type:
    return Type()


@dataclass(frozen=True)
class _Constructor(_Type):
    name: str = field(init=True)
    arg: Type = field(default=Omega(), init=True)
    is_omega: bool = field(init=False, compare=False)
    size: int = field(init=False, compare=False)
    organized: Type = field(init=False, compare=False)

    def __post_init__(self) -> None:
        super().__init__(
            is_omega=self._is_omega(),
            size=self._size(),
            organized=self._organized(),
        )

    def _is_omega(self) -> bool:
        return False

    def _size(self) -> int:
        return 1 + sum((inner.size for inner in self.arg))

    def _organized(self) -> Type:
        if len(self.arg) <= 1:
            return Type((self,), True)
        else:
            return Type(
                (
                    _Constructor(self.name, Type({ap}))
                    for inters in self.arg
                    for ap in inters.organized
                ),
                True,
            )

    def _str_prec(self, prec: int) -> str:
        if self.arg == Omega():
            return str(self.name)
        else:
            return f"{str(self.name)}({str(self.arg)})"


def Product(t1: Type, t2: Type) -> Type:
    return Intersection(Constructor("Pi1", t1), Constructor("Pi2", t2))


@dataclass(frozen=True)
class _Product(_Type):
    left: Type = field(init=True)
    right: Type = field(init=True)
    is_omega: bool = field(init=False, compare=False)
    size: int = field(init=False, compare=False)
    organized: Type = field(init=False, compare=False)

    def __post_init__(self) -> None:
        super().__init__(
            is_omega=self._is_omega(),
            size=self._size(),
            organized=self._organized(),
        )

    def _is_omega(self) -> bool:
        return False

    def _size(self) -> int:
        return (
            1
            + sum((inters.size for inters in self.left))
            + sum((inters.size for inters in self.right))
        )

    def _organized(self) -> Type:
        if len(self.left) + len(self.right) <= 1:
            return Type((self,), True)
        else:
            left_organized = Type.union(*(lft.organized for lft in self.left))
            right_organized = Type.union(*(lft.organized for lft in self.left))
            return Type(
                itertools.chain(
                    (_Product(Type((lp,)), Omega()) for lp in left_organized),
                    (_Product(Omega(), Type((rp,))) for rp in right_organized),
                ),
                True,
            )

    def _str_prec(self, prec: int) -> str:
        # product_prec: int = 9
        #
        # def product_str_prec(other: _Type) -> str:
        #     match other:
        #         case Product(_, _):
        #             return other._str_prec(product_prec)
        #         case _:
        #             return other._str_prec(product_prec + 1)
        #
        # result: str = (
        #     f"{product_str_prec(self.left)} * {self.right._str_prec(product_prec + 1)}"
        # )
        # return Type._parens(result) if prec > product_prec else result
        return "string repr WIP"


@dataclass(frozen=True)
class _Arrow(_Type):
    source: Type = field(init=True)
    target: Type = field(init=True)
    is_omega: bool = field(init=False, compare=False)
    size: int = field(init=False, compare=False)
    organized: Type = field(init=False, compare=False)

    def __post_init__(self) -> None:
        super().__init__(
            is_omega=self._is_omega(),
            size=self._size(),
            organized=self._organized(),
        )

    def _is_omega(self) -> bool:
        return all(tgt.is_omega for tgt in self.target)

    def _size(self) -> int:
        return (
            1
            + sum((src.size for src in self.source))
            + sum((tgt.size for tgt in self.target))
        )

    def _organized(self) -> Type:
        if len(self.target) == 0:
            return Type()
        elif len(self.target) == 1:
            return Type((self,))
        else:
            return Type(
                (
                    _Arrow(self.source, Type({tp}))
                    for tgt in self.target
                    for tp in tgt.organized
                )
            )

    def _str_prec(self, prec: int) -> str:
        arrow_prec: int = 8
        result: str
        if len(self.target) == 1:
            match list(self.target)[0]:
                case _Arrow(_, _):
                    result = (
                        f"{ {src._str_prec(arrow_prec + 1) for src in self.source} } -> "
                        f"{ list(self.target)[0]._str_prec(arrow_prec) }"
                    )
                case _:
                    result = (
                        f"{ {src._str_prec(arrow_prec + 1) for src in self.source} } -> "
                        f"{ list(self.target)[0]._str_prec(arrow_prec + 1) }"
                    )
        else:
            result = (
                f"{ {src._str_prec(arrow_prec + 1) for src in self.source} } -> "
                f"{ {tgt._str_prec(arrow_prec + 1) for tgt in self.target} } -> "
            )

        return _Type._parens(result) if prec > arrow_prec else result


def Intersection(*types: Type) -> Type:
    return Type.intersect(types)


# @dataclass(frozen=True)
# class _Intersection(Type):
#     inner: frozenset[Type] = field(init=True)
#     is_omega: bool = field(init=False, compare=False)
#     size: int = field(init=False, compare=False)
#     organized: set[Type] = field(init=False, compare=False)
#
#     def __post_init__(self) -> None:
#         super().__init__(
#             is_omega=self._is_omega(),
#             size=self._size(),
#             organized=self._organized(),
#         )
#
#     def _is_omega(self) -> bool:
#         return self.inner == frozenset({})
#
#     def _size(self) -> int:
#         return 1 + self.left.size + self.right.size
#
#     def _organized(self) -> set[Type]:
#         return set.union(self.left.organized, self.right.organized)
#
#     def _str_prec(self, prec: int) -> str:
#         intersection_prec: int = 10
#
#         def intersection_str_prec(other: Type) -> str:
#             match other:
#                 case Intersection(_, _):
#                     return other._str_prec(intersection_prec)
#                 case _:
#                     return other._str_prec(intersection_prec + 1)
#
#         result: str = (
#             f"{intersection_str_prec(self.left)} & {intersection_str_prec(self.right)}"
#         )
#         return Type._parens(result) if prec > intersection_prec else result
#
# @dataclass(frozen=True)
# class Intersection(Type):
#     left: Type = field(init=True)
#     right: Type = field(init=True)
#     is_omega: bool = field(init=False, compare=False)
#     size: int = field(init=False, compare=False)
#     organized: set[Type] = field(init=False, compare=False)
#
#     def __post_init__(self) -> None:
#         super().__init__(
#             is_omega=self._is_omega(),
#             size=self._size(),
#             organized=self._organized(),
#         )
#
#     def _is_omega(self) -> bool:
#         return self.left.is_omega and self.right.is_omega
#
#     def _size(self) -> int:
#         return 1 + self.left.size + self.right.size
#
#     def _organized(self) -> set[Type]:
#         return set.union(self.left.organized, self.right.organized)
#
#     def _str_prec(self, prec: int) -> str:
#         intersection_prec: int = 10
#
#         def intersection_str_prec(other: Type) -> str:
#             match other:
#                 case Intersection(_, _):
#                     return other._str_prec(intersection_prec)
#                 case _:
#                     return other._str_prec(intersection_prec + 1)
#
#         result: str = (
#             f"{intersection_str_prec(self.left)} & {intersection_str_prec(self.right)}"
#         )
#         return Type._parens(result) if prec > intersection_prec else result


# Type: TypeAlias = frozenset[_Type]
