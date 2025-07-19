## datetime-fromisoformat

The `fromisoformat(x: str)` from stdlib `datetime` type is very useful to parse
dates from machine-generated timestamps. However it is often overlooked that
it is only part of the stdlib module since python 3.7.

When fromisoformat is found in the code then the transformer will add some
boilerplate code under the name `datetime_fromisoformat`. When the script
is run under python 3.7 or later then the function is just calling the
stdlib `datetime.fromisoformat`. If the `datetime.datime` module has already
been imported but under a different name then that name is going to be used
as the prefix. 


        # original
        import datetime.datetime as Time
        def func1(x: x) -> Time:
            return Time.fromisoformat(x)
        """)

        # transformed
        
        import sys
        import datetime.datetime as Time
        if sys.version_info >= (3, 7):

            def Time_fromisoformat(x):
                return Time.fromisoformat(x)
        else:
        
            def Time_fromisoformat(x):
                import re
                m = re.match('(\\\\d\\\\d\\\\d\\\\d)-(\\\\d\\\\d)-(\\\\d\\\\d).(\\\\d\\\\d):(\\\\d\\\\d):(\\\\d\\\\d).(\\\\d\\\\d\\\\d\\\\d\\\\d\\\\d)', x)
                if m:
                    return Time(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7)))
                m = re.match('(\\\\d\\\\d\\\\d\\\\d)-(\\\\d\\\\d)-(\\\\d\\\\d).(\\\\d\\\\d):(\\\\d\\\\d):(\\\\d\\\\d).(\\\\d\\\\d\\\\d)', x)
                if m:
                    return Time(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7)) * 1000)
                m = re.match('(\\\\d\\\\d\\\\d\\\\d)-(\\\\d\\\\d)-(\\\\d\\\\d).(\\\\d\\\\d):(\\\\d\\\\d):(\\\\d\\\\d)', x)
                if m:
                    return Time(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)))
                m = re.match('(\\\\d\\\\d\\\\d\\\\d)-(\\\\d\\\\d)-(\\\\d\\\\d).(\\\\d\\\\d):(\\\\d\\\\d)', x)
                if m:
                    return Time(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))
                m = re.match('(\\\\d\\\\d\\\\d\\\\d)-(\\\\d\\\\d)-(\\\\d\\\\d)', x)
                if m:
                    return Time(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                raise ValueError('not a datetime isoformat: ' + x)
        
        def func1(x):
            return Time_fromisoformat(x)

Note that if a `--python-version` of 3.7 or later is selected then
this transformer will not be executed at all.

