## define-print-function

The change in python3 is sometimes overlooked: the division operator `/`
has been changed to always return float values. In python2 however,
if the both values are integer, it returns an integer - dropping the
fraction part that may have come from the division. So if code
written for python3 is run in python2, the result values change.

Again, there is a future statement in python2 and the integer `//`
division has been backported as well. So it is safe to force the
code to the newer result strategy in either python2 or python3.

        # original
        def func1(x: Any):
            print(x / 2)

        # transformed
        from __future__ import division, print_function
        
        def func1(x):
            print(x / 2)

Note that if a `--python-version` of 3.0 or later is selected then
this transformer will not be executed at all. If your code did
already contain a `from __future__` statement then the transformer
does not double the import of `division`, so the code stays
the same.

