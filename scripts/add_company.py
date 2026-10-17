#!/usr/bin/env python3
"""Append one company to data/companies.csv from a "Suggest a company" issue.

GitHub runs this automatically when you add the `approved` label to the issue.
It reads the issue form text from the ISSUE_BODY environment variable.
You can also run it yourself:  ISSUE_BODY="$(cat body.md)" python scripts/add_company.py
"""
import csv, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "data", "companies.csv")
INC = os.path.join(ROOT, "data", "incubators.csv")


def sections(body):
    out, cur = {}, None
    for line in body.splitlines():
        m = re.match(r"^###\s+(.*)", line)
        if m:
            cur = m.group(1).strip().lower(); out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    clean = {}
    for k, v in out.items():
        text = "\n".join(v).strip()
        clean[k] = "" if text in ("_No response_", "None") else text
    return clean


def field(f, *names):
    for n in names:
        for k, v in f.items():
            if k.startswith(n):
                return v
    return ""


def main():
    body = os.environ.get("ISSUE_BODY", "")
    if not body:
        sys.exit("ISSUE_BODY is empty")
    f = sections(body)
    name = field(f, "company name").strip()
    if not name:
        sys.exit("The issue has no company name")

    # Sectors / incubators come from checkbox lists ("- [X] AI & Software") or plain text.
    def ticked(text):
        boxes = re.findall(r"- \[[xX]\]\s*(.+)", text)
        return boxes or [x.strip() for x in re.split(r"[;,\n]", text) if x.strip()]

    incs = {}
    with open(INC, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            incs[r["name"].lower()] = r["id"]; incs[r["id"].lower()] = r["id"]
    inc_ids = []
    for x in ticked(field(f, "incubator")):
        x = re.sub(r"\s*\(.*?\)$", "", x).strip()
        inc_ids.append(incs.get(x.lower(), x))

    row = {
        "id": "",
        "name": name,
        "sectors": "; ".join(ticked(field(f, "sector"))),
        "incubators": "; ".join(inc_ids),
        "relation": field(f, "relationship") or "Incubated",
        "status": "" if field(f, "status").startswith("Active") else field(f, "status"),
        "city": field(f, "city"),
        "year": field(f, "year"),
        "website": re.sub(r"^https?://", "", field(f, "website")).strip("/"),
        "note": " ".join(field(f, "what they do").split())[:240],
        "source": field(f, "source"),
    }
    with open(CSV, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh); cols = reader.fieldnames; existing = list(reader)
    if any(r["name"].strip().lower() == name.lower() for r in existing):
        print(f'"{name}" is already in the sheet; adding the new incubator tags to it instead')
        for r in existing:
            if r["name"].strip().lower() == name.lower():
                have = [x.strip() for x in r["incubators"].split(";") if x.strip()]
                r["incubators"] = "; ".join(dict.fromkeys(have + inc_ids))
        rows = existing
    else:
        rows = existing + [row]
    with open(CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"Added {name}")


if __name__ == "__main__":
    main()
