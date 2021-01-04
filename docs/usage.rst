Usage
=====

To enable the plugin, add the extension to the list of extensions in your
Sphinx `conf.py` file:

.. code-block:: python

   extensions = ['sphinx_click']

Once enabled, *sphinx-click* enables automatic documentation for
`click-based`_ applications by way of a `Sphinx directive`_.

.. rst:directive:: .. click:: module:parser

   Automatically extract documentation from a `click-based`_ application and
   include it in your docs.

   .. code-block:: rst

       .. click:: module:parser
          :prog: hello-world
          :nested: full

   The directive takes the import name of a *click* object as its sole
   argument. This should be a subclass of |click.core.BaseCommand|_, such as
   ``click.Command``, ``click.Group``, ``click.MultiCommand``, etc.

   In addition, the following options are required:

   ``:prog:``
     The name of your tool (or how it should appear in your documentation). For
     example, if you run your script as ``./boo --opts args`` then ``:prog:``
     will be ``boo``. If this is not given, the module name is used.

   The following options are optional:

   ``:nested:``
     Whether subcommands should also be shown. One of:

     ``full``
       List sub-commands with full documentation.

    ``short``
       List sub-commands with short documentation.

    ``none``
       Do not list sub-commands.

     Defaults to ``short`` unless ``show-nested`` (deprecated) is set.

   ``:commands:``
     Document only listed commands.

   ``:show-nested:``
     This option is deprecated; use ``nested`` instead.

   The generated documentation includes anchors for the generated commands,
   their options and their environment variables using the `Sphinx standard
   domain`_.

.. _Sphinx directive: http://www.sphinx-doc.org/en/stable/extdev/markupapi.html
.. _click-based: http://click.pocoo.org/6/
.. _Sphinx standard domain: http://www.sphinx-doc.org/en/stable/domains.html#the-standard-domain
.. |click.core.BaseCommand| replace:: ``click.core.BaseCommand``
.. _click.core.BaseCommand: http://click.pocoo.org/6/api/#click.BaseCommand

Example
-------

Take the below ``click`` application, which is defined in the ``hello_world``
module:

.. code-block:: python

    import click

    @click.group()
    def greet():
        """A sample command group."""
        pass

    @greet.command()
    @click.argument('user', envvar='USER')
    def hello(user):
        """Greet a user."""
        click.echo('Hello %s' % user)

    @greet.command()
    def world():
        """Greet the world."""
        click.echo('Hello world!')

To document this, use the following:

.. code-block:: rst

    .. click:: hello_world:greet
      :prog: hello-world

By default, the subcommand, ``hello``, is listed but no documentation provided.
If you wish to include full documentation for the subcommand in the output,
configure the ``nested`` flag to ``full``.

.. code-block:: rst

    .. click:: hello_world:greet
      :prog: hello-world
      :nested: full

.. note::

    The ``nested`` flag replaces the deprecated ``show-nested`` flag.

Conversely, if you do not wish to list these subcommands or wish to handle them
separately, configure the ``nested`` flag to ``none``.

.. code-block:: rst

    .. click:: hello_world:greet
      :prog: hello-world
      :nested: none

You can also document only selected commands by using ``:commands:`` option.

.. code-block:: rst

    .. click:: hello_world:greet
      :prog: hello-world
      :commands: hello

You can cross-reference the commands, option and environment variables using
the roles provided by the `Sphinx standard domain`_.

.. code-block:: rst

    .. click:: hello_world:greet
       :prog: hello-world

    The :program:`hello` command accepts a :option:`user` argument. If this is
    not provided, the :envvar:`USER` environment variable will be used.

.. note::

    Cross-referencing using the ``:program:`` directive is not currently
    supported by Sphinx. Refer to the `Sphinx issue`__ for more information.

    __ https://github.com/sphinx-doc/sphinx/issues/880

Documenting |CommandCollection|_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When building more complex CLI, one might need to bring together multiple groups
of commands and make them accessible using a single client with |CommandCollection|_.
*sphinx-click* renders collection of commands with multiple sections, one for each
group listed in the command ``sources``. The group names are used as section titles
and the help string from the description are used as section description.
Thus, a client defined using a |CommandCollection| as ``cli`` can be rendered
using *sphinx-click* and the following directive:

.. code-block:: rst

   .. click:: cli:cli
      :prog: cli
      :nested: full

This will render the subcommands of each group in different sections, one for each
group in ``sources``. An example is provided in :doc:`examples/commandcollections`.


Modifying ``sys.path``
----------------------

If the application or script you wish to document is not installed (i.e. you
have not installed it with *pip* or run ``python setup.py``), then you may need
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
       :nested: full

assuming the group or command in ``git.git`` is named ``cli``.

Refer to `issue #2 <https://github.com/click-contrib/sphinx-click/issues/2>`__
for more information.

.. |CommandCollection| replace:: :code:`CommandCollection`
.. _CommandCollection: https://click.palletsprojects.com/en/7.x/api/#click.CommandCollection
