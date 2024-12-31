Sphinx Parsed Code-Block
========================


.. parsed-code-block:: yaml

    test:
        strings:
            string: "string"
            emphasised_string: *"string"*
            bold_string: **"string"**
            literal_string: ``"string"``
            link: :ref:`"string"<link>`
        numbers:
            number: 1
            emphasised_number: *17537543*
            bold_number: **0.459**
            literal_number: ``-95.4``
            link: :ref:`0<link>`
        lists:
            list: [1, 2, 3, 4, 5]
            emphasised_list: *[1, 2, 3, 4, 5]*
            bold_list: **[1, 2, 3, 4, 5]**
            literal_list: ``[1, 2, 3, 4, 5]``
            link: :ref:`[1, 2, 3, 4, 5]<link>`
        bools:
            bool: true
            emphasised_bool: *false*
            bold_bool: **false**
            literal_bool: ``true``
            link: :ref:`true<link>`
        null:
            none: null
            emphasised_none: *null*
            bold_none: **null**
            literal_none: ``null``
            link: :ref:`null<link>`
        key_and_value_highlighted:
            `string: "string"`
            *emphasised_number: 17537543*
            **bold_number: [1, 2, 3, 4, 5]**
            ``literal_string: true``
            :ref:`link: null<link>`


.. parsed-code-block:: yaml
    :linenos:
    :lineno-start: 1
    :emphasize-lines: 1,13,22

    test:
        strings:
            string: "string"
            emphasised_string: *"string"*
            bold_string: **"string"**
            literal_string: ``"string"``
            link: :ref:`"string"<link>`
        numbers:
            number: 1
            emphasised_number: *17537543*
            bold_number: **0.459**
            literal_number: ``-95.4``
            link: :ref:`0<link>`
        lists:
            list: [1, 2, 3, 4, 5]
            emphasised_list: *[1, 2, 3, 4, 5]*
            bold_list: **[1, 2, 3, 4, 5]**
            literal_list: ``[1, 2, 3, 4, 5]``
            link: :ref:`[1, 2, 3, 4, 5]<link>`
        bools:
            bool: true
            emphasised_bool: *false*
            bold_bool: **false**
            literal_bool: ``true``
            link: :ref:`true<link>`
        null:
            none: null
            emphasised_none: *null*
            bold_none: **null**
            literal_none: ``null``
            link: :ref:`null<link>`
        key_and_value_highlighted:
            `string: "string"`
            *emphasised_number: 17537543*
            **bold_number: [1, 2, 3, 4, 5]**
            ``literal_string: true``
            :ref:`link: null<link>`


.. parsed-code-block:: yaml
    :linenos:
    :lineno-start: 5
    :emphasize-lines: 4,13
    :caption: test
    :name: test-code-block

    test:
        strings:
            string: "string"
            emphasised_string: *"string"*
            bold_string: **"string"**
            literal_string: ``"string"``
            link: :ref:`"string"<link>`
        numbers:
            number: 1
            emphasised_number: *17537543*
            bold_number: **0.459**
            literal_number: ``-95.4``
            link: :ref:`0<link>`
        lists:
            list: [1, 2, 3, 4, 5]
            emphasised_list: *[1, 2, 3, 4, 5]*
            bold_list: **[1, 2, 3, 4, 5]**
            literal_list: ``[1, 2, 3, 4, 5]``
            link: :ref:`[1, 2, 3, 4, 5]<link>`
        bools:
            bool: true
            emphasised_bool: *false*
            bold_bool: **false**
            literal_bool: ``true``
            link: :ref:`true<link>`
        null:
            none: null
            emphasised_none: *null*
            bold_none: **null**
            literal_none: ``null``
            link: :ref:`null<link>`
        key_and_value_highlighted:
            `string: "string"`
            *emphasised_number: 17537543*
            **bold_number: [1, 2, 3, 4, 5]**
            ``literal_string: true``
            :ref:`link: null<link>`


ENDOFFILE!!!!!!!!!!!!!!!!!


.. _link:

Link Target
-----------

The above heading can be linked to.
