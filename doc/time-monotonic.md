# time-monotonic

A common error by programmers is to use `time.time()` taking the difference of two calls
as the time passed between the timestamps. But that is not true - as the `time()` value 
represents a wallclock time that may jump due to leap seconds and daylight saving time.
Instead you have to use a monotonic clock.

However the `time.monotonic()` function did not arrive before python 3.3. And a better
`time.monotonic_ns()` did only arrive in python 3.7. Of course each of the functions
can be replaced by the earlier one if not yet available - so the boilerplate code
is just a single line for each replacement function.

The transfomer checks the source code and if `time.monotonic()` is found then it 
replaced by `time_monotonic()` being locally defined function in the import section 
that either calls the stdlib function `time.monotonic()` or `time.time()`. Same if 
`time.monotonic_ns()` is found then it replaced by `time_monotonic_ns()` that
either calls `time.monotonic_ns()` or `time.monotonic()` scaling the value up.
If `time` has been imported under a different name already then that name is
used as the prefix for the wrapper functions.

        # original
        import time
        def func1() -> int:
            started = time.monotonic()
            time.sleep(0.8)
            stopped = time.monotonic()
            return stopped-started

        # transformed
        import sys
        import time
        if sys.version_info >= (3, 3):
            time_monotonic = time.monotonic
        else:
        
            def time_monotonic():
                return time.time()

        def func1():
            started = time_monotonic()
            time.sleep(0.8)
            stopped = time_monotonic()
            return stopped - started

and

        # original
        from time import monotonic_ns, sleep
        def func1() -> int:
            started = monotonic_ns()
            sleep(0.8)
            stopped = monotonic_ns()
            return stopped-started

        # transformed
        import sys, time
        from time import sleep
        if sys.version_info >= (3, 7):
            time_monotonic_ns = time.monotonic_ns
        else:

            def time_monotonic_ns():
                return int((time.time() - 946684800) * 1000000000)

        def func1():
            started = time_monotonic_ns()
            sleep(0.8)
            stopped = time_monotonic_ns()
            return stopped - started

