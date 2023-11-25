#!/usr/bin/env python3

import urllib.request
import json
from pathlib import Path
import hashlib
from pyodide_version import pyodide_version as PYODIDE_VERSION


lockfile_url = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/repodata.json"

# get original lockfile from Pyodide
with urllib.request.urlopen(lockfile_url) as j:
    repodata = json.load(j)


def update_lockfile(packages):
    """ Update the 'packages' item of lockfile. """
    repodata["packages"] = repodata["packages"] | packages


# compute sha256 for basthon.tar
with open(Path("lib") / "dist" / "basthon.tar", 'rb') as f:
    sha256 = hashlib.sha256(f.read()).hexdigest()

# lockfile basthon's part
update_lockfile(
    {"basthon": {"name": "basthon",
                 "version": "0.0.1",
                 "file_name": "{basthonRoot}/basthon.tar",
                 "install_dir": "site",
                 "sha256": sha256,
                 "depends": [],
                 "imports": ["basthon"]}}
)

# Fix: Pyodide does not declare pylab as importable from matplotlib
#      probably since it is deprecated...
repodata["packages"]["matplotlib"]["imports"].append("pylab")

# add our custom lockfile (packages part)
with open("custom-packages.json") as f:
    update_lockfile(json.load(f))

# add our Basthon packages to lockfile
for f in (Path("src") / "modules").glob("*/repodata.json"):
    with open(f) as j:
        packages = json.load(j)
    assert len(packages) == 1, "Failsafe: look carrefully if we can handle multiple packages here"
    pname, value = next(iter(packages.items()))
    fname = next((f.parent / "dist").glob("*.whl"))
    value['file_name'] = f"{{basthonRoot}}/modules/{fname.name}"
    with open(fname, 'rb') as whl:
        value['sha256'] = hashlib.sha256(whl.read()).hexdigest()
    update_lockfile(packages)

# writing repodata.json
with open("lib/dist/repodata.json", 'w') as f:
    json.dump(repodata, f)
