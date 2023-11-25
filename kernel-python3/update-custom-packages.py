exit()

# run this inside basthon to update custom-packages.json
import micropip
import json


f0 = json.loads(micropip.freeze())
await micropip.install(["my_super_module", "my other_super_module"])
f1 = json.loads(micropip.freeze())

data = {p: f1["packages"][p] for p in f1["packages"] if p not in f0["packages"]}
print(json.dumps(data, indent=2))
