# Data directory

- **occupations.csv** – Built by the data pipeline (`python -m src.run_data_pipeline refresh-data`). Per-occupation fields: `id` (SOC), `title`, `skills`, `median_salary`, `growth_pct`, `education`, `sector`; and when O*NET data is present: `abilities`, `knowledge`, `work_activities`, `interests` (RIASEC order by score), `job_zone` (1–5 preparation level). The app loads this file.
- **onet/** – Created by the pipeline when you run `refresh-data`: O*NET ZIP is downloaded from onetcenter.org, unzipped here, and the zip is deleted. The extracted files are kept; `data/onet/` is in `.gitignore` and is not synced to GitHub.

## Manual downloads (BLS only)

The pipeline does **not** fetch BLS data; you must download these files and place them as below. Full source details are in the **project README** (Data pipeline → Offline file sources).

| What | Source | Save as |
|------|--------|--------|
| OES wages (May 2024 national) | [BLS OES Tables](https://www.bls.gov/oes/tables.htm) → May 2024 National XLS | Any `.xlsx` in **`data/bls_oes/`** (e.g. `national_M2024_dl.xlsx`) |
| Employment projections | [occupation.xlsx](https://www.bls.gov/emp/ind-occ-matrix/occupation.xlsx) | **`data/bls_projections/occupation.xlsx`** |
