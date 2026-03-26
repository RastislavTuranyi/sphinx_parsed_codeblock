import pytest

from docutils.nodes import Text, emphasis, strong, literal, reference
from pygments.formatters.html import escape_html
from sphinx_parsed_codeblock import sphinx_parsed_codeblock as spc


class MockVisitor:
    def __init__(self, body: list[str]):
        self.body = body


class MockNode:
    def __init__(self, contents: list[str]):
        self.contents = contents

    def walkabout(self, visitor: MockVisitor):
        visitor.body.extend(self.contents)


class MockParent:
    def __init__(self, children: list):
        self.children = children


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


@pytest.mark.parametrize(
    'children,expected_text,expected_markup',
    (
        ([], [], []),
        ([Text('')], [''], [None]),
        ([Text('text')], ['text'], [None]),
        ([Text('text&text')], [escape_html('text&text')], [None]),
        ([Text('text  te\tmore text')], ['text  te\tmore text'], [None]),
        ([Text('text\nline2')], ['text', 'line2'], [None, None]),
        ([Text('text\n   line2')], ['text', '   line2'], [None, None]),
        ([Text('text\n\n\nline2')], ['text', '', '', 'line2'], [None, None, None, None]),
        (
            [Text('text\nline2'), Text(''), Text('   ')],
            ['text', 'line2', '', '   '], [None, None, None, None]
        ),
        ([emphasis('**', '')], [''], [0]),
        ([emphasis('*value*', 'value')], ['value'], [0]),
        ([emphasis('*value&value*', 'value&value')], [escape_html('value&value')], [0]),
        (
            [emphasis('*text  te\tmore text*', 'text  te\tmore text')],
            ['text  te\tmore text'],
            [0]
        ),
        (
            [emphasis('*value*', 'value'), emphasis('*d d*', 'd d'), emphasis('*gg*', 'gg')],
            ['value', 'd d', 'gg'],
            [0, 1, 2]
        ),
        ([strong('**value**', 'value')], ['value'], [0]),
        ([literal('``value``', 'value')], ['value'], [0]),
        ([reference('`value`', 'value')], ['value'], [0]),
        (
            [Text('text\nline2'), strong('**value**', 'value'), Text('   ')],
            ['text', 'line2', 'value', '   '],
            [None, None, 1, None]
        ),
        (
            [strong('**value**', 'value'), Text('text\nline2'), Text('   '), reference('`value`', 'value')],
            ['value', 'text', 'line2', '   ', 'value'],
            [0, None, None, None, 3]
        ),
    )
)
def test_split_parsed_codeblock(children, expected_text, expected_markup: list):
    parent = MockParent(children)
    generator = spc.split_parsed_codeblock(parent)
    text, markup = [], []

    for i, exp in enumerate(expected_markup):
        t, m = next(generator)
        text.append(t)
        markup.append(m)

        if isinstance(exp, int):
            expected_markup[i] = children[exp]

    with pytest.raises(StopIteration):
        next(generator)

    assert text == expected_text
    assert markup == expected_markup
