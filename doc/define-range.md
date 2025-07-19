## define-range

The define-range is a simple one - the orignal python2 `range()` was actually
creating a temporary object containing all the numbers requested in the
range-call. However it was found that nobody really needed any list-object
call - only the elements were used in an iteration loop. So when the
generator-yield syntax came about, python2 introduced `xrange()` returning
an Iterator.

In python3 the `range()` call returns the Iterator. That's an unfortunate
choice (they should have justed dropped `range()` an kept `xrange()`).
When first writing code compatible for python2 and python3, it may be handy
to write with `xrange()` and make a define `xrange = range` when running
in python3 mode. However this transformer does the opposite - it defaults
to the python3 `range()` Iterator and overrides python2 `range()` with
its own `xrange()` Iterator. Yes, overriding bultin functions is allowed.


        # original
        def foo(x: int):
            for i in range(x):
               print(i)
        
        # transformed
        import sys
        if sys.version_info < (3, 0):
            range = xrange
            
        def foo(x: int):
            for i in range(x):
               print(i)


Note that if a `--python-version` of 3.0 or later is selected then
this transformer will not be executed at all.
            
