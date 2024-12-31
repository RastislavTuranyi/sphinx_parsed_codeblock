from __future__ import annotations

from copy import deepcopy
import re
from typing import TYPE_CHECKING
import warnings

from docutils import nodes
from docutils.nodes import literal_block

from pygments.formatters.html import escape_html, HtmlFormatter

from sphinx.directives.code import CodeBlock, container_wrapper


if TYPE_CHECKING:
    from sphinx.builders.html import HTML5Translator


class MarkupHtmlFormatter(HtmlFormatter):
    def __init__(self, node: parsed_code_block, visitor: HTML5Translator, **options):
        super().__init__(**options)

        self.sphinx_generator = self._get_sphinx(node, visitor)

    def _get_sphinx(self, node, visitor):
        for child in node.children:
            if isinstance(child, nodes.Text):
                for line in child.astext().split('\n'):
                    yield escape_html(line), None
            else:
                yield escape_html(child.astext()), build_child_source(visitor, child)

    def _insert_markup(self, tokensource):
        for t, line in tokensource:
            try:
                yield t, ''.join(self._handle_one_line(line))
            except nodes.SkipNode:
                yield t, line

    def _handle_one_line(self, line):
        new_line = []
        span_iterator = re.finditer(r'(<span.*?>)(.*?)</span>', line)
        span, match = next(span_iterator).groups()
        for text, markup in self.sphinx_generator:
            if markup is None:
                while True:
                    if not text:
                        break

                    if match == text[:len(match)]:
                        text = text[len(match):]
                        new_line.append(span + match + r'</span>')

                        try:
                            span, match = next(span_iterator).groups()
                        except StopIteration:
                            new_line.append('\n')
                            return new_line
                    else:
                        raise Exception()

                continue

            if match == text:
                new_line.append(span + markup + r'</span>')
            else:
                spans, matches = [span], [match]
                for result in span_iterator:
                    spans.append(result.groups()[0])
                    matches.append(result.groups()[1])

                    if ''.join(matches) == text:
                        break
                else:
                    warnings.warn('Could not parse HTML; this is likely a bug', Warning)
                    raise nodes.SkipNode

                try:
                    start, end = markup.split(''.join(matches))
                except ValueError:
                    start, end = parse_complex_sphinx_source(markup, matches)

                new_line.append(start)
                for span, match in zip(spans, matches):
                    new_line.append(span + match + r'</span>')
                new_line.append(end)

            try:
                span, match = next(span_iterator).groups()
            except StopIteration:
                new_line.append('\n')
                return new_line

    def format_unencoded(self, tokensource, outfile):
        source = self._format_lines(tokensource)
        source = self._insert_markup(source)

        # As a special case, we wrap line numbers before line highlighting
        # so the line numbers get wrapped in the highlighting tag.
        if not self.nowrap and self.linenos == 2:
            source = self._wrap_inlinelinenos(source)

        if self.hl_lines:
            source = self._highlight_lines(source)

        if not self.nowrap:
            if self.lineanchors:
                source = self._wrap_lineanchors(source)
            if self.linespans:
                source = self._wrap_linespans(source)
            source = self.wrap(source)
            if self.linenos == 1:
                source = self._wrap_tablelinenos(source)
            source = self._wrap_div(source)
            if self.full:
                source = self._wrap_full(source, outfile)

        for t, piece in source:
            outfile.write(piece)


def parse_complex_sphinx_source(source: str, matches: list[str]) -> tuple[str, str]:
    try:
        result = next(re.finditer(r'<span.*</span>', source))
        return source[:result.start()], source[result.end():]
    except StopIteration:
        warnings.warn(f'Sphinx HTML render of the "{"".join(matches)}" line could not be interpreted; markup ignored.')
        return '', ''


class parsed_code_block(literal_block):
    def protect_children(self):
        """
        Creates a deep copy of children in a new, otherwise unused variable.

        This is necessary for the children not to get deleted by sphinx/docutils when `parsed_code_block` is wrapped in
        `docutils.nodes.container` when the ``caption`` is set.

        The copy is not actually used, but its mere presence fixes the issue.
        """
        self._protected_children = deepcopy(self.children)


def build_child_source(visitor, child: nodes.Node) -> str:
    i = len(visitor.body)
    child.walkabout(visitor)
    source = visitor.body.pop(i)

    for j in range(i+1, len(visitor.body)+1):
        source += visitor.body.pop(i)

    return source


def visit_parsed_code_block(self: HTML5Translator, node: parsed_code_block) -> None:
    lang = node.get('language', 'default')
    linenos = node.get('linenos', False)
    highlight_args = node.get('highlight_args', {})
    highlight_args['force'] = node.get('force', False)
    opts = self.config.highlight_options.get(lang, {})

    if linenos and self.config.html_codeblock_linenos_style:
        linenos = self.config.html_codeblock_linenos_style

    og_formatter = self.highlighter.formatter
    self.highlighter.formatter = MarkupHtmlFormatter

    highlight_args['node'] = node
    highlight_args['visitor'] = self

    highlighted = self.highlighter.highlight_block(
        node.astext(),
        lang,
        opts=opts,
        linenos=linenos,
        location=node,
        **highlight_args,
    )

    self.highlighter.formatter = og_formatter

    starttag = self.starttag(
        node, 'div', suffix='', CLASS='highlight-%s notranslate' % lang
    )

    self.body.append(starttag + highlighted + '</div>\n')
    raise nodes.SkipNode


def depart_parsed_code_block(self, node: parsed_code_block) -> None:
    pass


class ParsedCodeBlock(CodeBlock):
    def run(self) -> list[nodes.Node]:
        text_nodes, messages = self.state.inline_text('\n'.join(self.content), self.lineno)
        node = super().run()[0]

        caption = self.options.get('caption')
        if caption:
            for child in node.children:
                if not isinstance(child, nodes.caption):
                    node = child
                    break
            else:
                warnings.warn('parsed-code-block could not be created because of an issue with the '
                              'caption; defaulting to the parsed-literal behaviour (this may be a '
                              'bug)', Warning)
                return [node]

        custom_node = parsed_code_block('', '')
        custom_node.__dict__ = node.__dict__
        custom_node.children = []
        custom_node.extend(text_nodes)

        if caption:
            custom_node.protect_children()
            custom_node = container_wrapper(self, custom_node, caption)

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
