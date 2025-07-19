## define-absolute-import

The future "absolute_import" is the third of the usual three to be 
defined by default in your source code to make it portable from python2 to
python3. It enables to explicitly load from a local module instead of
using the global `sys.path` to find the `import name` as a file `name.py`.

The transformer gets triggered when it finds a from-dot, ie `from .this import that`.

        # original
        from .exceptions import MyException
        def func1(x: Any):
            print(x / 2)

        # transformed
        from __future__ import absolute_import, division, print_function
        from .exceptions import MyException
        
        def func1(x):
            print(x / 2)

Note that if a `--python-version` of 3.0 or later is selected then
this transformer will not be executed at all. If your code did
already contain a `from __future__` statement then the transformer
does not double the import of `absolute_import`, so the code stays
the same.

