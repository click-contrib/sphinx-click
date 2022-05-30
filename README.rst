============
sphinx-click
============

.. image:: https://github.com/click-contrib/sphinx-click/actions/workflows/ci.yaml/badge.svg
    :target: https://github.com/click-contrib/sphinx-click/actions/workflows/ci.yaml
    :alt: Build Status

.. image:: https://readthedocs.org/projects/sphinx-click/badge/?version=latest
    :target: https://sphinx-click.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

`sphinx-click` is a `Sphinx`__ plugin that allows you to automatically extract
documentation from a `click-based`__ application and include it in your docs.

__ http://www.sphinx-doc.org/
__ http://click.pocoo.org/

Installation
------------

Install the plugin using `pip`:

.. code-block:: shell

   $ pip install sphinx-click

Alternatively, install from source by cloning this repo then running `pip`
locally:

.. code-block:: shell

   $ pip install .

Usage
-----

.. important::

   To document a click-based application, both the application itself and any
   additional dependencies required by that application **must be installed**.

Enable the plugin in your Sphinx `conf.py` file:

.. code-block:: python

   extensions = ['sphinx_click']

Once enabled, you can now use the plugin wherever necessary in the
documentation.

.. code-block::

   .. click:: module:parser
      :prog: hello-world
      :nested: full

Detailed information on the various options available is provided in the
`documentation <https://sphinx-click.readthedocs.io>`_.
