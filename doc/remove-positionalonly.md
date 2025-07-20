# remove-positionalonly and remove-keywordsonly

The `",*,"` keywordonly syntax in function declarations feels natural to many python developers
but it did not exist before python3. It is similar to the `",/,"` positionalonly syntax but
that one came even later in python 3.8. The reason has been that native-code implementations 
do not like their arguments to be rearranged - and it was felt necessary to inform the type 
checker about it.

When stripping typehints for python2, both syntax elements get removed.

It gets a bit more complicated when a python3 typehints `*.pyi` file is generated. By
default they are compatible with python 3.6, so the keywordonly hint can stay, but
the positionalonly hint must be dropped. A similar case arises when downgrading the
main source code to just below python 3.8 - they keywordonly hint can stay but the
positionalonly hint must be dropped.



        # original
        class B:
           b: int
           c: str
           def __add__(self, y: list[str], /, a: int = 0, *, b: int = 0) -> list[str]:
               return [self.c] + y

        # transformed
        class B:
            def __add__(self, y, a=0, b=0):
                return [self.c] + y

        # generated pyi
        from typing import List
        class B:
            b: int
            c: str
            def __add__(self, y: List[str], a: int=0, *, b: int=0) -> List[str]:
                pass

