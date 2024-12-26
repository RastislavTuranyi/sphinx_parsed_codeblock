from __future__ import annotations

import re
import warnings

from docutils import nodes
from docutils.nodes import literal_block

from pygments.formatters.html import escape_html

from sphinx.directives.code import CodeBlock


def get_next(iterator, end=True) -> tuple[str, str, int]:
    result = next(iterator)
    span, match = result.groups()

    if end:
        pos = result.end()
    else:
        pos = result.start()

    return span, match, pos


def parse_complex_sphinx_source(source: str, matches: list[str]) -> tuple[str, str]:
    try:
        result = next(re.finditer(r'<span.*</span>', source))
        return source[:result.start()], source[result.end():]
    except StopIteration:
        warnings.warn(f'Sphinx HTML render of the "{"".join(matches)}" line could not be interpreted; markup ignored.')
        return '', ''


class parsed_code_block(literal_block):
    pass


def build_child_source(visitor, child: nodes.Node) -> str:
    i = len(visitor.body)
    child.walkabout(visitor)
    source = visitor.body.pop(i)

    for j in range(i+1, len(visitor.body)+1):
        source += visitor.body.pop(i)

    return source


def visit_parsed_code_block(self, node: parsed_code_block) -> None:
    lang = node.get('language', 'default')
    linenos = node.get('linenos', False)
    highlight_args = node.get('highlight_args', {})
    highlight_args['force'] = node.get('force', False)
    opts = self.config.highlight_options.get(lang, {})

    if linenos and self.config.html_codeblock_linenos_style:
        linenos = self.config.html_codeblock_linenos_style

    highlighted = self.highlighter.highlight_block(
        node.astext(),
        lang,
        opts=opts,
        linenos=linenos,
        location=node,
        **highlight_args,
    )

    starttag = self.starttag(
        node, 'div', suffix='', CLASS='highlight-%s notranslate' % lang
    )

    if not node.children:
        self.body.append(starttag + highlighted + '</div>\n')
        raise nodes.SkipNode

    span_iterator = re.finditer(r'(<span.*?>)(.*?)</span>', highlighted)

    span, match, regex_start = get_next(span_iterator, end=False)

    new_text = []
    try:
        for child in node.children:
            if isinstance(child, nodes.Text):
                text = escape_html(child.astext())

                while True:
                    if not text:
                        break

                    if match == text[:len(match)]:
                        text = text[len(match):]
                        new_text.append(span + match + r'</span>')
                        span, match, regex_end = get_next(span_iterator)
                    elif text[0] == '\n':
                        text = text[1:]
                        new_text.append('\n')
                    else:
                        break

                continue

            contents = escape_html(child.astext())
            if match == contents:
                new_text.append(span + build_child_source(self, child) + r'</span>')
                span, match, regex_end = get_next(span_iterator)
            else:
                spans, matches = [span], [match]
                for result in span_iterator:
                    spans.append(result.groups()[0])
                    matches.append(result.groups()[1])
                    regex_end = result.end()

                    if ''.join(matches) == contents:
                        break
                else:
                    self.body.append(starttag + highlighted + '</div>\n')
                    warnings.warn('Could not parse HTML; this is likely a bug', Warning)
                    raise nodes.SkipNode

                source = build_child_source(self, child)
                try:
                    start, end = source.split(''.join(matches))
                except ValueError:
                    start, end = parse_complex_sphinx_source(source, matches)

                new_text.append(start)
                for span, match in zip(spans, matches):
                    new_text.append(span + match + r'</span>')
                new_text.append(end)

                span, match, regex_end = get_next(span_iterator)
    except StopIteration:
        pass

    start = highlighted[:regex_start]
    end = highlighted[regex_end:]

    self.body.append(starttag + start + ''.join(new_text) + end + '</div>\n')
    raise nodes.SkipNode


def depart_parsed_code_block(self, node: parsed_code_block) -> None:
    pass


class ParsedCodeBlock(CodeBlock):
    def run(self) -> list[nodes.Node]:
        text_nodes, messages = self.state.inline_text('\n'.join(self.content), self.lineno)
        node = super().run()[0]

        custom_node = parsed_code_block('', '')
        custom_node.__dict__ = node.__dict__

        custom_node.children = []
        custom_node.extend(text_nodes)

        # self.add_name(custom_node)

        return [custom_node]


def setup(app):
    app.add_directive('parsed-code-block', ParsedCodeBlock)

    app.add_node(parsed_code_block,
                 html=(visit_parsed_code_block, depart_parsed_code_block))

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
