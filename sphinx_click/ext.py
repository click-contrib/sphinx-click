import collections.abc
import inspect
import functools
import re
import traceback
import typing as ty
import warnings
import itertools

try:
    import asyncclick as click
except ImportError:
    import click
import click.core
from docutils import nodes
from docutils.parsers import rst
from docutils.parsers.rst import directives
from docutils import statemachine
from sphinx import application
from sphinx.util import logging
from sphinx.util import nodes as sphinx_nodes
from sphinx.ext.autodoc import mock

LOG = logging.getLogger(__name__)

NESTED_COMPLETE = 'complete'
NESTED_FULL = 'full'
NESTED_SHORT = 'short'
NESTED_NONE = 'none'
NestedT = ty.Literal['complete', 'full', 'short', 'none', None]

ANSI_ESC_SEQ_RE = re.compile(r'\x1B\[\d+(;\d+){0,2}m', flags=re.MULTILINE)

_T_Formatter = ty.Callable[[click.Context], ty.Generator[str, None, None]]


def _process_lines(event_name: str) -> ty.Callable[[_T_Formatter], _T_Formatter]:
    def decorator(func: _T_Formatter) -> _T_Formatter:
        @functools.wraps(func)
        def process_lines(ctx: click.Context) -> ty.Generator[str, None, None]:
            lines = list(func(ctx))
            if "sphinx-click-env" in ctx.meta:
                ctx.meta["sphinx-click-env"].app.events.emit(event_name, ctx, lines)
            for line in lines:
                yield line

        return process_lines

    return decorator


def _indent(text: str, level: int = 1) -> str:
    prefix = ' ' * (4 * level)

    def prefixed_lines() -> ty.Generator[str, None, None]:
        for line in text.splitlines(True):
            yield (prefix + line if line.strip() else line)

    return ''.join(prefixed_lines())


def _get_usage(ctx: click.Context) -> str:
    """Alternative, non-prefixed version of 'get_usage'."""
    formatter = ctx.make_formatter()
    pieces = ctx.command.collect_usage_pieces(ctx)
    formatter.write_usage(ctx.command_path, ' '.join(pieces), prefix='')
    return formatter.getvalue().rstrip('\n')  # type: ignore


def _get_help_record(ctx: click.Context, opt: click.core.Option) -> ty.Tuple[str, str]:
    """Re-implementation of click.Opt.get_help_record.

    The variant of 'get_help_record' found in Click makes uses of slashes to
    separate multiple opts, and formats option arguments using upper case. This
    is not compatible with Sphinx's 'option' directive, which expects
    comma-separated opts and option arguments surrounded by angle brackets [1].

    [1] http://www.sphinx-doc.org/en/stable/domains.html#directive-option
    """

    def _write_opts(opts: ty.List[str]) -> str:
        rv, _ = click.formatting.join_options(opts)
        if not opt.is_flag and not opt.count:
            name = opt.name
            if opt.metavar:
                name = opt.metavar.lstrip('<[{($').rstrip('>]})$')
            rv += ' <{}>'.format(name)
        return rv  # type: ignore

    rv = [_write_opts(opt.opts)]
    if opt.secondary_opts:
        rv.append(_write_opts(opt.secondary_opts))

    out = []
    if opt.help:
        if opt.required:
            out.append('**Required** %s' % opt.help)
        else:
            out.append(opt.help)
    else:
        if opt.required:
            out.append('**Required**')

    extras = []

    if opt.show_default is not None:
        show_default = opt.show_default
    else:
        show_default = ctx.show_default

    if isinstance(show_default, str):
        # Starting from Click 7.0 show_default can be a string. This is
        # mostly useful when the default is not a constant and
        # documentation thus needs a manually written string.
        extras.append(':default: ``%r``' % ANSI_ESC_SEQ_RE.sub('', show_default))
    elif show_default and opt.default is not None:
        extras.append(
            ':default: ``%s``'
            % (
                ', '.join(repr(d) for d in opt.default)
                if isinstance(opt.default, (list, tuple))
                else repr(opt.default),
            )
        )

    if isinstance(opt.type, click.Choice):
        extras.append(':options: %s' % ' | '.join(str(x) for x in opt.type.choices))

    if extras:
        if out:
            out.append('')

        out.extend(extras)

    return ', '.join(rv), '\n'.join(out)


