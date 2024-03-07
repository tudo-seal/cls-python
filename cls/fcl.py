# Propositional Finite Combinatory Logic

from collections import defaultdict, deque
from collections.abc import Hashable, Iterable, Mapping, MutableMapping, Sequence
from functools import reduce
from itertools import chain, combinations
from typing import Callable, Generic, TypeAlias, TypeVar, cast

from .combinatorics import maximal_elements, minimal_covers, partition
from .subtypes import Subtypes
from .types import Arrow, Constructor, Intersection, Omega, Type

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
        self.subtypes = subtypes
        self.repository: Mapping[C, list[list[MultiArrow]]] = {
            c: list(FiniteCombinatoryLogic._function_types(ty))
            for c, ty in self.optimize(repository).items()
        }

    @staticmethod
    def flatten_intersection(left: Type, right: Type) -> set[Type]:
        to_flat = [left, right]
        flat = set()
        while to_flat:
            current = to_flat.pop()
            match current:
                case Intersection(l2, r2):
                    to_flat.extend((l2, r2))
                case _:
                    flat.add(current)

        return flat

    @staticmethod
    def optimize_tags(ty: Type) -> tuple[Type, dict[str, list[str]]]:
        """
        Replaces intersections of zero-arity constructors, by one single constructor.

        A dictionary containing the new name, mapping to each replaced components is also returned,
        to facilitate manual subtyping with the taxonomy.
        """

        match ty:
            case Omega():
                return Omega(), {}
            case Constructor(name, Omega()):
                return Constructor(f"__{name}__"), {f"__{name}__": [name]}
            case Constructor(name, arg):
                new_arg, repl_arg = FiniteCombinatoryLogic.optimize_tags(arg)
                return Constructor(name, new_arg), repl_arg
            case Arrow(src, tgt):
                new_src, repl_src = FiniteCombinatoryLogic.optimize_tags(src)
                new_tgt, repl_tgt = FiniteCombinatoryLogic.optimize_tags(tgt)
                return Arrow(new_src, new_tgt), repl_src | repl_tgt

            case Intersection(l, r):
                flattened = FiniteCombinatoryLogic.flatten_intersection(l, r)
                complex, simple = partition(
                    lambda t: isinstance(t, Constructor) and t.arg.is_omega, flattened
                )
                simple_combined = sorted(s.name for s in cast(Iterable[Constructor], simple))
                simple_combined_name = f"__{'_'.join(simple_combined)}__"
                return reduce(
                    lambda accum_type_and_taxonomy, new_type_and_taxonomy: (
                        Intersection(accum_type_and_taxonomy[0], new_type_and_taxonomy[0]),
                        accum_type_and_taxonomy[1] | new_type_and_taxonomy[1],
                    ),
                    chain(
                        [
                            (
                                Constructor(simple_combined_name),
                                {simple_combined_name: simple_combined},
                            )
                        ]
                        if len(simple) > 0
                        else [],
                        map(FiniteCombinatoryLogic.optimize_tags, complex),
                    ),
                )

            case _:
                raise RuntimeError("Not Supported")

    def optimize(self, repo: Mapping[C, Type]) -> dict[C, Type]:
        """Find all Intersections of zero arity constructorsm replace them and build a taxonomy,
        replicating the subtyping"""

        optimized_repo = {}
        names: set[str] = set()
        for c, ty in repo.items():
            optimized_type, d = FiniteCombinatoryLogic.optimize_tags(ty)
            for k, v in d.items():
                supertypes = set(
                    f"__{'_'.join(name)}__"
                    for name in chain.from_iterable(combinations(v, i) for i in range(len(v) + 1))
                    if name != ()
                )
                names = names.union(v)
                self.subtypes.environment[k] = supertypes
            optimized_repo[c] = optimized_type

        for n in names:
            self.subtypes.environment[f"__{n}__"] = {n}

        self.subtypes.environment = self.subtypes._transitive_closure(
            self.subtypes._reflexive_closure(self.subtypes.environment)
        )

        return optimized_repo

    @staticmethod
    def _function_types(ty: Type) -> Iterable[list[MultiArrow]]:
        """Presents a type as a list of 0-ary, 1-ary, ..., n-ary function types."""

        def unary_function_types(ty: Type) -> Iterable[tuple[Type, Type]]:
            tys: deque[Type] = deque((ty,))
            while tys:
                match tys.pop():
                    case Arrow(src, tgt) if not tgt.is_omega:
                        yield (src, tgt)
                    case Intersection(sigma, tau):
                        tys.extend((sigma, tau))

        current: list[MultiArrow] = [([], ty)]
        while len(current) != 0:
            yield current
            current = [
                (args + [new_arg], new_tgt)
                for (args, tgt) in current
                for (new_arg, new_tgt) in unary_function_types(tgt)
            ]

    def _subqueries(self, nary_types: list[MultiArrow], paths: list[Type]) -> Sequence[list[Type]]:
        # does the target of a multi-arrow contain a given type?
        target_contains: Callable[[MultiArrow, Type], bool] = (
            lambda m, t: self.subtypes.check_subtype(m[1], t)
        )
        # cover target using targets of multi-arrows in nary_types
        covers = minimal_covers(nary_types, paths, target_contains)
        if len(covers) == 0:
            return []
        # intersect corresponding arguments of multi-arrows in each cover
        intersect_args: Callable[[Iterable[Type], Iterable[Type]], list[Type]] = (
            lambda args1, args2: [Intersection(a, b) for a, b in zip(args1, args2)]
        )

        intersected_args = (list(reduce(intersect_args, (m[0] for m in ms))) for ms in covers)
        # consider only maximal argument vectors
        compare_args = lambda args1, args2: all(map(self.subtypes.check_subtype, args1, args2))
        return maximal_elements(intersected_args, compare_args)

    def inhabit(self, *targets: Type) -> TreeGrammar[C]:
        # type_targets = deque((self.optimize_tags(t)[0] for t in targets))
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

                paths: list[Type] = list(current_target.organized)

                # try each combinator and arity
                for combinator, combinator_type in self.repository.items():
                    for nary_types in combinator_type:
                        arguments: list[list[Type]] = list(self._subqueries(nary_types, paths))
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
            lambda ty: any(True for (_, args) in memo[ty] if is_ground(args, ground_types)),
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
