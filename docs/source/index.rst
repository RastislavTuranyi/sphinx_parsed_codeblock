.. _doc-top:

Sphinx Parsed Code-Block
========================

A `Sphinx <https://www.sphinx-doc.org/en/master/index.html>`_ extension that provides a parsed code-block directive.

This extension has exactly one functionality: to provide a new directive that combines the ``parsed-literal`` and
``code-block`` directives. This is done via the new ``parsed-code-block`` directive, which can be used the same way as the
Sphinx `code-block/sourcecode/code <https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-code-block>`_
directive::

    .. parsed-code-block:: yaml

        foo:
            bar: baz

``parsed-code-block`` is actually a subclass of the ``code-block`` directive, and so has the same arguments and options
(please see the
`Sphinx documentation <https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-code-block>`_
for details). However, ``parsed-code-block`` has the ``parsed-literal`` functionality on top, meaning that the contents
of the ``parsed-code-block`` are first parsed for inline RST markup, which is then added on top of the
synthax-highlighted contents. This, in effect, means that inline markup can be used together with the syntax highlighting::

    .. parsed-code-block:: yaml

        foo:
            italics: *"string"*
            bold: **12345**
            ``literal: null``
            link: :ref:`true<doc-top>`

yields:

.. parsed-code-block:: yaml

    foo:
        italics: *"string"*
        bold: **12345**
        ``literal: null``
        link: :ref:`true<doc-top>`


.. warning::

    Since the contents of the ``parsed-code-block`` directive are parsed for inline markup, markup symbols that are
    desired to be used as-is, e.g. so that the ``*`` symbol shows up as ``*`` without being parsed, they **must** be
    escaped. See the
    `parsed-literal documentation <https://docutils.sourceforge.io/0.4/docs/ref/rst/directives.html#parsed-literal-block>`_
    for more information.


.. warning::

    Only *inline* markup is parsed (i.e. markup and roles); any directives will **not** be parsed and will be passed to
    the syntax-highlighter as-is.


.. important::

    This extension does not perform *any* CSS manipulation; all markup is applied as-is on top of the syntax-highlighted
    contents. This means that some combinations of markup and highlighted syntax may result in undesirable appearances.
    See :doc:`examples` for examples of this behaviour.


Supported Output Formats
------------------------

* HTML

For any other formats, the ``parsed-code-block`` directive will behave as the ``parsed-literal`` directive, meaning that
an output will be created, but with the syntax highlighting turned off.


More Information
----------------

.. toctree::
    :maxdepth: 1

    examples


