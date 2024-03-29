from collections import deque
from collections.abc import Iterable, Mapping, MutableMapping
from typing import Any, Optional, TypeVar

from .subtypes import Subtypes
from .types import Type, Omega, Constructor, Product, Arrow, Intersection
from .enumeration import (
    interpret_term,
    enumerate_terms,
    enumerate_terms_iter,
    enumerate_terms_of_size,
)
from .fcl import FiniteCombinatoryLogic

__all__ = [
    "Subtypes",
    "Type",
    "Omega",
    "Constructor",
    "Product",
    "Arrow",
    "Intersection",
    "enumerate_terms",
    "enumerate_terms_iter",
    "enumerate_terms_of_size",
    "interpret_term",
    "FiniteCombinatoryLogic",
    "inhabit_and_interpret",
]

C = TypeVar("C")


def inhabit_and_interpret(
    repository: Mapping[C, Type],
    query: list[Type] | Type,
    max_count: Optional[int] = None,
    subtypes: Optional[Subtypes] = None,
) -> Iterable[Any]:
    fcl = FiniteCombinatoryLogic(repository, Subtypes(dict()) if subtypes is None else subtypes)

    if not isinstance(query, list):
        query = [query]

    grammar: MutableMapping[
        Type,
        deque[tuple[C, list[Type]]],
    ] = fcl.inhabit(*query)

    for q in query:
        enumerated_terms = enumerate_terms(start=q, grammar=grammar, max_count=max_count)
        for term in enumerated_terms:
            yield interpret_term(term)
