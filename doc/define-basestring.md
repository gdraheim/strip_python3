## define-basestring

The define-basestring transformation came from the habit that python2
uses "str" as a kind of "bytes"-variant. In order to support 2to3 the
python2 interpreter contains a "basestring" definition. I dont care
if that is a real base class for the two types or if it is just
a union-type or prototype decleration as you only ever use it in 
isinstance() calls - you do never create an instance of "basestring".

Since the "basestring" type is missing in python3, the transformer will 
check every isinstance() call in the script. If there is a check for "str"
then it gets replaced by "basestring" and the import-block gets an
equals-definition for "basestring" is-a "str".


        # original   
        def foo(x: Optional[str]):
            if isinstance(x, str):
                print(x)
           
        # transformed
        import sys
        if sys.version_info >= (3, 0):
            basestring = str

        def foo(x: Optional[str]):
            if isinstance(x, basestring):
                print(x)

Note that if a `--python-version` of 3.0 or later is selected then
this transformer will not be executed at all.

