How it Works
============

This page provides a brief overview of how this extension works:

Sphinx directive
----------------

This part is very simple: :class:`sphinx_parsed_codeblock.sphinx_parsed_codeblock.ParsedCodeBlock` is a subclass of the
sphinx's own code-block implementation, :class:`sphinx.directives.code.CodeBlock`. Therefore, ``ParsedCodeBlock`` simply runs
the sphinx implementation and so inherits all the options and capabilities. All it does afterwards is that it replaces
the node that ``CodeBlock`` returns (:class:`docutils.nodes.literal_block`) with a custom node,
:class:`sphinx_parsed_codeblock.sphinx_parsed_codeblock.parsed_code_block` (which itself is a subclass of ``literal_block``).
Then, it runs the sphinx/docutils inline parser to parse the contents for inline markup, and assigns the nodes returned
as children for the ``parsed_code_block``.

Writing HTML
------------

This is the main part of the extension, as it is necessary to resolve the different HTML coming from sphinx and from
pygments. This is done by implementing a custom subclass of :class:`pygments.formatters.html.HtmlFormatter`,
:class:`sphinx_parsed_codeblock.sphinx_parsed_codeblock.MarkupHtmlFormatter`. This class inserts a custom step into the
formatting process, where after pygments formats one line of the code, the new step takes it apart and figures out where
the sphinx formatting should go within that line. It then combines the HTML formatting from sphinx and the HTML
formatting from pygments.