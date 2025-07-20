# replace-builtin-typing and replace-union-typing

The `typing` module is available since python 3.5 including declaration for `List[]`
and `Union[]` types, and the `Optional[]` declaration for nullable types. However 
this required to use 'import' statements on that module to declare basic structures 
like lists and tuples and nullable types which occur in about every source code.

In python 3.9 and python 3.10 addtional syntactic sugar was added for that. To
delcare a list-type it possible to use `list[]` - the same for other basic 
container types like `dict[]`. With python 3.10 there is now a generalized
union-type with using `int | None` to declare a nullable type.

When supporting older python versions it is possible to replace the builtin-typing
with the imports from the `typing` module. For python2 this refers to the type
declarations in the parallel `*.pyi` header file which is usually generated
being compatible to python 3.6. When the target --python-version is 3.6 or
higher then the same replacements can be done in the main source code itself.

        # original
        class B:
           b: int
           c: str
           def __add__(self, y: list[str], /, *, b: int | None = 0) -> list[str]:
               x = int(b)
               return [self.c] + y

        # transformed
        class B:
            def __add__(self, y, b=0):
                x = int(b)
                return [self.c] + y
        
        # generated pyi
        from typing import List, Optional        
        class B:
            b: int
            c: str
            def __add__(self, y: List[str], *, b: Optional[int]=0) -> List[str]:
                pass

