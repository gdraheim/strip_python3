## replace-fstring

F-strings are widely used in python3 source code - but actually they did not exist
before Python 3.5. However `string.format` did exist before and fstrings is just
some syntactic sugar calling that function underneath. That allows a transformer
to replace `F"foo{bar}"` by `"foo{}".format(bar)`.

The underlying implementation of f-strings have been changed over time, so it
does even depend on the python version running the transformer what kind of
syntax can be transformed. So far, it did work fine on real code but be warned
that you may step on one of the corner cases. Specifically, the syntax of
`F{a=}` can not be reproduced as it the builtin parser itself returns 
`F"a={a!r}"` to the transformer.


        # original
        y = F"{a}"
        z = F"{a=}"
        q = F"{a:.2} {b!s}"


        # transformed
        y = '{}'.format(a)
        z = 'a={!r}'.format(a)
        q = '{:.2} {!s}'.format(a, b)

There is also the inverse transformer that can upgrade code to use fstrings
where they did use `.format` for compatibility. This transformer has to be selected
explicitly as `--fstring-from-var-locals`.

        # original
        y = 1
        x = "{y:n}"
        logg.warning("running %s", x)
        s = foo(x.format(**locals()))
        print(s)

        # transformed
        y = 1
        x = '{y:n}'
        logg.warning('running %s', x)
        s = foo(f'{y:n}')
        print(s)


