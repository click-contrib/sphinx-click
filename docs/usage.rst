Usage
=====

`sphinx-click` enables automatic documentation by way of a `Sphinx
directive`__.

.. rst:directive:: .. click:: module:parser

   Automatically extract documentation from a `click-based`__ application and
   include it in your docs.

   .. code-block:: rst

       .. click:: module:parser
          :prog: hello-world
          :show-nested:

   The directive takes the import name of the parser object as its sole
   argument.

   In addition, the following options are required:

   `:prog:`
     The name of your tool (or how it should appear in your documentation). For
     example, if you run your script as ``./boo --opts args`` then ``:prog:``
     will be ``boo``. If this is not given, the module name is used.

   The following options are optional:

   `:show-nested:`
     Enable full documentation for sub-commands.

   `:commands:`
     Document only listed commands.

__ http://www.sphinx-doc.org/en/stable/extdev/markupapi.html
__ http://click.pocoo.org/

Example
-------

Take the below `click` application, which is defined in the `example_app`
module:

.. code-block:: python

    import click

    @click.group()
    def greet():
        """A sample command group."""
        pass

    @greet.command()
    @click.argument('user')
    def hello(user):
        """Greet a user."""
        click.echo('Hello %s' % user)

    @greet.command()
    def world(user):
        """Greet the world."""
        click.echo('Hello world!')


To document this, use the following:

.. code-block:: rst

    .. click:: hello_world:greet
      :prog: hello-world

If you wish to include full documentation for the subcommand, ``hello``, in the
output, add the ``show-nested`` flag.

.. code-block:: rst

    .. click:: hello_world:greet
      :prog: hello-world
      :show-nested:

You can also document only selected commands by using ``:commands:`` option.

.. code-block:: rst

    .. click:: hello_world:greet
      :prog: hello-world
      :commands: hello

Modifying ``sys.path``
----------------------

If the application or script you wish to document is not installed (i.e. you
have not installed it with `pip` or run ``python setup.py``), then you may need
to modify ``sys.path``. For example, given the following application::

    git
      |- git
      |    |- __init__.py
      |    \- git.py
      \- docs
          |- git.rst
          |- index.rst
           \- conf.py

then it would be necessary to add the following to ``git/docs/conf.py``:

.. code-block:: python

   import os
   import sys
   sys.path.insert(0, os.path.abspath('..'))

Once done, you could include the following in ``git/docs/git.rst`` to document
the application:

.. code-block:: rst

    .. click:: git.git:cli
       :prog: git
       :show-nested:

assuming the group or command in ``git.git`` is named ``cli``.

Refer to `issue #2 <https://github.com/click-contrib/sphinx-click/issues/2>`__
for more information.
