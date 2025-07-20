# replace-annotated-typing

The `Annotated` typehint was introduced in python 3.9 and it is generally the
reason that `pydantic` requires that python version as a minimum. The Annotated
typehints takes a list of types where the standard type checker can watch for 
the standard builtin types while libraries can add conversion hints.

The most common form would be have a `Field` expression for pydantic. When
supporting older python versions that has to be removed. Actually, the
Field hint is relevant just for generated code that gets executed but it 
is not necessary in the `*.pyi` typehint externals.

        # original
        from typing import Annotated
        from pydantic import Field
        a: int 
        def adds(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> list[str]:
            if x := int(b):
                return [self.c] + y
            return 0

        # transformed
        from pydantic import Field
        
        def adds(self, y, a=0, b=0):
            x = int(b)
            if x:
                return [self.c] + y
            return 0
            
        # pyi typehints
        from typing import List, Optional
        a: int
        
        def adds(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> List[str]:
            pass
        
Similar typehints replacements are done for positional arguments, builtin and union-types.

See [replace-builtin-typing.md], [replace-union-typing.md], [remove-positionalonly.md],
[remove-keywordsonly.md], [replace-self-typing.md] and [remove-typeddict-pyi.md]

