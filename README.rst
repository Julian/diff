====
diff
====


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
