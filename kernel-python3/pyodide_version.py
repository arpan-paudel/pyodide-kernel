#!/usr/bin/env python3

from pathlib import Path
import re

regex = re.compile(r"PYODIDE_VERSION = \"(?P<version>.*)\"")

with open(Path("src") / "kernel.ts") as f:
    pyodide_version = regex.search(f.read()).group('version')

if __name__ == "__main__":
    print(pyodide_version)
