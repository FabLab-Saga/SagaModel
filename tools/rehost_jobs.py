"""Drop the Job_* items from layout/layout.yaml (before re-exporting) or re-point their `on:` to their machines
(after). System python3:  python3 tools/rehost_jobs.py drop|host"""
import re
import sys

HOST = {"Job_ShopBot": "ShopBot_PRSalpha_120_60", "Job_Glowforge_1": "Glowforge_ProHD_1", "Job_Prusa_01": "Prusa_MK3S_01",
        "Job_Prusa_03": "Prusa_MK3S_03", "Job_Prusa_04": "Prusa_MK3S_04", "Job_Prusa_06": "Prusa_MK3S_06", "Job_SRM20_1": "Roland_SRM20_1"}
p = "layout/layout.yaml"
s = open(p).read()
blocks = re.split(r"(?=\n  - id: )", s)
first = lambda b: (re.search(r"objects: \[([^\],]+)", b) or [None, None])[1]
idof = {first(b): re.search(r"id: (\S+)", b)[1] for b in blocks if re.search(r"id: (\S+)", b) and first(b)}
out = []
for b in blocks:
    o = first(b)
    if o in HOST:
        if sys.argv[1] == "drop":
            continue
        host = idof[HOST[o]]
        b = re.sub(r'"on": \S+', '"on": ' + host, b) if '"on":' in b else b.replace("    locked:", f'    "on": {host}\n    locked:', 1)
    out.append(b)
open(p, "w").write("".join(out))
print(sys.argv[1], "done")
