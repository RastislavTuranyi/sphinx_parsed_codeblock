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


PYGMENTS_LINE_STATE_ITERATIONS_CASES = (
    (r'<span>text</span>', (('<span>', 'text', r'</span>'),)),
    (r'<span>text 82&*(d//span   ddd</span>', (('<span>', 'text 82&*(d//span   ddd', r'</span>'),)),
    (r'<span><b>text</b></span>', (('<span><b>', 'text', '</b></span>'),)),
    (r'<span><b><em>text</em></b></span>', (('<span><b><em>', 'text', '</em></b></span>'),)),
    (r'<span class="a b c ddaj">text</span>', (('<span class="a b c ddaj">', 'text', r'</span>'),)),
    (r'<span>text</span><span>value</span>',
     (('<span>', 'text', r'</span>'), ('<span>', 'value', r'</span>'),)),
    (r'<span class="a">text</span><span><b><em>value</em></b></span>',
     (('<span class="a">', 'text', r'</span>'), ('<span><b><em>', 'value', r'</em></b></span>'),)),
)


@pytest.mark.parametrize('source_str,expected',PYGMENTS_LINE_STATE_ITERATIONS_CASES)
def test_pygments_line_state_dunder(source_str, expected):
    state = spc.PygmentsLineState(source_str)

    assert state.html_span == expected[0][0]
    assert state.text == expected[0][1]
    assert state.html_close == expected[0][2]

    for expected_html, expected_text, expected_close in expected[1:]:
        state.next()
        assert state.html_span == expected_html
        assert state.text == expected_text
        assert state.html_close == expected_close

    with pytest.raises(StopIteration):
        next(state)


@pytest.mark.parametrize('source_str,expected',PYGMENTS_LINE_STATE_ITERATIONS_CASES)
def test_pygments_line_state_iter(source_str, expected):
    state = spc.PygmentsLineState(source_str)

    assert state.html_span == expected[0][0]
    assert state.text == expected[0][1]
    assert state.html_close == expected[0][2]

    i = -1
    for i, (span, text, close) in enumerate(state.iter()):
        expected_html, expected_text, expected_close = expected[i+1]
        assert span == expected_html
        assert state.html_span == expected_html

        assert text == expected_text
        assert state.text == expected_text

        assert close == expected_close
        assert state.html_close == expected_close

    assert i+2 == len(expected)


@pytest.mark.parametrize('source_str,expected',PYGMENTS_LINE_STATE_ITERATIONS_CASES)
def test_pygments_line_state_restore_span(source_str, expected):
    state = spc.PygmentsLineState(source_str)
    assert state.restore_span() == ''.join(expected[0])


@pytest.mark.parametrize(
    'source_str,text,expected',
    (
        (r'<span>text</span>', 'new text', r'<span>new text</span>'),
        (r'<span>text 82&*(d//span   ddd</span>', '777', r'<span>777</span>'),
        (r'<span><b>text</b></span>', '<em>emphasis</em>', r'<span><b><em>emphasis</em></b></span>'),
        (r'<span><b><em>text</em></b></span>', '', r'<span><b><em></em></b></span>'),
    )
)
def test_pygments_line_state_create_span(source_str, text, expected):
    state = spc.PygmentsLineState(source_str)
    assert state.create_span(text) == expected


@pytest.mark.parametrize(
    'source_str,n,expected',
    (
        (r'<span>text</span>', 1, r'ext'),
        (r'<span>text 82&*(d//span   ddd</span>', 5, r'82&*(d//span   ddd'),
        (r'<span><b>text</b></span>', 2, r'xt'),
        (r'<span><b><em>text</em></b></span>', 4, r''),
    )
)
def test_pygments_line_state_cut(source_str, n, expected):
    state = spc.PygmentsLineState(source_str)
    close = state.html_close

    assert state.cut(n) is None
    assert state.html_span == ''
    assert state.text == expected
    assert state.html_close == close

