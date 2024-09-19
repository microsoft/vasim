#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
"""Setup instructions for the vasim package."""

import os
import re

from setuptools import setup

VERSION = "0.1.2-dev"
version = f"v{VERSION.replace('-dev', '')}"


# A simple routine to read and adjust the README.md for this module into a format
# suitable for packaging.
# See Also: https://github.com/microsoft/MLOS/tree/main/mlos_core/setup.py
def _get_long_desc_from_readme(base_url: str) -> dict:
    pkg_dir = os.path.dirname(__file__)
    readme_path = os.path.join(pkg_dir, "README.md")
    if not os.path.isfile(readme_path):
        return {
            "long_description": "missing",
        }
    jsonc_re = re.compile(r"```jsonc")
    link_re = re.compile(r"\]\(([^:#)]+)(#[a-zA-Z0-9_-]+)?\)")
    with open(readme_path, mode="r", encoding="utf-8") as readme_fh:
        lines = readme_fh.readlines()
        # Tweak source source code links.
        lines = [jsonc_re.sub(r"```json", line) for line in lines]
        # Tweak the lexers for local expansion by pygments instead of github's.
        lines = [link_re.sub(f"]({base_url}" + r"/\1\2)", line) for line in lines]
        return {
            "long_description": "".join(lines),
            "long_description_content_type": "text/markdown",
        }


setup(
    version=VERSION,
    **_get_long_desc_from_readme(f"https://github.com/microsoft/vasim/tree/{version}/"),
)
