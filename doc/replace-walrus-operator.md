## replace-walrus-operator

The walrus-operator `:=` allows to set local variable from an expression contexts.
That is a generalized function that works everywhere and could potententionally
replace the normal let-statement `a = 1`.

In reality however, the walrus-operator is only used in condition-expressions
of "if" and "while". Especially for the "while"-case it saves a lot of lines
to be written in the source code - and it much more readable. That makes it
to creep into source code all the while even that it did not exist before python 3.8

The transformer is limited to the special case of defining a variable in a
condition-expression and to evaluate the value right away. Only the conditions
of "if" and "while" are checked.

        # original
        def foo(b):
            while (x := int(b)) is not None:
                b += y
            return 0

        # transformed
        def foo(b):
            while True:
                x = int(b)
                if x is not None:
                    b += y
                else:
                    break
            return 0

and the more simpler if-block

        # original
        if x := fu(): pass

        # transformed
        x = fu()
        if x: pass


