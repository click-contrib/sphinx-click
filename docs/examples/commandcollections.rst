.. _example_commandcollections:

Documentating |CommandCollection|
=================================

The client in the file ``examples/commandcollections/cli.py`` using a
|CommandCollection| such as

.. literalinclude:: ../../examples/commandcollections/cli.py

The automatic documentation using *sphinx-click* gives for the following directive:

.. code-block:: rst

   .. click:: commandcollections.cli:cli
     :prog: cli
     :nested: full

----

.. click:: commandcollections.cli:cli
  :prog: cli
  :nested: full


.. |CommandCollection| replace:: ``CommandCollection``
.. _CommandCollection: https://click.palletsprojects.com/en/7.x/api/#click.CommandCollection
