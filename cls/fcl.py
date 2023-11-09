# Propositional Finite Combinatory Logic

from collections import defaultdict, deque
from collections.abc import Hashable, Iterable, Mapping, MutableMapping, Sequence
from typing import Callable, Generic, TypeAlias, TypeVar

from .combinatorics import maximal_elements, minimal_covers, partition
from .subtypes import Subtypes
from .types import _Arrow, Intersection, Type, _Type

T = TypeVar("T", bound=Hashable, covariant=True)
C = TypeVar("C")

# ([sigma_1, ..., sigma_n], tau) means sigma_1 -> ... -> sigma_n -> tau
MultiArrow: TypeAlias = tuple[list[Type], Type]


TreeGrammar: TypeAlias = MutableMapping[Type, deque[tuple[C, list[Type]]]]


def show_grammar(grammar: TreeGrammar[C]) -> Iterable[str]:
    for clause, possibilities in grammar.items():
        lhs = str(clause)
        yield (
            lhs
            + " => "
            + "; ".join(
                (str(combinator) + "(" + ", ".join(map(str, args)) + ")")
                for combinator, args in possibilities
            )
        )


def mstr(m: MultiArrow) -> tuple[str, str]:
    return (str(list(map(str, m[0]))), str(m[1]))


class FiniteCombinatoryLogic(Generic[C]):
    def __init__(self, repository: Mapping[C, Type], subtypes: Subtypes):
        self.repository: Mapping[C, list[list[MultiArrow]]] = {
            c: list(FiniteCombinatoryLogic._function_types(ty))
            for c, ty in repository.items()
        }
        self.subtypes = subtypes

    @staticmethod
    def _function_types(ty: Type) -> Iterable[list[MultiArrow]]:
        """Presents a type as a list of 0-ary, 1-ary, ..., n-ary function types."""

        def unary_function_types(ty: Type) -> Iterable[tuple[Type, Type]]:
            for t in ty:
                match t:
                    case _Arrow(src, tgt) if not tgt.is_omega:
                        yield (src, tgt)

        current: list[MultiArrow] = [([], ty)]
        while len(current) != 0:
            yield current
            current = [
                (args + [new_arg], new_tgt)
                for (args, tgt) in current
                for (new_arg, new_tgt) in unary_function_types(tgt)
            ]

    def _subqueries(
        self, nary_types: list[MultiArrow], paths: Type
    ) -> Sequence[list[Type]]:
        # does the target of a multi-arrow contain a given type?
        target_contains: Callable[
            [MultiArrow, _Type], bool
        ] = lambda m, t: self.subtypes.check_subtype(m[1], Type((t,)))
        # cover target using targets of multi-arrows in nary_types
        covers = minimal_covers(nary_types, paths, target_contains)

        if len(covers) == 0:
            return []

        intersected_args = [
            list(map(Intersection, *[multiarrow[0] for multiarrow in arity]))
            for arity in covers
        ]

        # consider only maximal argument vectors
        compare_args = lambda args1, args2: all(
            map(self.subtypes.check_subtype, args1, args2)
        )

        return maximal_elements(intersected_args, compare_args)

    def inhabit(self, *targets: Type) -> TreeGrammar[C]:
        type_targets = deque(targets)

        # dictionary of type |-> sequence of combinatory expressions
        memo: TreeGrammar[C] = defaultdict(deque)
        seen: set[Type] = set()

        while type_targets:
            current_target = type_targets.pop()

            # target type was not seen before
            if current_target not in seen:
                seen.add(current_target)
                # If the target is omega, then the result is junk
                if current_target.is_omega:
                    continue

                paths: Type = current_target.organized

                # try each combinator and arity
                for combinator, combinator_type in self.repository.items():
                    for nary_types in combinator_type:
                        arguments: list[list[Type]] = list(
                            self._subqueries(nary_types, paths)
                        )
                        if len(arguments) == 0:
                            continue

                        for subquery in arguments:
                            memo[current_target].append((combinator, subquery))
                            type_targets.extendleft(subquery)

        # prune not inhabited types
        FiniteCombinatoryLogic._prune(memo)

        return memo

    @staticmethod
    def _prune(memo: TreeGrammar[C]) -> None:
        """Keep only productive grammar rules."""

        def is_ground(args: list[Type], ground_types: set[Type]) -> bool:
            return all(arg in ground_types for arg in args)

        ground_types: set[Type] = set()
        candidates, new_ground_types = partition(
            lambda ty: any(
                True for (_, args) in memo[ty] if is_ground(args, ground_types)
            ),
            memo.keys(),
        )
        # initialize inhabited (ground) types
        while new_ground_types:
            ground_types.update(new_ground_types)
            candidates, new_ground_types = partition(
                lambda ty: any(is_ground(args, ground_types) for _, args in memo[ty]),
                candidates,
            )

        non_ground_types = set(memo.keys()).difference(ground_types)
        for target in non_ground_types:
            del memo[target]

        for target, possibilities in memo.items():
            memo[target] = deque(
                possibility
                for possibility in possibilities
                if is_ground(possibility[1], ground_types)
            )
