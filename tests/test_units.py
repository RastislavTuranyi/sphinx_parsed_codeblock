import pytest

from sphinx_parsed_codeblock import sphinx_parsed_codeblock as spc


class MockVisitor:
    def __init__(self, body: list[str]):
        self.body = body


class MockNode:
    def __init__(self, contents: list[str]):
        self.contents = contents

    def walkabout(self, visitor: MockVisitor):
        visitor.body.extend(self.contents)


@pytest.mark.parametrize('node,expected',
                         ((['this', 'is', 'a', 'sentence'], 'thisisasentence'),
                          ([], ''),
                          (['one'], 'one')))
def test_build_child_source(node, expected):
    node = MockNode(node)
    visitor = MockVisitor(['some', 'preexisting', 'data'])

    result = spc.build_child_source(visitor, node)

    assert result == expected


@pytest.mark.parametrize(
    'source,expected',
    (
        ('<span>value</span>', ('', '')),
        ('<a><span>value</span></a>', ('<a>', '</a>')),
        ('<a><span>value</span><span>value</span><span>value</span></a>', ('<a>', '</a>')),
        ('<a><b><p><span>value</span></p></b></a>', ('<a><b><p>', '</p></b></a>')),
        ('<a><span class="class span text" id="">value</span></a>', ('<a>', '</a>')),
        ('<a id="id"><span class="class span text" id="">value</span></a>', ('<a id="id">', '</a>')),
        ('', ('', '')),
        ('text', ('', '')),
        ('<a>aon <b>v</b> oia</a>', ('', ''))
    )
)
def test_parse_complex_sphinx_source(source, expected):
    result = spc.parse_complex_sphinx_source(source, [])
    assert result == expected
