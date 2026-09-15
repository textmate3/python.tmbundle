#!/usr/bin/env python3
"""Open pydoc's own documentation server in a browser, starting it if needed.

This used to daemonize with the two fork trick and call pydoc.serve, which
Python removed. Python starts its own server now, so this asks for one in a
new session and gets out of the way.
"""

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

PORT = 9877
URL = "http://localhost:%d/" % PORT
LOG = "/tmp/pydoc_server_%d.log" % PORT


def is_serving():
    try:
        urllib.request.urlopen(URL, timeout=1)
        return True
    except (urllib.error.URLError, OSError):
        return False


def start_server():
    """Run pydoc's server in its own session, so it outlives this command."""
    with open(LOG, "a") as log:
        subprocess.Popen(
            [sys.executable, "-m", "pydoc", "-p", str(PORT)],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )


def wait_for_server(timeout=10.0, interval=0.25):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if is_serving():
            return True
        time.sleep(interval)
    return False


def report():
    return """
<style type="text/css">
h2, dt { padding: 1em 0.3em 0.3em 0.3em; }
h2 { background: #7799ee; }
dl { margin: 0; }
dt { text-align: right; width: 5em; background: #ee77aa; float: left; }
dd { background: #ffc8d8; padding-top: 1em; overflow: hidden; }
dd a { margin-left: 0.5em; }
h2, dd { margin-bottom: 3px; }
</style>

<h2>Pydoc Server</h2>
<dl>
<dt>url</dt><dd><a href="{url}">{url}</a></dd>
<dt>python</dt><dd>{python}</dd>
<dt>log</dt><dd><a href="file://{log}">{log}</a></dd>
</dl>""".format(url=URL, python=sys.executable, log=LOG)


def main():
    if not is_serving():
        start_server()
        if not wait_for_server():
            print("<p>The pydoc server did not start. See <a href='file://%s'>%s</a>.</p>" % (LOG, LOG))
            return 1

    print(report())
    subprocess.run(["open", URL], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
