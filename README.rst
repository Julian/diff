====
diff
====

|PyPI| |Pythons| |CI| |Codecov|

.. |PyPI| image:: https://img.shields.io/pypi/v/diff.svg
  :alt: PyPI version
  :target: https://pypi.org/project/diff/

.. |Pythons| image:: https://img.shields.io/pypi/pyversions/diff.svg
  :alt: Supported Python versions
  :target: https://pypi.org/project/diff/

.. |CI| image:: https://github.com/Julian/diff/workflows/CI/badge.svg
  :alt: Build status
  :target: https://github.com/Julian/diff/actions?query=workflow%3ACI

.. |Codecov| image:: https://codecov.io/gh/Julian/diff/branch/master/graph/badge.svg
  :alt: Codecov Code coverage
  :target: https://codecov.io/gh/Julian/diff


``diff`` defines a difference protocol. Watch:

.. code-block:: python

    >>> class LonelyObject(object):
    ...     def __diff__(self, other):
    ...         return "{} is not like {}".format(self, other)
    ...
    ...     def __repr__(self):
    ...         return "<LonelyObject>"

    >>> from diff import diff
    >>> diff(LonelyObject(), 12).explain()
    '<LonelyObject> is not like 12'
