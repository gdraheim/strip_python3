## replace-namedtuple-class

The `typing.NamedTuple` class is often easier to create than a `@dataclass`. The
difference is that a `namedtuple` is not mutable. You can change fields only by
using the `._replace()` method on the object creating a new object.

A function variant of `namedtuple` did exist in `collections` since python 2.6.
The transformer will look for the fields in the `NamedTuple` class definition
and generate a function variant out of it.

Naturally, the `namedtuple` function can NOT be extended with helper methods like
the class-based `NamedTuple` can. The transformer will raise an Exception when
it finds a local `def` in a `NamedTuple` class - so you are restricted in
writing code that can be run on older python versions with this transformer.

Nethertheless, using simple `NamedTuple`-based classes is much easier to
read than the function-based `namedtuple`, AND type checkers can help
tracking the correct type for the fields of each instance.

        # original
        from typing import NamedTuple
        import socket

        class A(NamedTuple):
            b: int
            c: socket.socket

        # transformed
        from collections import namedtuple
        import socket
        A = namedtuple('A', ['b', 'c'])
        
