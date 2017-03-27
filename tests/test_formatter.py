import textwrap
import unittest

import click

from sphinx_click import ext


class GroupTestCase(unittest.TestCase):

    def test_no_parameters(self):
        """Validate a `click.Group` with no parameters.

        This exercises the code paths for a group with *no* arguments, *no*
        options and *no* environment variables.
        """

        @click.group()
        def cli():
            """A sample command group."""
            pass

        ctx = click.Context(cli, info_name='cli')
        output = list(ext._format_command(ctx, show_nested=False))

        self.assertEqual(textwrap.dedent("""
        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...
        """).lstrip(), '\n'.join(output))

    def test_basic_parameters(self):
        """Validate a combination of parameters.

        This exercises the code paths for a group with arguments, options and
        environment variables.
        """

        @click.group()
        @click.option('--param', envvar='PARAM', help='A sample option')
        @click.argument('ARG', envvar='ARG')
        def cli():
            """A sample command group."""
            pass

        ctx = click.Context(cli, info_name='cli')
        output = list(ext._format_command(ctx, show_nested=False))

        self.assertEqual(textwrap.dedent("""
        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] ARG COMMAND [ARGS]...

        .. rubric:: Options

        .. option:: --param <param>

            A sample option

        .. rubric:: Arguments

        .. option:: ARG

            Required argument

        .. rubric:: Environment variables

        .. envvar:: PARAM

            Provide a default for :option:`--param`

        .. envvar:: ARG

            Provide a default for :option:`ARG`
        """).lstrip(), '\n'.join(output))


class NestedCommandsTestCase(unittest.TestCase):

    @staticmethod
    def _get_ctx():

        @click.group()
        def cli():
            """A sample command group."""
            pass

        @cli.command()
        def hello():
            """A sample command."""
            pass

        return click.Context(cli, info_name='cli')

    def test_hide_nested(self):
        """Validate a nested command without show_nested.

        If we're not showing sub-commands separately, we should list them.
        """

        ctx = self._get_ctx()
        output = list(ext._format_command(ctx, show_nested=False))

        self.assertEqual(textwrap.dedent("""
        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...

        .. rubric:: Commands

        .. object:: hello

            A sample command.
        """).lstrip(), '\n'.join(output))

    def test_show_nested(self):
        """Validate a nested command without show_nested.

        If we're not showing sub-commands separately, we should not list them.
        """

        ctx = self._get_ctx()
        output = list(ext._format_command(ctx, show_nested=True))

        self.assertEqual(textwrap.dedent("""
        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...
        """).lstrip(), '\n'.join(output))
