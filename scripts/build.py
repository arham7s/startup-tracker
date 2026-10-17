#!/usr/bin/env python3
"""Validate the Atlas data and build the website.

    python scripts/build.py           # check data/*.csv and build the site into _site/
    python scripts/build.py --check   # only check, build nothing (used on pull requests)
    python scripts/build.py --fix     # tidy the CSVs in place: trim spaces, fill missing ids, sort by name

Exit code 1 means the data has errors; nothing is published until they are fixed.
Uses only the Python standard library.
"""
import csv, difflib, json, os, re, shutil, sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "_site")

SECTORS = ["Quantum", "Space & Aerospace", "Drones & Defence", "EV & Mobility", "Climate & Energy", "Agritech",
           "Healthtech & Medtech", "Biotech & Pharma", "Fintech", "Edtech & Skilling", "AI & Software",
           "SaaS & Enterprise", "Robotics & Hardware", "Semiconductors & Electronics", "Cybersecurity",
           "Consumer & D2C", "Social Impact", "Logistics & Supply Chain", "Media & Content", "Materials & Nanotech",
           "Water & Sanitation", "Legal & HR Tech", "Proptech", "Telecom & Networking", "Food & Beverage",
           "Fashion & Lifestyle", "Business Services", "Travel & Hospitality", "Other"]
RELATIONS = ["Incubated", "Invested", "Accelerated", "Supported", "Associated"]
STATUSES = ["", "Unicorn", "Listed", "Acquired", "Shut"]
COMPANY_COLS = ["id", "name", "sectors", "incubators", "relation", "status", "city", "year", "website", "note", "source"]
INCUBATOR_COLS = ["id", "name", "host", "city", "group", "founded", "scale", "focus", "website", "source", "order"]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:80] or "x"


def key(name):
    n = re.sub(r"\(.*?\)", " ", name.lower())
    n = re.sub(r"\b(private|pvt|limited|ltd|llp|opc|inc|technologies|technology)\b\.?", " ", n)
    return re.sub(r"[^a-z0-9]+", "", n)


def split(cell):
    return [x.strip() for x in re.split(r"[;|]", cell or "") if x.strip()]


def read(name, cols):
    path = os.path.join(DATA, name)
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        missing = [c for c in cols if c not in (r.fieldnames or [])]
        if missing:
            sys.exit(f"ERROR {name}: missing column(s) {', '.join(missing)}. The header row must be: {','.join(cols)}")
        return [{k: (v or "").strip() for k, v in row.items() if k} for row in r]


