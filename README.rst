====
diff
====

|PyPI| |Pythons| |CI| |pre-commit|

.. |PyPI| image:: https://img.shields.io/pypi/v/diff.svg
  :alt: PyPI version
  :target: https://pypi.org/project/diff/

.. |Pythons| image:: https://img.shields.io/pypi/pyversions/diff.svg
  :alt: Supported Python versions
  :target: https://pypi.org/project/diff/

.. |CI| image:: https://github.com/Julian/diff/workflows/CI/badge.svg
  :alt: Build status
  :target: https://github.com/Julian/diff/actions?query=workflow%3ACI

.. |pre-commit| image:: https://results.pre-commit.ci/badge/github/Julian/diff/main.svg
  :alt: pre-commit.ci status
  :target: https://results.pre-commit.ci/latest/github/Julian/diff/main


``diff`` defines a difference protocol.
Python objects can say *whether* they are equal, but never *why* they
aren't. Watch:

.. code-block:: python

    >>> from diff import Constant, diff

    >>> class LonelyObject:
    ...     def __diff__(self, other):
    ...         return Constant(explanation=f"{self} is not like {other}")
    ...
    ...     def __repr__(self):
    ...         return "<LonelyObject>"

    >>> diff(LonelyObject(), 12).explain()
    '<LonelyObject> is not like 12'

Equal objects have no difference at all:

.. code-block:: python

    >>> diff(12, 12) is None
    True

Types which will never implement the protocol are handled from the
outside, which covers the builtin containers as well as anything using
``attrs`` or ``dataclasses``:

.. code-block:: python

    >>> from dataclasses import dataclass

    >>> @dataclass
    ... class Point:
    ...     x: int
    ...     y: int

    >>> one = {"points": [Point(1, 2)], "name": "a"}
    >>> two = {"points": [Point(1, 9)], "name": "b"}
    >>> print(diff(one, two).explain())
    ['points'][0].y: 2 != 9
    ['name']: 'a' != 'b'

A class which knows how it differs needn't separately say how it
compares -- ``__eq__`` can be derived from ``__diff__``, where no
difference means equal:

.. code-block:: python

    >>> from diff import eq_from_diff

    >>> @eq_from_diff
    ... class Version:
    ...     def __init__(self, number):
    ...         self.number = number
    ...
    ...     def __diff__(self, other):
    ...         if not isinstance(other, Version):
    ...             return NotImplemented
    ...         if self.number == other.number:
    ...             return None
    ...         explanation = f"v{self.number} != v{other.number}"
    ...         return Constant(explanation=explanation)

    >>> Version(1) == Version(1)
    True
    >>> Version(1) == Version(2)
    False
    >>> diff(Version(1), Version(2)).explain()
    'v1 != v2'

Test suites are the obvious place to want all of this, so there's a
`pytest <https://docs.pytest.org/>`_ plugin (enabled simply by
installing this package) which explains failing ``==`` assertions, along
with a ``diff.unittest.TestCase`` whose ``assertEqual`` does the same.
