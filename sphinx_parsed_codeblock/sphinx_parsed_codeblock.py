from __future__ import annotations

from copy import deepcopy
import re
from typing import Generator, IO, TYPE_CHECKING

from docutils import nodes
from docutils.nodes import literal_block

from pygments.formatters.html import escape_html, HtmlFormatter

from sphinx.directives.code import CodeBlock, container_wrapper
from sphinx.util import logging


if TYPE_CHECKING:
    from sphinx.builders.html import HTML5Translator
    from sphinx.application import Sphinx


LOGGER = logging.getLogger(__name__)


def split_parsed_codeblock(
    node: parsed_code_block
) -> Generator[tuple[str, str | nodes.Node], None, None]:
    """
    Creates a generator that yields lines and elements from a parsed code block Sphinx node.

    In other words, it loops over the contents of a parsed code block Sphinx node (``node``). If it
    encounters text, it splits it into lines, otherwise it yields the markup element.

    Parameters
    ----------
    node
        The `parsed_code_block` node that is being highlighted.

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
            yield escape_html(child.astext()), child


class PygmentsLineState:
    """
    Class for storing the current state of a Pygments line, used in :py:class:`MarkupHtmlFormatter`.

    Given one line of text formatted by Pygments HTML formatter, this line is split into each
    individual ``<span></span>`` element - these can be iterated over to yield consecutive elements.

    Parameters
    ----------
    line
        One line of text formatted by Pygments HTML formatter.

    Attributes
    ----------
    html_span
        The opening `<span>` element and any other opening HTML tags.
    text
        The text contained in within the span tags.
    """
    def __init__(self, line: str):
        self._span_iterator = re.finditer(r'(<span.*?>)(.*?)</span>', line)
        self.__next__()

    def __iter__(self):
        return self

    def __next__(self) -> tuple[str, str]:
        self.html_span, self.text = next(self._span_iterator).groups()
        return self.html_span, self.text

    def __str__(self):
        return f'PygmentsLineState(html_span="{self.html_span}", text="{self.text}")'

    def cut(self, n: int) -> None:
        """
        Alters the current state by cutting the first ``n`` elements of the text. Also deletes the
        span.

        Parameters
        ----------
        n
            The number of characters to cut.
        """
        self.html_span = ''
        self.text = self.text[n:]

    def restore_span(self) -> str:
        """Reconstructs the current span."""
        return self.html_span + self.text + r'</span>'


class MarkupHtmlFormatter(HtmlFormatter):
    """
    Pygments HTML formatter that is aware of Sphinx.

    A custom HTML formatter for pygments that is aware of the sphinx node it is formatting and its
    corresponding sphinx HTML formatter.

    Parameters
    ----------
    node
        The sphinx node being formatted. This node should contain children nodes that carry the
        markup information.
    visitor
        The sphinx HTML formatter used for creating the sphinx HTML output.
    **options
        Pygments `pygments.formatters.html.HtmlFormatter` options.
    """
    def __init__(self,
                 node: parsed_code_block,
                 visitor: HTML5Translator,
                 **options):
        super().__init__(**options)

        self.sphinx_generator = split_parsed_codeblock(node)
        self.visitor = visitor

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

    def _handle_text_line(self,
                          sphinx_text: str,
                          pygments_state: PygmentsLineState,
                          new_line: list[str]) -> list[str] | None:
        """
        Handles plain (not formatted) sphinx text in the process of resolving sphinx and pygments.

        Given a plain ``sphinx_text``, advances the ``pygments_state``, saving the HTML, until one
        of:

        1. ``sphinx_text`` has run out -> continue onto the next line in parent function
        2. ``pygments_state`` has run out -> end of the pygments line, return upwards
        3. Pygments text is longer than the sphinx text -> get more sphinx text in parent function

        Parameters
        ----------
        sphinx_text
            The current line of sphinx text, not formatted.
        pygments_state
            The current state of the Pygments HTML-formatted line
        new_line
            The result list of strings for this line - this list will be appended to.

        Returns
        -------
        result
            ``None`` if an error occurred, otherwise ``new_line`` with the new text.

        Raises
        ------
        StopIteration
            If ``pygments_state`` has run out of elements, reaching the end of the line.
        """
        while True:
            if not sphinx_text:
                break

            if sphinx_text.startswith(pygments_state.text):
                sphinx_text = sphinx_text[len(pygments_state.text):]
                new_line.append(pygments_state.restore_span())
                next(pygments_state)
                continue

            # Handles markup in the middle of a word
            if pygments_state.text.startswith(sphinx_text):
                new_line.append(pygments_state.html_span + sphinx_text)
                pygments_state.cut(len(sphinx_text))
                break
            else:
                LOGGER.warning('sphinx-parsed-codeblock: '
                               'Could not resolve markup and syntax highlighting; this '
                               'will probably cause much of the markup from a code-block '
                               'to be removed (this is likely a bug)')
                return None
        return new_line

    def _handle_markup_over_multiple_elements(self,
                                              sphinx_text: str,
                                              sphinx_markup: str,
                                              pygments_state: PygmentsLineState,
                                              new_line: list[str]
                                              ) -> bool | None:
        """
        Handles formatted sphinx text that extends over multiple Pygments-formatted elements.

        I.e., when Pygments splits text into multiple separate spans for its formatting, but sphinx
        formatting is applied over all that text, this function will handle that case by applying
        the sphinx formatting for all pygments elements.

        Parameters
        ----------
        sphinx_text
            The plain text contained within formatted sphinx element - unformatted version of
            ``sphinx_markup``.
        sphinx_markup
            The HTML-formatted text of a sphinx markup node - ``sphinx_text`` with the formatting.
        pygments_state
            The current state of Pygments HTML formatting, containing the current span + text.
        new_line
            List of strings containing the new line of text - the formatting will be appended to it.

        Returns
        -------
        result
            If everything went ok, ``None``, otherwise ``False``.
        """
        spans, matches = [pygments_state.html_span], [pygments_state.text]
        for span, text in pygments_state:
            spans.append(span)
            matches.append(text)

            if ''.join(matches) == sphinx_text:
                break
        else:
            LOGGER.warning('sphinx-parsed-codeblock: '
                           'Could not resolve markup and syntax highlighting; one line of '
                           'a code-block will be stripped of markup (this is likely a bug)')
            return False

        try:
            start, end = sphinx_markup.split(''.join(matches))
        except ValueError:
            start, end = parse_complex_sphinx_source(sphinx_markup, matches)

        new_line.append(start)
        for span_html_opener, span_contents in zip(spans, matches):
            new_line.append(span_html_opener + span_contents + r'</span>')
        new_line.append(end)

    def _handle_markup(self,
                       sphinx_text: str,
                       sphinx_markup: str,
                       pygments_state: PygmentsLineState,
                       new_line: list[str]
                       ) -> bool | None:
        """
        Handles formatted sphinx text in the process of resolving sphinx and pygments.

        Given a text and its HTML-formatted version, applies the formatting to the HTML-formatted
        text from pygments.

        Parameters
        ----------
        sphinx_text
            The plain text contained within formatted sphinx element - unformatted version of
            ``sphinx_markup``.
        sphinx_markup
            The HTML-formatted text of a sphinx markup node - ``sphinx_text`` with the formatting.
        pygments_state
            The current state of Pygments HTML formatting, containing the current span + text.
        new_line
            List of strings containing the new line of text - the formatting will be appended to it.

        Returns
        -------
        result
            If everything went ok, ``None``. If the text ran out, ``True``. If an error occurred,
            ``False``.
        """
        if pygments_state.text == sphinx_text:
            new_line.append(pygments_state.html_span + sphinx_markup + r'</span>')
            return None

        if pygments_state.text.startswith(sphinx_text):
            new_line.append(pygments_state.html_span + sphinx_markup)
            pygments_state.cut(len(sphinx_text))
            if pygments_state.text:
                return True
            return None

        return self._handle_markup_over_multiple_elements(sphinx_text, sphinx_markup, pygments_state, new_line)

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
        pygments_state = PygmentsLineState(line)

        for sphinx_text, markup in self.sphinx_generator:
            if markup is None:
                try:
                    result = self._handle_text_line(sphinx_text, pygments_state, new_line)
                except StopIteration:
                    new_line.append('\n')
                    return new_line

                if result is None:
                    return line
                continue

            markup = build_child_source(self.visitor, markup)

            result = self._handle_markup(sphinx_text, markup, pygments_state, new_line)
            if result is True:
                continue
            if result is False:
                return line

            try:
                next(pygments_state)
            except StopIteration:
                new_line.append('\n')
                return new_line

    def format_unencoded(self, tokensource: Generator, outfile: IO) -> None:
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
    try:
        source = visitor.body.pop(i)
    except IndexError:
        return ''

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