def write(name, cols, rows):
    with open(os.path.join(DATA, name), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for row in rows:
            w.writerow([row.get(c, "") for c in cols])


HINTS = {"space": "Space & Aerospace", "aero": "Space & Aerospace", "drone": "Drones & Defence", "defen": "Drones & Defence",
         "ev": "EV & Mobility", "mobility": "EV & Mobility", "climate": "Climate & Energy", "clean": "Climate & Energy",
         "energy": "Climate & Energy", "agri": "Agritech", "health": "Healthtech & Medtech", "med": "Healthtech & Medtech",
         "bio": "Biotech & Pharma", "pharma": "Biotech & Pharma", "fin": "Fintech", "edu": "Edtech & Skilling",
         "ai": "AI & Software", "software": "AI & Software", "saas": "SaaS & Enterprise", "robot": "Robotics & Hardware",
         "iot": "Robotics & Hardware", "semi": "Semiconductors & Electronics", "chip": "Semiconductors & Electronics",
         "cyber": "Cybersecurity", "security": "Cybersecurity", "logistic": "Logistics & Supply Chain",
         "material": "Materials & Nanotech", "nano": "Materials & Nanotech", "water": "Water & Sanitation",
         "quantum": "Quantum", "telecom": "Telecom & Networking", "food": "Food & Beverage", "d2c": "Consumer & D2C"}


def suggest(value, options):
    if options is SECTORS:
        low = value.lower()
        for k, v in HINTS.items():
            if low.startswith(k) or k in low.split():
                return f' Did you mean "{v}"?'
    m = difflib.get_close_matches(value, options, n=1, cutoff=0.5)
    return f' Did you mean "{m[0]}"?' if m else ""


def main():
    check_only = "--check" in sys.argv
    fix = "--fix" in sys.argv
    errors, warnings = [], []

    incs = read("incubators.csv", INCUBATOR_COLS)
    cos = read("companies.csv", COMPANY_COLS)

    inc_ids = set()
    for n, row in enumerate(incs, start=2):
        if not row["id"] or not row["name"]:
            errors.append(f"incubators.csv line {n}: id and name are required")
        if row["id"] in inc_ids:
            errors.append(f'incubators.csv line {n}: id "{row["id"]}" is used twice')
        inc_ids.add(row["id"])

    seen_ids, seen_keys = {}, {}
    for n, row in enumerate(cos, start=2):
        where = f"companies.csv line {n}"
        if not row["name"]:
            if any(row.values()):
                errors.append(f"{where}: name is empty")
            continue
        if not row["id"]:
            row["id"] = slug(row["name"])
            base, k = row["id"], 2
            while row["id"] in seen_ids:
                row["id"] = f"{base}-{k}"; k += 1
            if not fix:
                warnings.append(f'{where}: no id, using "{row["id"]}" (run --fix to save it)')
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", row["id"]):
            errors.append(f'{where}: id "{row["id"]}" may only use lowercase letters, digits and dashes')
        if row["id"] in seen_ids:
            errors.append(f'{where}: id "{row["id"]}" already used on line {seen_ids[row["id"]]}')
        seen_ids[row["id"]] = n

        k = key(row["name"])
        if k in seen_keys:
            warnings.append(f'{where}: "{row["name"]}" looks like a duplicate of line {seen_keys[k]}')
        seen_keys.setdefault(k, n)

        secs = split(row["sectors"])
        if not secs:
            errors.append(f"{where} ({row['name']}): add at least one sector")
        for s in secs:
            if s not in SECTORS:
                errors.append(f'{where} ({row["name"]}): unknown sector "{s}".{suggest(s, SECTORS)}')
        ids = split(row["incubators"])
        if not ids:
            errors.append(f"{where} ({row['name']}): add at least one incubator id")
        for i in ids:
            if i not in inc_ids:
                errors.append(f'{where} ({row["name"]}): unknown incubator id "{i}".{suggest(i, sorted(inc_ids))}')
        if row["relation"] and row["relation"] not in RELATIONS:
            errors.append(f'{where}: relation must be one of {", ".join(RELATIONS)}')
        if row["status"] not in STATUSES:
            errors.append(f'{where}: status must be empty or one of {", ".join(STATUSES[1:])}')
        if row["year"] and not re.fullmatch(r"(19|20)\d\d", row["year"]):
            errors.append(f'{where}: year "{row["year"]}" should be four digits, like 2024')
        if row["source"] and not row["source"].startswith(("http://", "https://")):
            errors.append(f"{where}: source must be a full link starting with https://")
        if " " in row["website"]:
            errors.append(f"{where}: website has a space in it")

    for w in warnings[:50]:
        print("warning:", w)
    if len(warnings) > 50:
        print(f"warning: … and {len(warnings) - 50} more")
    if errors:
        print(f"\n{len(errors)} error(s) — fix these, then try again:")
        for e in errors:
            print("ERROR", e)
        sys.exit(1)

    if fix:
        cos.sort(key=lambda r: r["name"].lower())
        incs.sort(key=lambda r: int(r["order"] or 999))
        write("companies.csv", COMPANY_COLS, cos)
        write("incubators.csv", INCUBATOR_COLS, incs)
        print("Tidied data/companies.csv and data/incubators.csv")

    print(f"OK: {len(cos)} companies, {len(incs)} incubators, {len(warnings)} warning(s)")
    if check_only:
        return

    fields = ["id", "name", "sectors", "incubators", "relation", "status", "city", "year", "website", "note", "source"]
    rows = []
    for r in cos:
        if not r["name"]:
            continue
        rows.append([r["id"], r["name"], split(r["sectors"]), split(r["incubators"]), r["relation"] or "Incubated",
                     r["status"], r["city"], r["year"], r["website"], r["note"], r["source"]])
    inc_out = []
    for r in incs:
        d = {k: r[k] for k in INCUBATOR_COLS if r.get(k)}
        if "order" in d:
            d["order"] = int(d["order"])
        inc_out.append(d)
    atlas = {"built": datetime.now(timezone.utc).isoformat(timespec="seconds"), "incubators": inc_out,
             "fields": fields, "rows": rows}

    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(os.path.join(OUT, "data"))
    with open(os.path.join(OUT, "data", "atlas.json"), "w", encoding="utf-8") as f:
        json.dump(atlas, f, ensure_ascii=False, separators=(",", ":"))
    repo = os.environ.get("GITHUB_REPOSITORY", "arham7s/india-incubator-atlas")
    with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
        html = f.read().replace("__REPO__", repo)
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    print(f"Built _site/ for {repo}")


if __name__ == "__main__":
    main()
