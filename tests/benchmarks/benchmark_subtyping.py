from functools import reduce
from cls.types import Intersection, Arrow, Constructor, Type
from cls.subtypes import Subtypes


def main():
    ib = Type.intersect([Constructor("a", Constructor(str(i))) for i in range(10)])
    ic = Type.intersect([Constructor("a", Constructor(str(i))) for i in range(10, 20)])
    arrb = Type.arrows([ib, ib, ib, ib, ib, ib, ib, ib])
    arrc = Type.arrows([ic, ic, ic, ic, ic, ic, ic, ic])

    taxonomy = {str(k): {str(k + 10)} for k in range(10)}
    subt = Subtypes(taxonomy)
    subt.check_subtype(arrb, arrc)


if __name__ == "__main__":
    main()
