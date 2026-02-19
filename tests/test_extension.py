import pickle

from docutils import nodes
from sphinx import addnodes as sphinx_nodes


def test_mock_import_compatibility():
    """Test that sphinx_click.ext.mock is callable after sphinx.ext.autodoc.mock is imported.

    Regression test for https://github.com/click-contrib/sphinx-click/issues/159

    When sphinx_autodoc_typehints imports `from sphinx.ext.autodoc.mock import mock`,
    it causes Python to bind the submodule as an attribute on sphinx.ext.autodoc,
    which can shadow the re-exported mock function. sphinx_click must import mock
    directly from the submodule to avoid this issue.
    """
    # Simulate sphinx_autodoc_typehints being loaded first
    from sphinx.ext.autodoc.mock import mock  # noqa: F401

    # Now import sphinx_click (as would happen during Sphinx extension loading)
    import sphinx_click.ext

    # Verify the mock function is callable
    with sphinx_click.ext.mock([]):
        pass


def test_basics(make_app, rootdir):
    srcdir = rootdir / 'basics'
    app = make_app('xml', srcdir=srcdir)
    app.build()

    # TODO: rather than using the pickled doctree, we should decode the XML
    content = pickle.loads((app.doctreedir / 'index.doctree').read_bytes())

    # doc has format like so:
    #
    # document:
    #   section:
    #     title:
    #     section:
    #       title:
    #       paragraph:
    #       rubric:  (Usage)
    #       literal_block:
    #       rubric:  (Commands)
    #       index:
    #       desc:
    #         desc_signature:
    #         desc_signature:
    #       index:
    #       desc:
    #         desc_signature:
    #         desc_signature:

    section = content[0][1]
    assert isinstance(section, nodes.section)

    assert isinstance(section[0], nodes.title)
    assert section[0].astext() == 'greet'
    assert isinstance(section[1], nodes.paragraph)
    assert section[1].astext() == 'A sample command group.'
    assert isinstance(section[2], nodes.rubric)
    assert section[2].astext() == 'Usage'
    assert isinstance(section[3], nodes.literal_block)

    assert isinstance(section[4], nodes.rubric)
    assert section[4].astext() == 'Commands'
    assert isinstance(section[5], sphinx_nodes.index)
    assert isinstance(section[6], sphinx_nodes.desc)
    assert section[6].astext() == 'hello\n\nGreet a user.'
    assert isinstance(section[7], sphinx_nodes.index)
    assert isinstance(section[8], sphinx_nodes.desc)
    assert section[8].astext() == 'world\n\nGreet the world.'


def test_commands(make_app, rootdir):
    srcdir = rootdir / 'commands'
    app = make_app('xml', srcdir=srcdir)
    app.build()

    # TODO: rather than using the pickled doctree, we should decode the XML
    content = pickle.loads((app.doctreedir / 'index.doctree').read_bytes())

    # doc has format like so:
    #
    # document:
    #   section:
    #     title:
    #     section:
    #       title:
    #       paragraph:
    #       rubric:  (Usage)
    #       literal_block:
    #       rubric:  (Commands)
    #       index:
    #       desc:
    #         desc_signature:
    #         desc_signature:

    section = content[0][1]
    assert isinstance(section, nodes.section)

    assert isinstance(section[0], nodes.title)
    assert section[0].astext() == 'greet'
    assert isinstance(section[1], nodes.paragraph)
    assert section[1].astext() == 'A sample command group.'
    assert isinstance(section[2], nodes.rubric)
    assert section[2].astext() == 'Usage'
    assert isinstance(section[3], nodes.literal_block)

    # we should only show a single command, 'world'
    assert isinstance(section[4], nodes.rubric)
    assert section[4].astext() == 'Commands'
    assert isinstance(section[5], sphinx_nodes.index)
    assert isinstance(section[6], sphinx_nodes.desc)
    assert section[6].astext() == 'world\n\nGreet the world.'


def test_nested_full(make_app, rootdir):
    srcdir = rootdir / 'nested-full'
    app = make_app('xml', srcdir=srcdir)
    app.build()

    # TODO: rather than using the pickled doctree, we should decode the XML
    content = pickle.loads((app.doctreedir / 'index.doctree').read_bytes())

    # doc has format like so:
    #
    # document:
    #   section:
    #     title:
    #     section:
    #       title:
    #       paragraph:
    #       rubric:  (Usage)
    #       literal_block:
    #       section:
    #         title
    #         paragraph
    #         rubric:  (Usage)
    #         literal_block
    #         ...
    #       section:
    #         title
    #         paragraph
    #         rubric:  (Usage)
    #         literal_block

    section = content[0][1]
    assert isinstance(section, nodes.section)

    assert isinstance(section[0], nodes.title)
    assert section[0].astext() == 'greet'
    assert isinstance(section[1], nodes.paragraph)
    assert section[1].astext() == 'A sample command group.'
    assert isinstance(section[2], nodes.rubric)
    assert section[2].astext() == 'Usage'
    assert isinstance(section[3], nodes.literal_block)

    subsection_a = section[4]
    assert isinstance(subsection_a, nodes.section)

    assert isinstance(subsection_a[0], nodes.title)
    assert subsection_a[0].astext() == 'hello'
    assert isinstance(subsection_a[1], nodes.paragraph)
    assert subsection_a[1].astext() == 'Greet a user.'
    assert isinstance(subsection_a[2], nodes.rubric)
    assert subsection_a[2].astext() == 'Usage'
    assert isinstance(subsection_a[3], nodes.literal_block)
    # we don't need to verify the rest of this: that's done elsewhere

    subsection_b = section[5]
    assert isinstance(subsection_b, nodes.section)

    assert isinstance(subsection_b[0], nodes.title)
    assert subsection_b[0].astext() == 'world'
    assert isinstance(subsection_b[1], nodes.paragraph)
    assert subsection_b[1].astext() == 'Greet the world.'
    assert isinstance(subsection_b[2], nodes.rubric)
    assert subsection_b[2].astext() == 'Usage'
    assert isinstance(subsection_b[3], nodes.literal_block)
