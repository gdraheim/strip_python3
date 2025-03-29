#! /usr/bin/env python3
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring
import sys
import unittest

sys.path.append("../src")
import strip_python3 as app  # pylint:disable=wrong-import-position

class StripUnitTest(unittest.TestCase):
    def test_0000(self) -> None:
        y = app.to_int("y")
        n = app.to_int("n")
        self.assertEqual(y, 1)
        self.assertEqual(n, 0)

if __name__ == "__main__":
    unittest.main()
