import logging
import unittest
from cls import Constructor
from cls.subtypes import Subtypes
from cls.types import Arrow, Intersection, Omega


class TestSubtype(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        format="%(module)s %(levelname)s: %(message)s",
        # level=logging.INFO,
    )

    def test_CAx(self) -> None:
        subtypes = Subtypes({"c": {"d"}, "A": {"B"}})
        self.assertTrue(
            subtypes.check_subtype(
                Constructor("c", Constructor("A")), Constructor("d", Constructor("B"))
            )
        )

    def test_not_CAx(self) -> None:
        subtypes = Subtypes({})
        self.assertFalse(
            subtypes.check_subtype(
                Constructor("c", Constructor("A")), Constructor("d", Constructor("B"))
            )
        )

    def test_CDist(self) -> None:
        subtypes = Subtypes({})
        self.assertTrue(
            subtypes.check_subtype(
                Intersection(
                    Constructor("c", Constructor("A")),
                    Constructor("c", Constructor("B")),
                ),
                Constructor("c", Intersection(Constructor("A"), Constructor("B"))),
            )
        )

    def test_not_CDist(self) -> None:
        subtypes = Subtypes({})
        self.assertFalse(
            subtypes.check_subtype(
                Intersection(
                    Constructor("c", Constructor("A")),
                    Constructor("c", Constructor("B")),
                ),
                Constructor("c", Intersection(Constructor("A"), Constructor("C"))),
            )
        )

    def test_omega(self) -> None:
        subtypes = Subtypes({})
        self.assertTrue(subtypes.check_subtype(Constructor("A"), Omega()))

    def test_not_omega(self) -> None:
        subtypes = Subtypes({})
        self.assertFalse(subtypes.check_subtype(Omega(), Constructor("A")))

    def test_to_omega(self) -> None:
        subtypes = Subtypes({})
        self.assertTrue(subtypes.check_subtype(Omega(), Arrow(Omega(), Omega())))

    def test_a_to_omega(self) -> None:
        subtypes = Subtypes({})
        self.assertTrue(
            subtypes.check_subtype(Constructor("A"), Arrow(Constructor("B"), Omega()))
        )

    def test_sub(self) -> None:
        subtypes = Subtypes({"B1": {"A1"}, "A2": {"B2"}})
        a1 = Constructor("A1")
        a2 = Constructor("A2")
        b1 = Constructor("B1")
        b2 = Constructor("B2")
        self.assertTrue(subtypes.check_subtype(Arrow(a1, a2), Arrow(b1, b2)))

    def test_not_sub(self) -> None:
        subtypes = Subtypes({})
        a1 = Constructor("A1")
        a2 = Constructor("A2")
        b1 = Constructor("B1")
        b2 = Constructor("B2")
        self.assertFalse(subtypes.check_subtype(Arrow(a1, a2), Arrow(b1, b2)))

    def test_dist(self) -> None:
        subtypes = Subtypes({})
        a = Constructor("A")
        b1 = Constructor("B1")
        b2 = Constructor("B2")
        self.assertTrue(
            subtypes.check_subtype(
                Intersection(Arrow(a, b1), Arrow(a, b2)), Arrow(a, Intersection(b1, b2))
            )
        )

    def test_non_dist(self) -> None:
        subtypes = Subtypes({})
        a = Constructor("A")
        b1 = Constructor("B1")
        b2 = Constructor("B2")
        b3 = Constructor("B3")
        self.assertFalse(
            subtypes.check_subtype(
                Intersection(Arrow(a, b1), Arrow(a, b2)), Arrow(a, Intersection(b1, b3))
            )
        )

    def test_constructor_refl(self) -> None:
        a = Constructor("A")
        subtypes = Subtypes({})
        self.assertTrue(subtypes.check_subtype(a, a))

    def test_idempotence_right(self) -> None:
        a = Constructor("A")

        subtypes = Subtypes({})
        self.assertTrue(subtypes.check_subtype(a, Intersection(a, a)))


if __name__ == "__main__":
    unittest.main()
