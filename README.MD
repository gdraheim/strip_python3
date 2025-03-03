# easy way to transform and remove python3 typehints

This project has been inspired by `'strip-hints'` and `'py-backwards'` but it is
now based on the Python 3.9+ standard library's `'ast.unparse()'`. More specifically
it is using `'ast_comments'` to keep the comments. The implementation wants to make
it very easy so that you can add your own source code transformations.

As a bonus, `'strip_python3'` can extract typehints to `'*.pyi'` file containing only
the outer object-oriented interface.


# references

* https://github.com/t3rn0/ast-comments/blob/master/ast_comments.py (copied)
* https://github.com/python/typed_ast (archived)
* https://github.com/nvbn/py-backwards (stopped)
* https://github.com/abarker/strip-hints (still active)

# background

The "typed_ast" project was started in April 2016 showing a way to hand type comments.
The "py-backwards" project delivered an "unparse()" function for "typed_ast" in May 2017.
It also showed a generic approach to code transformers. However the syntactic sugar for
python3 grew over time and while its own "ast" "parse()" was getting better. Since 
Python 3.8 in 2019 the "typed_ast" project was discontinued and archived in 2023. Since
Python 3.9 in 2020 the "ast" module got its own "unparse()" function. And in 2022 the
"ast-comments" module showed how to hook into the standard module - the standard python3 
"ast.parse()" got an "enrich()" phase for adding "Comment" nodes, and the standard python3 
Unparser class got a "handle_Comment" to decent source code back from it.

Since then the standard python3 features a NodeTransformer class that is supposedly
making it easy to rewrite python code. However we are missing examples - if it is
used then it is buried deep in other projects. I would like to assemble some of these
python code transformations, specifically for removing newer features so that python
code can be shipped and used on older systems with some possibly archaic python version.
The "py-backwards" has stopped at a point somehwere around python 3.6, so a new start
is required with a code base that makes it easier to get contributions by users.

Speficifally for removing typehints, the "strip-hints" project shows how to use the
standard python "tokenizer" module which is clearly better than using some grep/sed
style text transformations. In both variants however you need to guess what kind of code
you have on a specific line, which is where "ast"-based approaches have a much easier
time. The standard python3 "unparse()" is however producing code that is formatted
good enough for shipping via pypi and other distribution channels. The differences
to the output of code beautyfiers have become minimal. Note however that the code
removal does sometimes make comments appear on lines where they don't belong to.



