from __future__ import annotations

from copy import deepcopy
import re
from typing import Generator, TYPE_CHECKING

from docutils import nodes
from docutils.nodes import literal_block

from pygments.formatters.html import escape_html, HtmlFormatter

from sphinx.directives.code import CodeBlock, container_wrapper
from sphinx.util import logging


if TYPE_CHECKING:
    from sphinx.builders.html import HTML5Translator
    from sphinx.application import Sphinx


LOGGER = logging.getLogger(__name__)


class MarkupHtmlFormatter(HtmlFormatter):
    def __init__(self,
                 node: parsed_code_block,
                 visitor: HTML5Translator,
                 **options):
        super().__init__(**options)

        self.sphinx_generator = self._get_sphinx(node, visitor)

    @staticmethod
    def _get_sphinx(node: parsed_code_block,
                    visitor: HTML5Translator
                    ) -> Generator[tuple[str, str | None], None, None]:
        """
        Creates a generator that yields elements from the sphinx nodes.

        To be precise, it either yields a full line of text (as marked by the \n character, which
        happens if a given sphinx node is a non-markup Text node), or the full contents of a markup
        node.

        Parameters
        ----------
        node
            The `parsed_code_block` node that is being highlighted.
        visitor
            The visitor used in docutils/sphinx for walking through nodes.

        Yields
        ------
        text: str
            The simple text of an element.
        markup: str or None
            The HTML-formatted element.
        """
        for child in node.children:
            if isinstance(child, nodes.Text):
                for line in child.astext().split('\n'):
                    yield escape_html(line), None
            else:
                yield escape_html(child.astext()), build_child_source(visitor, child)

    def _insert_markup(self, tokensource: Generator) -> Generator[tuple[int, str], None, None]:
        """
        Inserts sphinx markup into a highlighted line, yielding the lines.

        Parameters
        ----------
        tokensource
            Generator over syntax-highlighted lines.

        Yields
        ------
        int
            The integer from `tokensource`.
        line: str
            The syntax-highlighted line containing sphinx markup.
        """
        for t, line in tokensource:
            yield t, ''.join(self._handle_one_line(line))

    def _handle_one_line(self, line: str) -> list[str] | str:
        """
        Inserts the sphinx markup into one line of syntax-highlighted code.

        Parameters
        ----------
        line
            A single line of already syntax-highlighted code.

        Returns
        -------
        new_line
            The `line` with the sphinx markup inserted.
        """
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
                        LOGGER.warning('sphinx-parsed-codeblock: '
                                       'Could not resolve markup and syntax highlighting; this '
                                       'will probably cause much of the markup from a code-block '
                                       'to be removed (this is likely a bug)')
                        return line

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
                    LOGGER.warning('sphinx-parsed-codeblock: '
                                   'Could not resolve markup and syntax highlighting; one line of '
                                   'a code-block will be stripped of markup (this is likely a bug)')
                    return line

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
    """
    Attempts to parse sphinx-formatted HTML markup to find the HTML tags responsible.

    Should be used when sphinx does not format a markup element by simply enclosing the text in some
    HTML tags (e.g. ideally ``foo: **bar**`` -> ``foo: <b>bar</b>``), but instead inserts various
    ``span`` elements inside, i.e. ``foo: **[1, 2]**`` ->
    ``foo: <b><span>[1,</span><span> 2]</span></b>``. In the above example, this function attempts
    to find and return the ``<b>`` and ``</b>`` tags.

    Parameters
    ----------
    source
        The sphinx-formatted HTML output, with the markup present in the HTML.
    matches
        The text that is expected inside the tags attempted to be found. Used for logging in case of
        failure.

    Returns
    -------
    start_tag
        The start HTML tag applied by sphinx. Empty string if failed.
    end_tag
        The end HTML tag applied by sphinx. Empty string if failed.
    """
    try:
        result = next(re.finditer(r'<span.*</span>', source))
        return source[:result.start()], source[result.end():]
    except StopIteration:
        LOGGER.warning(f'sphinx-parsed-codeblock: '
                       f'Sphinx HTML render of the "{"".join(matches)}" line could not be '
                       f'interpreted; markup ignored.')
        return '', ''


class parsed_code_block(literal_block):
    """Custom node for the parsed code-block - a subclass of `docutils.nodes.literal_block`"""
    def protect_children(self):
        """
        Creates a deep copy of children in a new, otherwise unused variable.

        This is necessary for the children not to get deleted by sphinx/docutils when `parsed_code_block` is wrapped in
        `docutils.nodes.container` when the ``caption`` is set.

        The copy is not actually used, but its mere presence fixes the issue.
        """
        self._protected_children = deepcopy(self.children)


def build_child_source(visitor: HTML5Translator, child: nodes.Node) -> str:
    """
    Formats a markup element using sphinx and returns the HTML code.

    Parameters
    ----------
    visitor
        The node visitor used for traversing nodes and creating HTML output.
    child
        A child of the `parsed_code_block` node. Should be a child that has a markup.

    Returns
    -------
    source
        The HTML source for the given `child`.
    """
    i = len(visitor.body)
    child.walkabout(visitor)
    source = visitor.body.pop(i)

    for j in range(i+1, len(visitor.body)+1):
        source += visitor.body.pop(i)

    return source


def visit_parsed_code_block(self: HTML5Translator, node: parsed_code_block) -> None:
    """
    Visits the `parsed_code_block` node and creates the HTML output.

    Parameters
    ----------
    self
        The HTML translator.
    node
        The `parsed_code_block` node to create HTML output for
    """
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
    """Empty function; all HTML output for `parsed_code_block` occurs in `visit_parsed_code_block`"""
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
                LOGGER.warning('sphinx-parsed-codeblock: '
                               'parsed-code-block could not be created because of an issue '
                               'with the caption; defaulting to the parsed-literal behaviour (this '
                               'may be a bug)')
                return [node]

        custom_node = parsed_code_block('', '')
        custom_node.__dict__ = node.__dict__
        custom_node.children = []
        custom_node.extend(text_nodes)

        if caption:
            custom_node.protect_children()  # Necessary to work with the container
            custom_node = container_wrapper(self, custom_node, caption)

        return [custom_node]


def setup(app: Sphinx) -> dict[str, str | bool]:
    """The main function - sets up the extension."""
    app.add_directive('parsed-code-block', ParsedCodeBlock)

    app.add_node(parsed_code_block,
                 html=(visit_parsed_code_block, depart_parsed_code_block))

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
