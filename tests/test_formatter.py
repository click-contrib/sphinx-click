import textwrap
import unittest

import click
from sphinx_click import ext


class CommandTestCase(unittest.TestCase):
    def test_no_parameters(self):
        """Validate a `click.Command` with no parameters.

        This exercises the code paths for a command with *no* arguments, *no*
        options and *no* environment variables.
        """

        @click.command()
        def foobar():
            """A sample command."""
            pass

        ctx = click.Context(foobar, info_name='foobar')
        output = list(ext._format_command(ctx, show_nested=False))

        self.assertEqual(
            textwrap.dedent("""
        A sample command.

        .. program:: foobar
        .. code-block:: shell

            foobar [OPTIONS]
        """).lstrip(), '\n'.join(output))

    def test_basic_parameters(self):
        """Validate a combination of parameters.

        This exercises the code paths for a command with arguments, options and
        environment variables.
        """

        @click.command()
        @click.option('--param', envvar='PARAM', help='A sample option')
        @click.option('--choice', help='A sample option with choices',
                      type=click.Choice(['Option1', 'Option2']))
        @click.argument('ARG', envvar='ARG')
        def foobar(bar):
            """A sample command."""
            pass

        ctx = click.Context(foobar, info_name='foobar')
        output = list(ext._format_command(ctx, show_nested=False))

        self.assertEqual(
            textwrap.dedent("""
        A sample command.

        .. program:: foobar
        .. code-block:: shell

            foobar [OPTIONS] ARG

        .. rubric:: Options

        .. option:: --param <param>

            A sample option

        .. option:: --choice <choice>

            A sample option with choices

            :options: Option1|Option2

        .. rubric:: Arguments

        .. option:: ARG

            Required argument

        .. rubric:: Environment variables

        .. _foobar-param-PARAM:

        .. envvar:: PARAM
           :noindex:

            Provide a default for :option:`--param`

        .. _foobar-arg-ARG:

        .. envvar:: ARG
           :noindex:

            Provide a default for :option:`ARG`
        """).lstrip(), '\n'.join(output))

    @unittest.skipIf(ext.CLICK_VERSION < (7, 0),
                     'The hidden flag was added in Click 7.0')
    def test_hidden(self):
        """Validate a `click.Command` with the `hidden` flag."""

        @click.command(hidden=True)
        def foobar():
            """A sample command."""
            pass

        ctx = click.Context(foobar, info_name='foobar')
        output = list(ext._format_command(ctx, show_nested=False))

        self.assertEqual('', '\n'.join(output))


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

        self.assertEqual(
            textwrap.dedent("""
        A sample command group.

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

        self.assertEqual(
            textwrap.dedent("""
        A sample command group.

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

        .. _cli-param-PARAM:

        .. envvar:: PARAM
           :noindex:

            Provide a default for :option:`--param`

        .. _cli-arg-ARG:

        .. envvar:: ARG
           :noindex:

            Provide a default for :option:`ARG`
        """).lstrip(), '\n'.join(output))

    def test_no_line_wrapping(self):
        r"""Validate behavior when a \b character is present.

        https://click.palletsprojects.com/en/7.x/documentation/#preventing-rewrapping
        """

        @click.group()
        def cli():
            """A sample command group.

            \b
            This is
            a paragraph
            without rewrapping.

            And this is a paragraph
            that will be rewrapped again.
            """
            pass

        ctx = click.Context(cli, info_name='cli')
        output = list(ext._format_command(ctx, show_nested=False))

        self.assertEqual(
            textwrap.dedent("""
        A sample command group.

        | This is
        | a paragraph
        | without rewrapping.

        And this is a paragraph
        that will be rewrapped again.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...
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

        self.assertEqual(
            textwrap.dedent("""
        A sample command group.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...

        .. rubric:: Commands

        .. object:: hello

            A sample command.
        """).lstrip(), '\n'.join(output))

    def test_show_nested(self):
        """Validate a nested command with show_nested.

        If we're not showing sub-commands separately, we should not list them.
        """

        ctx = self._get_ctx()
        output = list(ext._format_command(ctx, show_nested=True))

        self.assertEqual(
            textwrap.dedent("""
        A sample command group.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...
        """).lstrip(), '\n'.join(output))


class CommandFilterTestCase(unittest.TestCase):
    @staticmethod
    def _get_ctx():
        @click.group()
        def cli():
            """A sample command group."""

        @cli.command()
        def hello():
            """A sample command."""

        @cli.command()
        def world():
            """A world command."""

        return click.Context(cli, info_name='cli')

    def test_no_commands(self):
        """Validate an empty command group."""

        ctx = self._get_ctx()
        output = list(ext._format_command(ctx, show_nested=False, commands=''))

        self.assertEqual(
            textwrap.dedent("""
        A sample command group.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...
        """).lstrip(), '\n'.join(output))

    def test_order_of_commands(self):
        """Validate the order of commands."""

        ctx = self._get_ctx()
        output = list(ext._format_command(ctx, show_nested=False,
                                          commands='world, hello'))

        self.assertEqual(
            textwrap.dedent("""
        A sample command group.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...

        .. rubric:: Commands

        .. object:: world

            A world command.

        .. object:: hello

            A sample command.
        """).lstrip(), '\n'.join(output))


class CustomMultiCommandTestCase(unittest.TestCase):
    def test_basics(self):
        """Validate a custom ``click.MultiCommand`` with no parameters.

        This exercises the code paths to extract commands correctly from these
        commands.
        """

        @click.command()
        def hello():
            """A sample command."""

        @click.command()
        def world():
            """A world command."""

        class MyCLI(click.MultiCommand):
            _command_mapping = {
                'hello': hello,
                'world': world,
            }

            def list_commands(self, ctx):
                return ['hello', 'world']

            def get_command(self, ctx, name):
                return self._command_mapping[name]

        cli = MyCLI(help='A sample custom multicommand.')
        ctx = click.Context(cli, info_name='cli')
        output = list(ext._format_command(ctx, show_nested=False))

        self.assertEqual(
            textwrap.dedent("""
        A sample custom multicommand.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...

        .. rubric:: Commands

        .. object:: hello

            A sample command.

        .. object:: world

            A world command.
        """).lstrip(), '\n'.join(output))

    @unittest.skipIf(ext.CLICK_VERSION < (7, 0),
                     'The hidden flag was added in Click 7.0')
    def test_hidden(self):
        """Ensure 'hidden' subcommands are not shown."""
        @click.command()
        def hello():
            """A sample command."""

        @click.command()
        def world():
            """A world command."""

        @click.command(hidden=True)
        def hidden():
            """A hidden command."""

        class MyCLI(click.MultiCommand):
            _command_mapping = {
                'hello': hello,
                'world': world,
                'hidden': hidden,
            }

            def list_commands(self, ctx):
                return ['hello', 'world', 'hidden']

            def get_command(self, ctx, name):
                return self._command_mapping[name]

        cli = MyCLI(help='A sample custom multicommand.')
        ctx = click.Context(cli, info_name='cli')
        output = list(ext._format_command(ctx, show_nested=False))

        # Note that we do NOT expect this to show the 'hidden' command
        self.assertEqual(
            textwrap.dedent("""
        A sample custom multicommand.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...

        .. rubric:: Commands

        .. object:: hello

            A sample command.

        .. object:: world

            A world command.
        """).lstrip(), '\n'.join(output))
