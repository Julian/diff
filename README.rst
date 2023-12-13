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


``diff`` defines a difference protocol. Watch:

.. code-block:: python

    >>> class LonelyObject:
    ...     def __diff__(self, other):
    ...         return f"{self} is not like {other}"
    ...
    ...     def __repr__(self):
    ...         return "<LonelyObject>"

    >>> from diff import diff
    >>> diff(LonelyObject(), 12).explain()
    '<LonelyObject> is not like 12'
