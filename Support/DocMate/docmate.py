"""Find documentation for a word, locally through pydoc and online at python.org.

This used to carry a 536 KB pickle mapping names to `docs.python.org/lib/*.html`
URLs, a layout python.org stopped using after Python 2.5, and it started the
pydoc server by monkey-patching it through the `new` module, which Python
removed. Both jobs are things Python now does itself.
"""

import os
import pydoc
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PORT = 7464
LOCAL_URL = "http://localhost:%d/" % PORT
LOG = "/tmp/textmate_pydoc_%d.log" % PORT

# TM_PYTHONDOCS lets a person point at a local copy of the documentation.
PYTHON_DOCS = os.environ.get("TM_PYTHONDOCS", "https://docs.python.org/3")


def python_version():
    return "%d.%d" % sys.version_info[:2]


def is_serving():
    try:
        urllib.request.urlopen(LOCAL_URL, timeout=1)
        return True
    except (urllib.error.URLError, OSError):
        return False


def launch_pydoc_server():
    """Start pydoc's own server if it is not already up, and answer its URL."""
    if is_serving():
        return LOCAL_URL

    with open(LOG, "a") as log:
        subprocess.Popen(
            [sys.executable, "-m", "pydoc", "-p", str(PORT)],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if is_serving():
            break
        time.sleep(0.25)
    return LOCAL_URL


def pydoc_url():
    return LOCAL_URL, PORT


def library_docs(word):
    """A link into the official documentation for `word`.

    A search rather than a guessed page, since python.org has a search that
    is current by definition and a URL scheme that is not ours to predict.
    """
    if not word:
        return []

    query = urllib.parse.urlencode({"q": word, "check_keywords": "yes", "area": "default"})
    return [("%s in the Python %s documentation" % (word, python_version()),
             "%s/search.html?%s" % (PYTHON_DOCS.rstrip("/"), query))]


def local_docs(word):
    """A link to pydoc's page for `word`, when pydoc can resolve it here."""
    if not word:
        return []

    try:
        target, name = pydoc.resolve(word)
    except (ImportError, pydoc.ErrorDuringImport):
        return []

    return [(pydoc.describe(target), "%s%s.html" % (LOCAL_URL, name))]
