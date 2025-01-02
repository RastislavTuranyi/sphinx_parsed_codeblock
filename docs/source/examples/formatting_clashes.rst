Formatting Clashes
==================

Links
-----

Simple markup usually works fine, but links can have various circumstances where they are not displayed as might be
expected:

.. code-block:: rst

    .. parsed-code-block:: yaml

        foo:
            :ref:`bar: baz<doc-top>`
            :doc:`source</source>`: "source"

.. parsed-code-block:: yaml

    foo:
        :ref:`bar: baz<doc-top>`
        :doc:`source</source>`: "source"


Doubling up on formatting
-------------------------

If a syntax highlighter applies a formatting, e.g. bolding, then if the same formattting is applied via RST markup, it
might not make any difference, as e.g. the bold letters cannot become any bolder:

.. code-block:: rst

    .. parsed-code-block:: yaml

        foo:
            unbolded: true
            **bolded**: true

.. parsed-code-block:: yaml

    foo:
        unbolded: true
        **bolded**: true

