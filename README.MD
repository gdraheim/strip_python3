# easy way to transform and remove python3 typehints

This project has been inspired by `'strip-hints'` and `'py-backwards'` but it is
now based on the Python 3.9+ standard library's `'ast.unparse()'`. More specifically
it is using `'ast_comments'` to keep the comments. The implementation wants to make
it very easy so that you can add your own transformations.

As a bonus, `'strip_python3'` can extract typehints to `'*.pyi'` file containing only
the outer object-oriented interface.


# references

* https://github.com/t3rn0/ast-comments/blob/master/ast_comments.py
