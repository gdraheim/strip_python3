## define-print-function

Everybody knows this one: the python2 `"print x"` syntax was replaced
by `"print(x)"`. It turns out that many people writing code for python2
were also starting to use that syntax as a default to allow for easy
migration to python3 later. That was very simple - just import the future.


        # original
        def func1(x: Any):
            print(x())

        # transformed
        from __future__ import print_function
        
        def func1(x):
            print(x())

Note that if a `--python-version` of 3.0 or later is selected then
this transformer will not be executed at all. If your code did
already contain a `from __future__` statement then the transformer
does not double the import of `print_function`, so the code stays
the same.

