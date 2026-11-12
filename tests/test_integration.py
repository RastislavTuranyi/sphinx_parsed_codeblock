from packaging.version import Version
from pathlib import Path
import pytest

from pygments import __version__ as pygments_version

try:
    from sphinx.testing.path import path

    @pytest.fixture(scope='session')
    def rootdir():
        return path(__file__).parent.abspath() / 'roots'

    SPHINX_PATH = True
except ImportError:
    from pathlib import Path as path

    @pytest.fixture(scope='session')
    def rootdir():
        return path(__file__).parent.absolute() / 'roots'

    SPHINX_PATH = False


pytest_plugins = ('sphinx.testing.fixtures',)


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
            if 'class="headerlink" href="#id1" title="' in line and 'ink to this code">' in line:
                continue
            out.append(line)

    return out


@pytest.mark.sphinx("html", testroot="integration")
def test_integration_html(app, status):
    if SPHINX_PATH:
        root_dir = path(__file__).parent.abspath()
    else:
        root_dir = path(__file__).parent.absolute()

    app.build()
    assert "build succeeded" in status.getvalue()  # Build succeeded

    result = clean_up((Path(app.srcdir) / "_build/html/test.html").read_text())

    if Version(pygments_version) < Version("2.21"):
        expected = clean_up((root_dir / 'roots' / 'test-integration' / "test_old.html")
                            .read_text(encoding='utf-8'))
    else:
        expected = clean_up((root_dir / 'roots' / 'test-integration' / "test_new.html")
                            .read_text(encoding='utf-8'))

    assert expected != []
    assert result == expected
