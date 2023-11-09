from collections import deque
from collections.abc import Iterable
import itertools
from typing import TypeGuard

from .types import _Arrow, _Constructor, Constructor, Type, _Type, _Product


def filter_constructor(types: Iterable[_Type]) -> Iterable[_Constructor]:
    for t in types:
        if isinstance(t, _Constructor):
            yield t


def filter_arrow(types: Iterable[_Type]) -> Iterable[_Arrow]:
    for t in types:
        if isinstance(t, _Arrow):
            yield t


def filter_product(types: Iterable[_Type]) -> Iterable[_Product]:
    for t in types:
        if isinstance(t, _Product):
            yield t


class Subtypes:
    def __init__(self, environment: dict[str, set[str]]):
        self.environment = self._transitive_closure(
            self._reflexive_closure(environment)
        )

    def _check_subtype_rec(self, subtypes: Type, supertypes: Type) -> bool:
        if all(supertype.is_omega for supertype in supertypes):
            return True

        result: bool = True

        for supertype in supertypes:
            match supertype:
                case _Constructor(name2, arg2):
                    casted_constr = [
                        c.arg
                        for c in filter_constructor(subtypes)
                        if c.name == name2 or name2 in self.environment.get(c.name, {})
                    ]
                    result = (
                        result
                        and (len(casted_constr) != 0)
                        and self._check_subtype_rec(Type.intersect(casted_constr), arg2)
                    )

                case _Arrow(src2, tgt2):
                    casted_arr = Type.intersect(
                        a.target
                        for a in filter_arrow(subtypes)
                        if self._check_subtype_rec(src2, a.source)
                    )
                    result = (
                        result
                        and len(casted_arr) != 0
                        and self._check_subtype_rec(casted_arr, tgt2)
                    )
                case _Product(left2, right2):
                    casted_l = Type.intersect(p.left for p in filter_product(subtypes))
                    casted_r = Type.intersect(p.right for p in filter_product(subtypes))
                    result = (
                        result
                        and len(casted_l) != 0
                        and len(casted_r) != 0
                        and self._check_subtype_rec(casted_l, left2)
                        and self._check_subtype_rec(casted_r, right2)
                    )

                case _:
                    raise TypeError(f"Unsupported type in check_subtype: {supertype}")
        return result

    def check_subtype(self, subtype: Type, supertype: Type) -> bool:
        """Decides whether subtype <= supertype."""

        return self._check_subtype_rec(subtype, supertype)

    @staticmethod
    def _reflexive_closure(env: dict[str, set[str]]) -> dict[str, set[str]]:
        all_types: set[str] = set(env.keys())
        for v in env.values():
            all_types.update(v)
        result: dict[str, set[str]] = {
            subtype: {subtype}.union(env.get(subtype, set())) for subtype in all_types
        }
        return result

    @staticmethod
    def _transitive_closure(env: dict[str, set[str]]) -> dict[str, set[str]]:
        result: dict[str, set[str]] = {
            subtype: supertypes.copy() for (subtype, supertypes) in env.items()
        }
        has_changed = True

        while has_changed:
            has_changed = False
            for known_supertypes in result.values():
                for supertype in known_supertypes.copy():
                    to_add: set[str] = {
                        new_supertype
                        for new_supertype in result[supertype]
                        if new_supertype not in known_supertypes
                    }
                    if to_add:
                        has_changed = True
                    known_supertypes.update(to_add)

        return result

    def minimize(self, tys: set[Type]) -> set[Type]:
        result: set[Type] = set()
        for ty in tys:
            if all(map(lambda ot: not self.check_subtype(ot, ty), result)):
                result = {ty, *(ot for ot in result if not self.check_subtype(ty, ot))}
        return result
