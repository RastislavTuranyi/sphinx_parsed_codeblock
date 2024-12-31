# sphinx_parsed_codeblock

Sphinx extension adding a directive for a parsed code-block.

## Intro

Have you ever tried to use markup inside a code-block? For example, to create a link from inside some code?
Disappointingly, there is no such functionality in sphinx - a choice must be made between the markup 
(via the [`parsed-literal`](https://docutils.sourceforge.io/0.4/docs/ref/rst/directives.html#parsed-literal-block)
directive) and the syntax highlighting (via the 
[`code-block`/`sourcecode`/`code`](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-code-block>)
directive). However, with this extension, that is no longer the case! A new directive, `parsed-code-block`, is provided,
which mixes the functionality of both, providing support for markup inside syntax-highlighted code-block.

## Quickstart

The extension can be installed via pip:

```
pip install https://github.com/RastislavTuranyi/sphinx_parsed_codeblock
```

Then, by including the extension in `conf.py`:

```Python
extensions = ['sphinx_parsed_codeblock']
```

the new directive can be used anywhere in the RST documentation:

```rst
.. parsed-code-block:: yaml

    foo:
        italics: *"string"*
        bold: **12345**
        ``literal: null``
        link: :ref:`true<doc-top>`
```

The `parsed-code-block` directive is a subclass of the default `code-block` directive and so can be used with all
the same options and arguments:

```rst
.. parsed-code-block:: yaml
    :linenos:
    :lineno-start: 5
    :emphasize-lines: 2, 4
    :caption: test
    :name: test-code-block

    foo:
        italics: *"string"*
        bold: **12345**
        ``literal: null``
        link: :ref:`true<doc-top>`
```

## Installation

Currently, the package can only be installed via pip and from GitHub, either directly:

```
pip install https://github.com/RastislavTuranyi/sphinx_parsed_codeblock
```

or from a local copy:

```
git clone https://github.com/RastislavTuranyi/sphinx_parsed_codeblock.git
pip install sphinx_parsed_codeblock
```

However, either way, don't forget to include the extension in the `conf.py`:

```python
extensions = ['sphinx_parsed_codeblock']
```

## Functionality

This extension provides one new directive - `parsed-code-block` - which allows for RST markup to be used 
inside a syntax-highlighted code-block. All *inline* markup is supported:

- *italics* (`*italics*`)
- **bold** (`**bold**`)
- `literal` (` ``literal`` `)
- [link](https://github.com/RastislavTuranyi/sphinx_parsed_codeblock) (``:ref:`link` ``)
- etc.

though higher-level RST such as directives will not be parsed.

## Supported Output Formats

- HTML

For all other formats, the `parsed-code-block` is treated the same as `parsed-literal`, so 
output will be produced, but without syntax highlighting.


