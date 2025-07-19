## define-callable

This transformer cares about a weird choice to drop the `callable()` 
builtin in python 3.0. It was resurrected in python 3.2. As python3
did not catch on for production-level code until python 3.3 this
omission is often overlooked when writing portable code.

In any case, if a python3.0 or python3.1 is encountered then some
boilerplate-code gets activated for `callable()` bringing back
the global builtin function. As always, the extra code in the
import section gets only generated when some the `callable` 
function was actually used in the given script.


        # original
        def func1(x: Any):
            if callable(x):
                repr(x())

        # transformed
        import sys
        if sys.version_info >= (3, 0) and sys.version_info < (3, 2):
        
            def callable(x):
                return hasattr(x, '__call__')
        
        def func1(x):
            if callable(x):
                repr(x())

Note that if a `--python-version` of 3.2 or later is selected then
this transformer will not be executed at all. As it is extremely
unlikely to find a python 3.0 in 3.1 on a production server, it
safe to use `"--no-define-callable"` or just `"--noc"` on
the commandline (or use `no-define-callable = 1` in the 
`[tool.strip-python3]` section in the `pyproject.toml` file)


