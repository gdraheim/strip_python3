# replace-self-typing

The python language contains the object-oriented mechanism to make a class
by inhereting the features of one or more other classes. It makes the new
class a sub-type of the other - with the `instanceof` builtin function allowing
to check an object being made from the given class or one of its subclasses.

With the introduction of typehints in python 3.5 it was possible to declare
the return type of a function but it did need to be the same in sub-classes
even when it was assured that the function will always `return self`.

So if you would redefine a function in a sub-class with the name of the
sub-class as the return type, the type checker would indicate a type
mismatch with the function in the parent class. So the following would
be called out:

        # problem
        class A:
           def foo(self, x: int) -> A:
               return self
        class B:
           def foo(self, x: int) -> B: # error
               return self

The `typing` module did provide a solution from its beginning - by creating
a generic `TypeVar` binding it to the base type. Let's call it a workaround.

        # workaround
        from typing import TypeVar
        SelfA = TypeVar("SelfA", bound="A")
        class A:
           def foo(self, x: int) -> SelfA:
               return self
        class B:
           def foo(self, x: int) -> SelfA:
               return self

Then in python 3.11 we finally got a `Self` class.

        class A:
           def foo(self, x: int) -> Self:
               return self
        class B:
           def foo(self, x: int) -> Self:
               return self

The transformer will find references to "Self" (and not only in return types)
replacing it wit the workaround described in PEP 673.

        # original
        class B:
           b: int
           c: str
           def __add__(self, y: list[str], /, a: Self, *, b: int | None = 0) -> Self:
               x = int(b)
               return a

        # transformed
        class B:       
            def __add__(self, y, a, b=0):
                x = int(b)
                return a

        # generated pyi
        from typing import TypeVar
        from typing import List, Optional
        a: int
        SelfB = TypeVar('SelfB', bound='B')
        class B:
            b: int
            c: str
            def __add__(self, y: List[str], a: SelfB, *, b: Optional[int]=0) -> SelfB:
                pass

The usage of "Self" was catching on with python 3.12 when it was required to
add an "@override" when an inherited function would be redefined.

