# India Incubator Atlas

Search, map and drill into startups across Indian incubators and accelerators by sector, incubator and city.

**Live site:** `https://<your-username>.github.io/india-incubator-atlas/`

## How it works

| Part | File | What it does |
| --- | --- | --- |
| Master sheet | `data/companies.csv` | One row per company. This is the database. |
| Incubator list | `data/incubators.csv` | One row per incubator; `id` is what companies refer to. |
| Website | `index.html` | The Atlas page. It reads `data/atlas.json`, which the build makes from the CSVs. |
| Checker + builder | `scripts/build.py` | Refuses bad rows (unknown sector or incubator, bad year or link), then builds `_site/`. |
| Publish | `.github/workflows/deploy.yml` | On every change to `main`: check, build, publish to GitHub Pages. |
| PR check | `.github/workflows/check.yml` | Checks the data on every pull request before you merge. |
| Suggestions | `.github/ISSUE_TEMPLATE/add-company.yml` + `workflows/suggest.yml` | "Suggest a company" form. Add the `approved` label and a pull request with the new row appears. |
| Backups | `.github/workflows/backup.yml` | Saves the CSVs as a Release on the 1st of every month. |

## Add a company (quickest way)

1. Open `data/companies.csv` on GitHub and click the pencil (Edit).
2. Add a line at the bottom. Leave `id` empty; the checker fills it.
   ```
   ,Acme Robotics,Robotics & Hardware; AI & Software,iitm-ic,Incubated,,Chennai,2025,acme.in,Warehouse robots,https://example.com/portfolio
   ```
3. Click **Commit changes**. Check the **Actions** tab: green means it is live in about a minute; red tells you which line to fix.

Separate several sectors or incubators with `; `. Sector names and incubator ids must match the lists below.

## Check locally (optional)

```
python scripts/build.py --check   # only check
python scripts/build.py           # check and build into _site/
python -m http.server -d _site    # preview at http://localhost:8000
python scripts/build.py --fix     # tidy: trim spaces, fill ids, sort by name
```

## Allowed values

**Sectors:** Quantum · Space & Aerospace · Drones & Defence · EV & Mobility · Climate & Energy · Agritech · Healthtech & Medtech · Biotech & Pharma · Fintech · Edtech & Skilling · AI & Software · SaaS & Enterprise · Robotics & Hardware · Semiconductors & Electronics · Cybersecurity · Consumer & D2C · Social Impact · Logistics & Supply Chain · Media & Content · Materials & Nanotech · Water & Sanitation · Legal & HR Tech · Proptech · Telecom & Networking · Food & Beverage · Fashion & Lifestyle · Business Services · Travel & Hospitality · Other

**Relationship:** Incubated · Invested · Accelerated · Supported · Associated

**Status:** empty (active) · Unicorn · Listed · Acquired · Shut

**Incubator ids:** see the `id` column of `data/incubators.csv`.
