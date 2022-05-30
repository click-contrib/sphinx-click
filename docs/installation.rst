Installation
============

Install the plugin using `pip`:

.. code-block:: shell

   $ pip install sphinx-click

Alternatively, install from source by cloning this repo then running
`setup.py`:

.. code-block:: shell

   $ python setup.py install

*sphinx-click* supports both `click`__ and `asyncclick`__. If *asyncclick* is
found, it will be preferred.

.. important::

   Both the package you're referencing and any dependencies **must be
   installed**.

.. __: https://pypi.org/project/click/
.. __: https://pypi.org/project/asyncclick/