def _format_help(help_string: str) -> ty.Generator[str, None, None]:
    help_string = inspect.cleandoc(ANSI_ESC_SEQ_RE.sub('', help_string))

    bar_enabled = False
    for line in statemachine.string2lines(
        help_string, tab_width=4, convert_whitespace=True
    ):
        if line == '\b':
            bar_enabled = True
            continue
        if line == '':
            bar_enabled = False
        line = '| ' + line if bar_enabled else line
        yield line
    yield ''


@_process_lines("sphinx-click-process-description")
def _format_description(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format the description for a given `click.Command`.

    We parse this as reStructuredText, allowing users to embed rich
    information in their help messages if they so choose.
    """
    help_string = ctx.command.help or ctx.command.short_help
    if help_string:
        yield from _format_help(help_string)


@_process_lines("sphinx-click-process-usage")
def _format_usage(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format the usage for a `click.Command`."""
    yield '.. code-block:: shell'
    yield ''
    for line in _get_usage(ctx).splitlines():
        yield _indent(line)
    yield ''


def _format_command_name(ctx: click.Context) -> str:
    command_name: str = ctx.command_path.replace(' ', '-')
    return command_name


def _format_option(
    ctx: click.Context, opt: click.core.Option
) -> ty.Generator[str, None, None]:
    """Format the output for a `click.core.Option`."""

    # Add an anchor for each form of option name
    # For click.option('--flag', '-f', ...) it'll create anchors for "flag" and "f"
    option_names = list(set([option_name.lstrip('-') for option_name in opt.opts]))
    for option_name in option_names:
        yield '.. _{command_name}-{param}:'.format(
            command_name=_format_command_name(ctx), param=option_name
        )
        yield ''

    opt_help = _get_help_record(ctx, opt)

    yield '.. option:: {}'.format(opt_help[0])
    if opt_help[1]:
        yield ''
        bar_enabled = False
        for line in statemachine.string2lines(
            ANSI_ESC_SEQ_RE.sub('', opt_help[1]), tab_width=4, convert_whitespace=True
        ):
            if line == '\b':
                bar_enabled = True
                continue
            if line == '':
                bar_enabled = False
            line = '| ' + line if bar_enabled else line
            yield _indent(line)


@_process_lines("sphinx-click-process-options")
def _format_options(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format all `click.Option` for a `click.Command`."""
    # the hidden attribute is part of click 7.x only hence use of getattr
    params = [
        param
        for param in ctx.command.params
        if isinstance(param, click.core.Option) and not getattr(param, 'hidden', False)
    ]

    for param in params:
        for line in _format_option(ctx, param):
            yield line
        yield ''


def _format_argument(
    ctx: click.Context,
    arg: click.Argument,
) -> ty.Generator[str, None, None]:
    """Format the output of a `click.Argument`."""
    yield '.. _{command_name}-{param}:'.format(
        command_name=_format_command_name(ctx), param=arg.human_readable_name
    )
    yield ''

    yield '.. option:: {}'.format(arg.human_readable_name)
    yield ''
    yield _indent(
        '{} argument{}'.format(
            'Required' if arg.required else 'Optional', '(s)' if arg.nargs != 1 else ''
        )
    )
    # Subclasses of click.Argument may add a `help` attribute (like typer.main.TyperArgument)
    help = getattr(arg, 'help', None)
    if help:
        yield ''
        help_string = ANSI_ESC_SEQ_RE.sub('', help)
        for line in _format_help(help_string):
            yield _indent(line)


@_process_lines("sphinx-click-process-arguments")
def _format_arguments(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format all `click.Argument` for a `click.Command`."""
    params = [x for x in ctx.command.params if isinstance(x, click.Argument)]

    for param in params:
        for line in _format_argument(ctx, param):
            yield line
        yield ''


def _format_envvar(
    ctx: click.Context,
    param: click.core.Parameter,
) -> ty.Generator[str, None, None]:
    """Format the envvars of a `click.Option` or `click.Argument`."""
    command_name = _format_command_name(ctx)

    # Add an anchor for each form of parameter name
    # For click.option('--flag', '-f', ...) it'll create anchors for "flag" and "f"
    param_names = sorted(set(param_name.lstrip('-') for param_name in param.opts))

    # Only add the parameter's own name if it's not already present, in whatever case
    if param.name.upper() not in (
        name.upper() for name in param_names
    ):  # Case-insensitive "in" test
        param_names.append(param.name)

    for param_name in param_names:
        yield '.. _{command_name}-{param_name}-{envvar}:'.format(
            command_name=command_name,
            param_name=param_name,
            envvar=param.envvar,
        )
        yield ''

    yield '.. envvar:: {}'.format(param.envvar)
    yield '   :noindex:'
    yield ''
    if isinstance(param, click.Argument):
        param_ref = param.human_readable_name
    else:
        # if a user has defined an opt with multiple "aliases", always use the
        # first. For example, if '--foo' or '-f' are possible, use '--foo'.
        param_ref = param.opts[0]

    yield _indent('Provide a default for :option:`{}`'.format(param_ref))


@_process_lines("sphinx-click-process-envars")
def _format_envvars(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format all envvars for a `click.Command`."""

    auto_envvar_prefix = ctx.auto_envvar_prefix
    if auto_envvar_prefix is not None:
        params = []
        for param in ctx.command.params:
            if not param.envvar:
                param.envvar = f"{auto_envvar_prefix}_{param.name.upper()}"
            params.append(param)
    else:
        params = [x for x in ctx.command.params if x.envvar]

    for param in params:
        for line in _format_envvar(ctx, param):
            yield line
        yield ''


def _format_subcommand(command: click.Command) -> ty.Generator[str, None, None]:
    """Format a sub-command of a `click.Command` or `click.Group`."""
    yield '.. object:: {}'.format(command.name)

    short_help = command.get_short_help_str()

    if short_help:
        yield ''
        for line in statemachine.string2lines(
            short_help, tab_width=4, convert_whitespace=True
        ):
            yield _indent(line)


@_process_lines("sphinx-click-process-epilog")
def _format_epilog(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format the epilog for a given `click.Command`.

    We parse this as reStructuredText, allowing users to embed rich
    information in their help messages if they so choose.
    """
    if ctx.command.epilog:
        yield from _format_help(ctx.command.epilog)


def _get_lazyload_commands(
    ctx: click.Context, multi_command: click.MultiCommand
) -> ty.Dict[str, click.Command]:
    commands = {}
    for command in multi_command.list_commands(ctx):
        commands[command] = multi_command.get_command(ctx, command)

    return commands


def _filter_commands(
    ctx: click.Context,
    commands: ty.Optional[ty.List[str]] = None,
) -> ty.List[click.Command]:
    """Return list of used commands."""
    lookup = getattr(ctx.command, 'commands', {})
    if not lookup and isinstance(ctx.command, click.MultiCommand):
        lookup = _get_lazyload_commands(ctx, ctx.command)

    if commands is None:
        return sorted(lookup.values(), key=lambda item: item.name)

    return [lookup[command] for command in commands if command in lookup]


def _format_header(ctx: click.Context) -> ty.Generator[str, None, None]:
    for line in _format_description(ctx):
        yield line

    yield '.. _{command_name}:'.format(
        command_name=_format_command_name(ctx),
    )
    yield ''
    yield '.. program:: {}'.format(ctx.command_path)


def _format_subcommand_summary(
    ctx: click.Context,
    commands: ty.Optional[ty.List[str]] = None,
) -> ty.Generator[str, None, None]:
    command_objs = _filter_commands(ctx, commands)

    if command_objs:
        yield '.. rubric:: Commands'
        yield ''

    for command_obj in command_objs:
        # Don't show hidden subcommands
        if command_obj.hidden:
            continue

        for line in _format_subcommand(command_obj):
            yield line
        yield ''


def _format_command(
    ctx: click.Context,
    nested: NestedT,
    commands: ty.Optional[ty.List[str]] = None,
    hide_header: bool = False,
) -> ty.Generator[str, None, None]:
    """Format the output of `click.Command`."""
    if ctx.command.hidden:
        return None

    # description

    if nested == NESTED_NONE or not hide_header:
        for line in _format_header(ctx):
            yield line

    # usage

    for line in _format_usage(ctx):
        yield line

    # options

    lines = list(_format_options(ctx))
    if lines:
        # we use rubric to provide some separation without exploding the table
        # of contents
        yield '.. rubric:: Options'
        yield ''

    for line in lines:
        yield line

    # arguments

    lines = list(_format_arguments(ctx))
    if lines:
        yield '.. rubric:: Arguments'
        yield ''

    for line in lines:
        yield line

    # environment variables

    lines = list(_format_envvars(ctx))
    if lines:
        yield '.. rubric:: Environment variables'
        yield ''

    for line in lines:
        yield line

    # description

    for line in _format_epilog(ctx):
        yield line

    # if we're nesting commands, we need to do this slightly differently
    if nested in (NESTED_FULL, NESTED_NONE):
        return

    for line in _format_subcommand_summary(ctx, commands):
        yield line


def _format_summary(
    ctx: click.Context,
    commands: ty.Optional[ty.List[str]] = None,
    hide_header: bool = False,
) -> ty.Generator[str, None, None]:
    """Format the output of `click.Command`."""
    if ctx.command.hidden:
        return

    if not hide_header:
        # description
        for line in _format_header(ctx):
            yield line

        # usage
        for line in _format_usage(ctx):
            yield line

    for line in _format_subcommand_summary(ctx, commands):
        yield line


def nested(argument: ty.Optional[str]) -> NestedT:
    values = (NESTED_COMPLETE, NESTED_FULL, NESTED_SHORT, NESTED_NONE, None)

    if argument not in values:
        raise ValueError(
            "%s is not a valid value for ':nested:'; allowed values: %s"
            % directives.format_values(values)
        )

    return ty.cast(NestedT, argument)


class ClickDirective(rst.Directive):
    has_content = False
    required_arguments = 1
    option_spec = {
        'prog': directives.unchanged_required,
        'nested': nested,
        'commands': directives.unchanged,
        'show-nested': directives.flag,
        'hide-header': directives.flag,
        'post-process': directives.unchanged_required,
    }

    def _load_module(self, module_path: str) -> ty.Any:
        """Load the module."""

        try:
            module_name, attr_name = module_path.split(':', 1)
        except ValueError:  # noqa
            raise self.error(
                '"{}" is not of format "module:parser"'.format(module_path)
            )

        try:
            with mock(self.env.config.sphinx_click_mock_imports):
                mod = __import__(module_name, globals(), locals(), [attr_name])
        except (Exception, SystemExit) as exc:  # noqa
            err_msg = 'Failed to import "{}" from "{}". '.format(attr_name, module_name)
            if isinstance(exc, SystemExit):
                err_msg += 'The module appeared to call sys.exit()'
            else:
                err_msg += 'The following exception was raised:\n{}'.format(
                    traceback.format_exc()
                )

            raise self.error(err_msg)

        if not hasattr(mod, attr_name):
            raise self.error(
                'Module "{}" has no attribute "{}"'.format(module_name, attr_name)
            )

        return getattr(mod, attr_name)

    def _generate_nodes(
        self,
        name: str,
        command: click.Command,
        parent: ty.Optional[click.Context],
        nested: NestedT,
        commands: ty.Optional[ty.List[str]] = None,
        semantic_group: bool = False,
        hide_header: bool = False,
    ) -> ty.List[nodes.Element]:
        """Generate the relevant Sphinx nodes.

        Format a `click.Group` or `click.Command`.

        :param name: Name of command, as used on the command line
        :param command: Instance of `click.Group` or `click.Command`
        :param parent: Instance of `click.Context`, or None
        :param nested: The granularity of subcommand details.
        :param commands: Display only listed commands or skip the section if
            empty
        :param semantic_group: Display command as title and description for
            `click.CommandCollection`.
        :param hide_header: Hide the title and summary.
        :returns: A list of nested docutil nodes
        """
        ctx = click.Context(command, info_name=name, parent=parent)

        if command.hidden:
            return []

        # Summary
        source_name = ctx.command_path
        result = statemachine.StringList()

        lines: collections.abc.Iterator[str] = iter(())
        hide_current_header = hide_header
        if nested == NESTED_COMPLETE:
            lines = itertools.chain(lines, _format_summary(ctx, commands, hide_header))
            nested = ty.cast(NestedT, NESTED_FULL)
            hide_current_header = True

        ctx.meta["sphinx-click-env"] = self.env
        if semantic_group:
            lines = itertools.chain(lines, _format_description(ctx))
        else:
            lines = itertools.chain(
                lines, _format_command(ctx, nested, commands, hide_current_header)
            )

        for line in lines:
            LOG.debug(line)
            result.append(line, source_name)

        # Subcommands

        subcommand_nodes = []
        if nested == NESTED_FULL:
            if isinstance(command, click.CommandCollection):
                for source in command.sources:
                    subcommand_nodes.extend(
                        self._generate_nodes(
                            source.name,
                            source,
                            parent=ctx,
                            nested=nested,
                            semantic_group=True,
                            hide_header=False,  # Hiding the header should not propagate to children
                        )
                    )
            else:
                # We use the term "subcommand" here but these can be main commands as well
                for subcommand in _filter_commands(ctx, commands):
                    parent = ctx if not semantic_group else ctx.parent
                    subcommand_nodes.extend(
                        self._generate_nodes(
                            subcommand.name,
                            subcommand,
                            parent=parent,
                            nested=nested,
                            hide_header=False,  # Hiding the header should not propagate to children
                        )
                    )

        final_nodes: ty.List[nodes.Element]
        section: nodes.Element
        if hide_header:
            final_nodes = subcommand_nodes

            if nested == NESTED_NONE or nested == NESTED_SHORT:
                section = nodes.paragraph()
                self.state.nested_parse(result, 0, section)
                final_nodes.insert(0, section)

        else:
            # Title

            section = nodes.section(
                '',
                nodes.title(text=name),
                ids=[nodes.make_id(ctx.command_path)],
                names=[nodes.fully_normalize_name(ctx.command_path)],
            )

            sphinx_nodes.nested_parse_with_titles(self.state, result, section)

            for node in subcommand_nodes:
                section.append(node)
            final_nodes = [section]

        self._post_process(command, final_nodes)

        return final_nodes

    def _post_process(
        self,
        command: click.Command,
        nodes: ty.List[nodes.Element],
    ) -> None:
        """Runs the post-processor, if any, for the given command and nodes.

        If a post-processor for the created nodes was set via the
        :post-process: option, every set of nodes generated by the directive is
        run through the post-processor.

        This allows for per-command customization of the output.
        """
        if self.postprocessor:
            self.postprocessor(command, nodes)

    def run(self) -> ty.Sequence[nodes.Element]:
        self.env = self.state.document.settings.env

        command = self._load_module(self.arguments[0])

        if not isinstance(command, (click.Command, click.Group)):
            raise self.error(
                '"{}" of type "{}" is not click.Command or click.Group.'
                '"click.BaseCommand"'.format(type(command), self.arguments[0])
            )

        if 'prog' not in self.options:
            raise self.error(':prog: must be specified')

        prog_name = self.options['prog']
        show_nested = 'show-nested' in self.options
        nested = self.options.get('nested')
        hide_header = 'hide-header' in self.options

        self.postprocessor = None
        if 'post-process' in self.options:
            postprocessor_module_path = self.options['post-process']
            self.postprocessor = self._load_module(postprocessor_module_path)

        if show_nested:
            if nested:
                raise self.error(
                    "':nested:' and ':show-nested:' are mutually exclusive"
                )
            else:
                warnings.warn(
                    "':show-nested:' is deprecated; use ':nested: full'",
                    DeprecationWarning,
                )
                nested = NESTED_FULL if show_nested else NESTED_SHORT

        commands = None
        if self.options.get('commands'):
            commands = [
                command.strip() for command in self.options['commands'].split(',')
            ]

        return self._generate_nodes(
            prog_name, command, None, nested, commands, False, hide_header
        )


def setup(app: application.Sphinx) -> ty.Dict[str, ty.Any]:
    # Need autodoc to support mocking modules
    app.setup_extension('sphinx.ext.autodoc')
    app.add_directive('click', ClickDirective)

    app.add_event("sphinx-click-process-description")
    app.add_event("sphinx-click-process-usage")
    app.add_event("sphinx-click-process-options")
    app.add_event("sphinx-click-process-arguments")
    app.add_event("sphinx-click-process-envvars")
    app.add_event("sphinx-click-process-epilog")
    app.add_config_value(
        'sphinx_click_mock_imports', lambda config: config.autodoc_mock_imports, 'env'
    )

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
