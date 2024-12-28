from pathlib import Path
import pytest

from sphinx.testing.path import path

pytest_plugins = ('sphinx.testing.fixtures',)


@pytest.fixture(scope='session')
def rootdir():
    return path(__file__).parent.abspath() / 'roots'


def clean_up(text: str) -> list[str]:
    text = text.split('\n')
    out = []
    start, end = False, False

    for i, line in enumerate(text):
        line = line.replace('\n', '').strip()

        if start is False:
            if '<h1>Sphinx Parsed Code-Block' in line:
                start = True
            continue

        if end is False:
            if 'ENDOFFILE!!!!!!!!!!!!!!!!!' in line:
                end = True
                continue
        else:
            continue

        if line:
            out.append(line)

    return out


@pytest.mark.sphinx("html", testroot="integration")
def test_integration_html(app, status):
    root_dir = path(__file__).parent.abspath()

    app.build()
    assert "build succeeded" in status.getvalue()  # Build succeeded

    result = clean_up((Path(app.srcdir) / "_build/html/index.html").read_text())
    expected = clean_up((root_dir / 'roots' / 'test-integration' / "index.html").read_text())

    assert expected != []
    assert result == expected
