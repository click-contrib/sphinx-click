import pickle

from docutils import nodes
from sphinx import addnodes as sphinx_nodes


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
    #       literal_block:
    #       rubric:
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
    assert isinstance(section[2], nodes.literal_block)

    assert isinstance(section[3], nodes.rubric)
    assert section[3].astext() == 'Commands'
    assert isinstance(section[4], sphinx_nodes.index)
    assert isinstance(section[5], sphinx_nodes.desc)
    assert isinstance(section[6], sphinx_nodes.index)
    assert isinstance(section[7], sphinx_nodes.desc)
