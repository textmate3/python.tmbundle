"""Tests for the bundle's own Python.

Each command's script is pulled out of its property list and run, so what is
tested is what ships rather than a copy of it.

Run from the bundle's directory:

    "$TM_PYTHON" Tests/python_commands_tests.py
"""

import os
import plistlib
import subprocess
import sys
import unittest

BUNDLE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BUNDLE, "Support/DocMate"))

import docmate


def command_script(directory, name):
    with open(os.path.join(BUNDLE, directory, name), "rb") as plist:
        return plistlib.load(plist)["command"]


def run_script(script, environment=None, stdin=""):
    return subprocess.run(
        [sys.executable, "-c", script],
        env={**os.environ, **(environment or {})},
        input=stdin,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


class NewFunction(unittest.TestCase):
    SCRIPT = None

    @classmethod
    def setUpClass(cls):
        cls.SCRIPT = command_script("Commands", "New Function.plist")

    def snippet(self, word):
        return run_script(self.SCRIPT, {"TM_CURRENT_WORD": word})

    def test_a_self_only_special_method_takes_only_self(self):
        self.assertIn("def __repr__(self):", self.snippet("repr"))

    def test_a_binary_operator_takes_other(self):
        self.assertIn("def __eq__(self, other):", self.snippet("eq"))

    def test_a_python_3_only_operator_is_known(self):
        self.assertIn("def __matmul__(self, other):", self.snippet("matmul"))

    def test_an_asynchronous_context_manager_is_known(self):
        self.assertIn("def __aenter__(self):", self.snippet("aenter"))

    def test_a_method_taking_more_than_self_gets_its_arguments(self):
        self.assertIn("def __setitem__(self, key, value):", self.snippet("setitem"))

    def test_an_unknown_name_becomes_an_ordinary_method(self):
        self.assertIn("def helper(", self.snippet("helper"))

    def test_the_docstring_names_the_method_rather_than_saying_percent_s(self):
        snippet = self.snippet("eq")
        self.assertIn("docstring for __eq__", snippet)
        self.assertNotIn("%s", snippet)

    def test_a_method_python_3_dropped_is_no_longer_offered_as_a_special_one(self):
        # __nonzero__ became __bool__, so asking for it makes a plain method.
        self.assertIn("def nonzero(", self.snippet("nonzero"))


class Super(unittest.TestCase):
    SCRIPT = None

    @classmethod
    def setUpClass(cls):
        cls.SCRIPT = command_script("Commands", "super.tmCommand")

    def snippet(self, source, line, column):
        return run_script(
            self.SCRIPT,
            {"TM_LINE_NUMBER": str(line), "TM_LINE_INDEX": str(column)},
            stdin=source,
        ).strip()

    def test_it_writes_the_zero_argument_form_python_3_asks_for(self):
        source = "class Duck(Bird):\n    def __init__(self):\n        \n"
        snippet = self.snippet(source, 3, 8)
        self.assertTrue(snippet.startswith("super()."), snippet)
        self.assertNotIn("Duck, self", snippet)

    def test_it_names_the_method_the_caret_is_in(self):
        source = "class Duck(Bird):\n    def fly(self):\n        \n"
        self.assertIn("${1:fly}", self.snippet(source, 3, 8))

    def test_positional_arguments_become_tab_stops_without_self(self):
        source = "class Duck(Bird):\n    def fly(self, height, speed):\n        \n"
        snippet = self.snippet(source, 3, 8)
        self.assertIn("${2:height}", snippet)
        self.assertIn("${3:speed}", snippet)
        self.assertNotIn("self}", snippet)

    def test_star_args_and_keyword_arguments_are_carried_through(self):
        source = "class Duck(Bird):\n    def fly(self, *rest, fast=False, **options):\n        \n"
        snippet = self.snippet(source, 3, 8)
        self.assertIn("*rest", snippet)
        self.assertIn("fast=fast", snippet)
        self.assertIn("**options", snippet)

    def test_an_asynchronous_method_is_found_too(self):
        source = "class Duck(Bird):\n    async def fly(self, height):\n        \n"
        self.assertIn("${1:fly}", self.snippet(source, 3, 8))

    def test_a_file_that_does_not_parse_still_answers_something_useful(self):
        self.assertIn("super()", self.snippet("class Duck(:\n    \n", 2, 4))


class Documentation(unittest.TestCase):
    def test_a_library_link_goes_to_the_current_documentation_over_https(self):
        (description, url), = docmate.library_docs("os.path")
        self.assertTrue(url.startswith("https://docs.python.org/3/search.html"), url)
        self.assertIn("os.path", description)

    def test_a_word_pydoc_can_resolve_gets_a_local_link(self):
        entries = docmate.local_docs("os.path")
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0][1].endswith("os.path.html"))

    def test_a_word_pydoc_cannot_resolve_gets_nothing_rather_than_an_error(self):
        self.assertEqual(docmate.local_docs("no_such_module_anywhere"), [])

    def test_no_word_asks_for_nothing(self):
        self.assertEqual(docmate.library_docs(""), [])
        self.assertEqual(docmate.local_docs(""), [])

    def test_tm_pythondocs_redirects_at_a_local_copy(self):
        saved = os.environ.get("TM_PYTHONDOCS")
        os.environ["TM_PYTHONDOCS"] = "file:///tmp/pydocs"
        try:
            import importlib
            importlib.reload(docmate)
            (_, url), = docmate.library_docs("os")
            self.assertTrue(url.startswith("file:///tmp/pydocs/search.html"), url)
        finally:
            if saved is None:
                os.environ.pop("TM_PYTHONDOCS", None)
            else:
                os.environ["TM_PYTHONDOCS"] = saved
            importlib.reload(docmate)


class Templates(unittest.TestCase):
    NAMES = [
        "Python Script/template.py",
        "Python Script with Args/template.py",
        "Python Class/template.py",
        "Python Unittest/template.py",
    ]

    def test_every_template_compiles_once_its_placeholders_are_filled_in(self):
        for name in self.NAMES:
            with self.subTest(template=name):
                with open(os.path.join(BUNDLE, "Templates", name)) as handle:
                    source = handle.read().replace("${TM_NEW_FILE_BASENAME}", "Placeholder")
                compile(source, name, "exec")

    def test_every_template_asks_for_a_python_that_exists(self):
        for name in self.NAMES:
            with self.subTest(template=name):
                with open(os.path.join(BUNDLE, "Templates", name)) as handle:
                    first_line = handle.readline().strip()
                self.assertEqual(first_line, "#!/usr/bin/env python3")


if __name__ == "__main__":
    unittest.main(verbosity=2)
