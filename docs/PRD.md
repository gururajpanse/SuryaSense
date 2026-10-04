# PRD – Aditya-L1 Solar Flare Nowcasting & Forecasting

Product Requirements Document · ISRO Problem Statement 15 · Version 0.1 · 4 October 2026

## 1. Document control

| Item | Value |
| --- | --- |
| Built from | BRD version 0.2 (decisions D-1 to D-9 confirmed, except where marked proposed) |
| Phase | AI SDLC phase 1: requirements (second of two documents) |
| Status | Draft for review |
| Submission | About 12 Oct 2026 (exact demo date still open, OI-7) |
| Companion documents | AGENTS.md, plan.md, implementation\_plan.md (to follow) |

**Priority key.** P0 = core system that must work: nowcasting, catalogue, API, dashboard, live alerts, quality gates. P1 = forecasting, built only after P0 works. P2 = stretch.

**ID key.** US = user story, FR = functional requirement, DR = dashboard requirement, NFR = non-functional requirement, ML = model and evaluation requirement, AC = acceptance criterion. BR, BO, BRU, SM and OI refer to the BRD.

**UNVERIFIED** means not yet confirmed with real data or a source. These items are listed in section 14.

## 2. Product overview

The product is a Python pipeline with a FastAPI back end and a Vite, React and TypeScript dashboard. It reads Aditya-L1 SoLEXS and HEL1OS data, detects flares, builds a master flare catalogue, validates it against the GOES flare list, and shows light curves and alerts. A separate forecasting module estimates the probability of a flare in the next 30 minutes.

Three principles shape every requirement.

1. **Nowcasting first (BRD D-9).** Detectors, catalogue, API, dashboard, replay and live alerts form one complete system. Forecasting is added afterwards and can be switched off without breaking anything else.
2. **Two modes (BRD D-1).** Replay mode uses Aditya-L1 data from past days. Live mode uses the GOES real-time feed, because Aditya-L1 data is not available in real time.
3. **Honest evaluation.** Chronological splits, trailing windows only, thresholds tuned on validation data only, test set scored once, and weak results reported as they are.

This is a student project. It is **not an operational space-weather warning system**.

## 3. Personas

| Persona | Who | Goal | Needs from the product | Must avoid |
| --- | --- | --- | --- | --- |
| Evaluator | Professor or evaluator who watches the demo | Judge whether the method is correct and the results are honest | Quick view of detected flares, comparison with GOES, per-class results, a working live demo | Hidden assumptions, inflated metrics, a demo that fails |
| Developer | Project lead who builds and runs everything | Build, rebuild and debug the pipeline within 8 days | Config-driven runs, clear errors, tests, a repository that the coding agent cannot damage | Manual steps, hard-coded dates, silent data problems |
| Observer | Teammate or audience member with no solar physics background | Understand at a glance whether something is happening | Plain status banner, clear colours and words, a visible not-operational notice | Jargon, misleading alarms |

## 4. User stories

| ID | As a | I want | So that | Priority | Linked requirements |
| --- | --- | --- | --- | --- | --- |
| US-01 | Developer | SoLEXS and HEL1OS files read into clean tables | I can analyse both bands | P0 | FR-02, FR-03, FR-09 |
| US-02 | Developer | a manifest and coverage report | I know which days are usable and how much the instruments overlap | P0 | FR-04, FR-05, FR-06 |
| US-03 | Developer | to change data windows in one config file | I never edit code to change dates | P0 | FR-01 |
| US-04 | Developer | detectors that output a flare list for any day | I get the catalogue | P0 | FR-10 to FR-14 |
| US-05 | Developer | one command to rebuild the catalogue | results are reproducible | P0 | FR-15 |
| US-06 | Evaluator | to see how many flares the system found, missed or wrongly flagged versus GOES | I can judge accuracy | P0 | FR-18 |
| US-07 | Evaluator | results split by flare class | I can see if big flares are caught | P0 | FR-18 |
| US-08 | Evaluator | to replay a past day and watch alerts appear | I can see the system work on Aditya-L1 data | P0 | FR-31, FR-32, DR-03 to DR-06 |
| US-09 | Evaluator | to see live GOES data with alerts | I see it work in real time | P0 | FR-33, FR-34, DR-02 |
| US-10 | Observer | a banner that says Quiet, Flare in progress or Forecast watch | I understand the situation at a glance | P0 | DR-06 |
| US-11 | Observer | a clear notice that this is not an official warning | I am not misled | P0 | DR-11 |
| US-12 | Developer | to train and compare forecast models | I know whether complexity helps | P1 | FR-20 to FR-29 |
| US-13 | Evaluator | forecast probability and lead time, when available | I can judge early warning | P1 | FR-28, DR-07 |
| US-14 | Developer | to switch forecasting off and still have a working system | a failed forecast cannot ruin the demo | P0 | FR-30 |
| US-15 | Developer | automated tests and CI | I can trust changes made by the coding agent | P0 | FR-37, NFR-06, NFR-07 |
| US-16 | Evaluator | a model card with limits | I know what the models can and cannot do | P0 | FR-40 |
| US-17 | Developer | a guarantee that raw data and secrets never reach Git | I respect the data licence | P0 | FR-08, NFR-08, NFR-10 |

## 5. System modules and build order

| Order | Module | Folder (see agreed structure) | Priority | Depends on | Can be switched off |
| --- | --- | --- | --- | --- | --- |
| 1 | Configuration | config/ | P0 | none | No |
| 2 | Data readers and manifest | src/solarflare/io, scripts/ | P0 | config | No |
| 3 | Preprocessing | src/solarflare/preprocess | P0 | readers | No |
| 4 | Nowcast detectors and catalogue | src/solarflare/nowcast, data/catalog | P0 | preprocessing | No |
| 5 | Alerts | src/solarflare/alerts | P0 | nowcast | No |
| 6 | API | app/ (back end) | P0 | catalogue, alerts | No |
| 7 | Dashboard | app/ (frontend) | P0 | API | No |
| 8 | Features and labels | src/solarflare/features | P1 | preprocessing, GOES | Yes |
| 9 | Forecast models | src/solarflare/forecast, models/ | P1 | features | Yes |
| 10 | Quality and delivery | tests/, .github/workflows/ci.yml, Docker | P0 | all | No |

The exact paths inside app/ for back end and frontend are decided in implementation\_plan.md, which must follow the agreed folder structure.

## 6. Functional requirements

### 6.1 Data and ingestion

| ID | Requirement | Priority | BRD link |
| --- | --- | --- | --- |
| FR-01 | config/data\_windows.yaml defines pilot, train, validation and test windows, the embargo, and excluded dates. No date is hard-coded anywhere else. | P0 | BR-26, BRU-01, BRU-11 |
| FR-02 | The SoLEXS reader returns a UTC-indexed table for a given day, with documented columns and units, and reports a missing or unreadable day instead of failing silently. | P0 | BR-01 |
| FR-03 | The HEL1OS reader reads the FITS light curves for each energy band at the native 1 second cadence, joins 12-hour chunks, and reports gaps between chunks. | P0 | BR-02 |
| FR-04 | data/data\_manifest.csv lists every raw file: instrument, date, file name, size, checksum, status and read result. | P0 | BR-03 |
| FR-05 | A coverage report (docs/data\_coverage) lists, for every day in the windows, which instrument has data, plus the number of days with both. | P0 | BR-04 |
| FR-06 | Duplicate, corrupt and excluded files are detected (by checksum, content comparison and the exclusion list), flagged in the manifest and skipped, never deleted. | P0 | BR-05, BRU-11 |
| FR-07 | A GOES loader reads the flare summary and 1-minute flux files, and a GOES real-time client reads the live feed. Whether 2026 science-quality GOES files exist is **UNVERIFIED**; the loader must accept another satellite folder or operational data. | P0 | BR-06 |
| FR-08 | Everything under data/raw is treated as read-only. No code writes there. | P0 | BR-27 |
| FR-09 | Preprocessing writes Parquet files to data/interim and data/processed: UTC timestamps, bad values flagged, native cadence kept for detection, and a 1-minute grid for combined features. Gaps longer than a configured length are not interpolated. | P0 | BR-01, BR-02 |

### 6.2 Nowcasting and catalogue

| ID | Requirement | Priority | BRD link |
| --- | --- | --- | --- |
| FR-10 | The soft X-ray detector uses a trailing rolling background, a threshold above background, a derivative check and peak finding. It outputs start, peak and end times for each flare. | P0 | BR-07 |
| FR-11 | The hard X-ray detector uses the same method on the configured HEL1OS energy bands. | P0 | BR-08 |
| FR-12 | All detector settings live in config files, one set per data source (SoLEXS, HEL1OS, GOES), and are tuned on the validation window only. | P0 | BRU-04 |
| FR-13 | A merge step combines soft and hard detections that fall within a configured time tolerance into one event with a band flag: soft only, hard only, or both. | P0 | BR-09 |
| FR-14 | Each event gets a class estimate when a trustworthy calibration to GOES classes exists. Calibration of SoLEXS to GOES classes is **UNVERIFIED**; if it is not available, events carry an amplitude estimate and the matched GOES class is used only for reporting. | P0 | BR-09 |
| FR-15 | The catalogue is saved as Parquet and a DuckDB or SQLite table, and rebuilt with one command from configuration. | P0 | BR-10 |
| FR-16 | Nowcasting is causal: the output at time t depends only on data up to t. The same code is used in replay and live mode. | P0 | BRU-03 |
| FR-17 | The same detector code runs on GOES flux with its own configuration for live mode. | P0 | BR-22 |

### 6.3 Validation

| ID | Requirement | Priority | BRD link |
| --- | --- | --- | --- |
| FR-18 | Detected flares are matched one-to-one to the GOES flare list. A match means the intervals overlap or the peaks differ by at most a configured tolerance (proposed default 5 minutes). The report gives matched, missed and false detections, TPR and false alarm ratio, overall and by class. | P0 | BR-11, BR-17 |
| FR-19 | The report also gives detection delay (alert time minus GOES flare start) and peak-time error. | P1 | BR-16 |

### 6.4 Forecasting (separate module, built after P0 works)

| ID | Requirement | Priority | BRD link |
| --- | --- | --- | --- |
| FR-20 | The label builder marks a time step positive when a GOES flare peak occurs in the next 30 minutes (horizon configurable). Steps where a flare is already in progress are excluded from forecast evaluation, because that is nowcasting. | P1 | BR-12 |
| FR-21 | The feature builder uses trailing windows only (for example the last 5, 15, 30 and 60 minutes: mean, maximum, slope, soft and hard ratio). Features are listed in docs/data\_dictionary. | P1 | BR-13, BRU-03 |
| FR-22 | Splits come from config, are chronological, and have a 60-minute embargo. An automated check fails if any splits overlap. | P1 | BRU-01, BRU-02 |
| FR-23 | A threshold baseline gives a probability-like score from a simple rule on soft X-ray level and rise. | P1 | BR-14 |
| FR-24 | A logistic regression model is trained and evaluated. | P1 | BR-14 |
| FR-25 | An XGBoost or LightGBM model is trained and evaluated. | P1 | BR-14 |
| FR-26 | Three trained variants: Model A (SoLEXS plus HEL1OS features, replay mode), Model A soft-only (to test whether hard X-rays help), and Model G (GOES only, live mode). | P1 | BR-14, BR-22 |
| FR-27 | A probability becomes an alert using a threshold chosen on validation data by a rule stated in config. Consecutive steps above threshold form one alert episode, with a configured cooldown. | P1 | BR-15 |
| FR-28 | Forecast evaluation reports TPR and false alarm ratio per alert episode, TSS and precision-recall per time step, lead time per true alert, all by class. | P1 | BR-16, BR-17 |
| FR-29 | Each saved model in models/ has a metadata file: data windows, features, settings, metrics, date and Git commit. | P1 | BR-18 |
| FR-30 | A config switch turns the forecasting module off. With it off, the catalogue, API and dashboard work and an automated test proves it. | P0 | D-9 |

### 6.5 API (FastAPI, read-only)

| ID | Requirement | Priority | BRD link |
| --- | --- | --- | --- |
| FR-31 | Read-only endpoints: health, list of replay days, light curve slice (instrument, start, end), flare catalogue query, live status, and forecast (when enabled). No endpoint changes data. | P0 | BR-19 to BR-22 |
| FR-32 | Light curve and catalogue endpoints return time slices so the dashboard can replay at any speed. | P0 | BR-21 |
| FR-33 | A live poller fetches the GOES real-time feed about every 60 seconds, runs the nowcast on it, caches the result and retries with back-off after errors. The feed format and reachability are **UNVERIFIED** (OI-4). | P0 | BR-22 |
| FR-34 | If the feed fails, the API switches to a recorded GOES sample and sets a fallback flag the dashboard shows. | P0 | BR-24 |
| FR-35 | Every response states mode (replay or live), data source, data time in UTC, and model version where relevant. | P0 | BR-23 |
| FR-36 | When forecasting is off, the forecast endpoint answers with a clear disabled status, not an error. | P0 | D-9 |

### 6.6 Quality, delivery and documentation

| ID | Requirement | Priority | BRD link |
| --- | --- | --- | --- |
| FR-37 | CI runs pytest, ruff, mypy, Vitest, ESLint and a dependency scan on every push. | P0 | BR-25 |
| FR-38 | Docker packaging starts the API and the dashboard together. | P1 | BR-28 |
| FR-39 | The README gives exact steps to rebuild the pilot results from a fresh clone. | P0 | SM-9 |
| FR-40 | A model card (docs/model\_card) states data, method, metrics, limits, intended use and the not-operational notice, and an AI-usage note records how AI tools were used. | P0 | BR-18, BR-29 |
| FR-41 | Every pipeline run logs a run id, the config used and the Git commit. | P0 | BR-10 |

## 7. Dashboard requirements

The dashboard is a single-page app built with Vite, React and TypeScript, served alongside the FastAPI back end. It is designed for a laptop screen or projector.

| ID | Requirement | Priority |
| --- | --- | --- |
| DR-01 | One page, designed for screens of 1280 pixels wide or more. Mobile layout is not required. | P0 |
| DR-02 | A visible switch between Replay and Live. The current mode is always shown on screen. | P0 |
| DR-03 | Replay: a day picker that lists only days with data (from the API), play and pause, a seek bar, and a speed control (for example 1x, 10x, 60x). | P0 |
| DR-04 | Two linked time-series panels with a shared time axis and zoom: soft X-ray and hard X-ray. In live mode the soft panel shows GOES, and the hard panel says hard X-rays are not available in live mode. | P0 |
| DR-05 | Flare markers for start, peak and end on the panels, with the band flag (soft, hard or both). | P0 |
| DR-06 | An alert banner with three states: Quiet, Flare in progress (nowcast), and Forecast watch (only when forecasting is on). Each state uses colour and a text label together. | P0 |
| DR-07 | A forecast panel showing probability over time with the alert threshold line. It is hidden when forecasting is off, with a short note. | P1 |
| DR-08 | In replay, GOES flares can be shown on the chart and in the list, with a toggle. | P0 |
| DR-09 | A sortable catalogue table for the visible range: start, peak, end, band flags, class or amplitude estimate, and the matched GOES flare. | P0 |
| DR-10 | A status bar: data source, mode, last data time in UTC, feed health, API health and model version. | P0 |
| DR-11 | A permanent notice on every screen: not an operational warning system. | P0 |
| DR-12 | A fallback banner when the live feed is down and the recorded sample is being shown. | P0 |
| DR-13 | An alert log listing the alerts raised in the current session with time and type. | P1 |
| DR-14 | Clear error states: if the API is down the page shows a message, never a blank chart. | P0 |
| DR-15 | Times are shown in UTC. A local-time toggle is optional. | P0, P2 |
| DR-16 | A colour-blind-safe palette. Meaning never depends on colour alone. | P0 |
| DR-17 | Charts handle a full day of data. One day of 1-second HEL1OS data is 86,400 points, so the API or the chart reduces points for display without hiding flare peaks. | P0 |
| DR-18 | An About panel citing ISRO and ISSDC for Aditya-L1 data and NOAA for GOES data, and linking to the model card. | P0 |

## 8. Non-functional requirements

Targets marked proposed are starting values to be measured on the pilot data and then confirmed or changed.

| ID | Category | Requirement | Target |
| --- | --- | --- | --- |
| NFR-01 | Performance | Building the catalogue for one day of data on the project laptop | At most 5 minutes (proposed) |
| NFR-02 | Performance | A selected replay day appears in the dashboard | Within 3 seconds (proposed) |
| NFR-03 | Live latency | New live data reaches the screen | Within about 60 seconds of arrival (SM-10) |
| NFR-04 | Reliability | Feed errors never crash the back end; retries with back-off; fallback banner after failure | Fallback shown within 2 minutes (proposed) |
| NFR-05 | Reproducibility | Pinned dependencies, fixed random seeds, config logged for each run | Same config and data give the same results |
| NFR-06 | Maintainability | Type hints, ruff and mypy clean, modules kept inside the agreed folders | CI passes |
| NFR-07 | Testing | pytest for readers, detectors, matching, splits and leakage; Vitest for key dashboard components | Coverage of nowcast and io code at least 70 percent (proposed) |
| NFR-08 | Security | No secrets in the repository; .env files git-ignored; dependency scan in CI; read-only API; CORS limited to the local dashboard | CI and review checks pass |
| NFR-09 | Portability | Docker runs the API and dashboard together. The laptop operating system and the Python and Node versions are **UNVERIFIED** (OI-12) | Runs from a fresh clone |
| NFR-10 | Data protection | Raw data, extracted data and large derived files are git-ignored; a check fails if they are staged | Zero data files tracked |
| NFR-11 | Usability | A new user runs the demo on pilot data by following the README | Within 15 minutes (proposed) |
| NFR-12 | Observability | Structured logs with run id, config and Git commit | Present for every run |
| NFR-13 | Attribution | ISRO, ISSDC and NOAA are cited in the README, the model card and the dashboard | Present |

## 9. Data requirements

### 9.1 Storage and Git rules

The agreed folder structure applies. Train, validation and test are **not** folders; the split lives only in config/data\_windows.yaml.

| Data | Location | Format | Git status |
| --- | --- | --- | --- |
| Raw SoLEXS files | data/raw/solexs/YYYY-MM/ | Zip as downloaded | Ignored, read-only |
| Raw HEL1OS files | data/raw/hel1os/YYYY-MM/ | Zip as downloaded | Ignored, read-only |
| Raw GOES files | data/raw/goes/flsum and data/raw/goes/avg1m | NetCDF or CSV as downloaded (**UNVERIFIED**) | Ignored |
| Extracted files | data/extracted | FITS | Ignored |
| Cleaned per-instrument series | data/interim | Parquet | Ignored |
| Features and labels | data/processed | Parquet | Ignored |
| Flare catalogue | data/catalog | Parquet and DuckDB or SQLite | Ignored by default |
| Manifest | data/data\_manifest.csv | CSV with names, sizes, checksums only | May be committed |
| Windows and detector settings | config/ | YAML | Committed |
| Models and metadata | models/ | Pickle or native model files and JSON | Metadata committed; model files decided in implementation\_plan.md |
| Recorded GOES sample for the fallback | A small folder named in implementation\_plan.md | CSV or Parquet | May be committed after the licence is checked |

### 9.2 Data windows

The windows below are held in config, so changing them is a one-file edit. The compact windows are a **proposal** to cut download time for the 8-day deadline and are not yet confirmed (OI-10).

| Window | BRD windows | Proposed compact windows |
| --- | --- | --- |
| Pilot | 2026-09-19 to 2026-09-25, skipping 22 and 23 Sep | Same |
| Train | 2026-07-01 to 2026-07-31 | 2026-07-01 to 2026-07-21 |
| Validation | 2026-08-01 to 2026-08-15 | 2026-08-01 to 2026-08-08 |
| Test | 2026-09-01 to 2026-09-15 | 2026-09-01 to 2026-09-10 |
| Approximate HEL1OS download | about 6.5 GB | about 4 GB |

All windows are **UNVERIFIED** until Total Rows are confirmed on both portals (OI-1). Model G is trained on GOES data before the test period; its dates are set in config once GOES availability is known (OI-3).

### 9.3 Data quality rules

- Timestamps are converted to UTC and checked to increase in order.
- Units and energy bands are recorded in the data dictionary.
- Missing values are flagged and never silently filled. Gaps longer than a configured length are not interpolated.
- Duplicated days (the four excluded dates and any found by checksum or content comparison) are flagged and skipped.
- Every dropped file or day is listed with a reason in the manifest or coverage report.

## 10. Model and evaluation requirements

### 10.1 Tasks

| Task | Type | Trained | Output | Priority |
| --- | --- | --- | --- | --- |
| Nowcast | Rule-based event detection | No. Only detector settings are tuned on the validation window | Flare events with start, peak, end | P0 |
| Forecast | Binary classification at each 1-minute step: will a flare peak occur in the next 30 minutes | Yes: baseline, logistic regression, XGBoost or LightGBM | Probability, then alert episodes | P1 |

### 10.2 Model requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| ML-01 | Splits come from config, are chronological and have a 60-minute embargo. An automated check fails on overlap. | P1 |
| ML-02 | Features use only data up to the prediction time. An automated leakage test changes data after time t and confirms the features at t do not change. | P1 |
| ML-03 | Class imbalance is handled in training (for example class weights). Validation and test data are never resampled. The share of positive steps in each split is reported. | P1 |
| ML-04 | The model ladder is baseline, then logistic regression, then gradient boosting, each compared with the one before. Random seeds are fixed. Hyper-parameter search is small, uses validation data only, and is limited by the time available. | P1 |
| ML-05 | Variants: Model A (SoLEXS plus HEL1OS, replay), Model A soft-only, Model G (GOES only, live). Model G never uses SoLEXS or HEL1OS data, and Model A never uses GOES flux as an input. GOES flare times are used only for labels and validation of Model A. | P1 |
| ML-06 | The alert threshold is chosen on validation data by a rule named in config (for example highest TSS, or highest TPR under a false alarm cap). | P1 |
| ML-07 | The test set is scored once. The evaluation script logs a hash of the config and models and refuses a second test run unless an explicit flag is given. Anything changed after seeing test results is reported as such. | P1 |
| ML-08 | Results are reported by class: B and C versus M and X. If a class has fewer than 10 events in a window (proposed), the report shows the count and makes no performance claim for that class. | P0 |
| ML-09 | A Brier score or reliability check is reported so the probabilities can be judged, not only the alerts. | P1 |
| ML-10 | Weak or negative results are written in the report and the model card. A model that does not beat the baseline is reported as not helping. | P0 |
| ML-11 | Optional: bootstrap confidence intervals by day. | P2 |

### 10.3 Metric definitions

The BRD used the phrase false alarm rate. That phrase has more than one meaning in the literature, so this PRD fixes two terms and reports both. The evaluator's preferred definition is **UNVERIFIED** (OI-11).

| Metric | Definition | Level |
| --- | --- | --- |
| TPR (recall) | TP divided by (TP plus FN): share of real flares caught | Events for nowcast; alert episodes for forecast |
| False alarm ratio (FAR) | FP divided by (TP plus FP): share of alerts that were wrong | Events or alert episodes |
| POFD | FP divided by (FP plus TN): share of non-flare time steps that raised an alarm | Time steps |
| TSS | TPR minus POFD | Time steps |
| Precision | TP divided by (TP plus FP), which equals 1 minus FAR | Events or episodes |
| Precision-recall curve and average precision | Standard definitions | Time steps |
| Brier score | Mean squared error of the probability | Time steps |
| Lead time | GOES flare peak time minus the first alert time of the episode, in minutes, for true alerts only; report the median and the spread | Alert episodes |
| Detection delay | Nowcast alert time minus GOES flare start time | Events |

Accuracy is never used as a headline metric (BRU-08).

## 11. Acceptance criteria

Each criterion can be checked by running a command or inspecting a named output. Targets marked goal are goals, not guarantees: if a goal is missed the report states the actual number and the reason.

| ID | Criterion | Linked | Priority |
| --- | --- | --- | --- |
| AC-01 | Every pilot file is either read successfully or flagged in the manifest with a reason. No file fails silently. | FR-02, FR-03, FR-04 | P0 |
| AC-02 | The coverage report lists every day in all windows with its status and states the number of days with both instruments. | FR-05 | P0 |
| AC-03 | One command builds the catalogue for a pilot day and finishes within the NFR-01 target. | FR-10 to FR-15, NFR-01 | P0 |
| AC-04 | Causality test: changing data after time t does not change the nowcast output at t. | FR-16 | P0 |
| AC-05 | The catalogue has no duplicate flares, and every flare has start before peak before end. | FR-13, FR-15 | P0 |
| AC-06 | A validation report exists for the validation window with matched, missed and false detections, TPR and FAR, overall and by class. Goal: TPR at least 0.80 for C-class and above (SM-1). | FR-18 | P0 |
| AC-07 | The split check passes: no overlap and an embargo of at least 60 minutes. | FR-22 | P1 |
| AC-08 | The leakage test passes. | ML-02 | P1 |
| AC-09 | The test set is scored once and the log shows one test run. | ML-07 | P1 |
| AC-10 | The forecast report compares baseline, logistic regression and gradient boosting, plus Model A, Model A soft-only and Model G, with TSS, precision-recall, FAR, lead time and per-class results. | FR-26, FR-28 | P1 |
| AC-11 | With forecasting switched off, the catalogue, API and dashboard work, and the test suite proves it. | FR-30, FR-36 | P0 |
| AC-12 | Replay of a chosen day shows both light curves and flare markers, and an alert never appears before its detection time. | DR-03 to DR-06 | P0 |
| AC-13 | In a 30-minute rehearsal, live mode shows each new GOES point within about 60 seconds. | FR-33, NFR-03 | P0 |
| AC-14 | With the network disconnected, the dashboard shows the fallback banner within about 2 minutes and keeps running on the recorded sample. | FR-34, DR-12 | P0 |
| AC-15 | CI is green: pytest, ruff, mypy, Vitest, ESLint and the dependency scan. | FR-37 | P0 |
| AC-16 | From a fresh clone, the README steps rebuild the pilot results. | FR-39 | P0 |
| AC-17 | A check confirms no raw data files or secrets are tracked by Git. | FR-08, NFR-08, NFR-10 | P0 |
| AC-18 | The not-operational notice is visible on every dashboard screen. | DR-11 | P0 |
| AC-19 | The model card, the AI-usage note and the data citations exist. | FR-40, NFR-13 | P0 |

## 12. Traceability from ISRO to requirements

| ISRO item | BRD objective | Functional requirements | Acceptance criteria |
| --- | --- | --- | --- |
| Objective 1: automated nowcasting with real-time detection and classification using soft and hard X-ray data | BO-1 | FR-02, FR-03, FR-10 to FR-17 | AC-01 to AC-05 |
| Objective 2: forecasting from precursor patterns in soft and hard X-ray light curves | BO-2 | FR-20 to FR-29 | AC-07 to AC-10 |
| Expected outcome 1: automated database of nowcasted flares from combined light curves | BO-1 | FR-13, FR-15 | AC-05 |
| Expected outcome 2: trained forecasting model with quantifiable lead time | BO-2, BO-3 | FR-26 to FR-29 | AC-10 |
| Expected outcome 3: interface with light curves and visual alerts | BO-4 | FR-31 to FR-36, DR-01 to DR-18 | AC-11 to AC-14, AC-18 |
| Evaluation: detection of low and high class flares | BO-3 | FR-18, ML-08 | AC-06 |
| Evaluation: high true positive rate and low false alarm rate | BO-3 | FR-18, FR-28, section 10.3 | AC-06, AC-10 |
| Evaluation: lead time before flare peak | BO-3 | FR-19, FR-28 | AC-10 |
| Data: SoLEXS and HEL1OS Level-1 from PRADAN, supplementary data allowed | BO-1 | FR-01 to FR-09, FR-07 | AC-01, AC-02 |

## 13. Out of scope and change control

Out of scope matches BRD section 7: operational warning claims, real-time Aditya-L1 ingestion, full-mission downloads, image-based forecasting, public redistribution of raw data, user accounts and mobile apps.

Stretch items (60-minute horizon, 1D-CNN or LSTM, transfer learning, foundation-model comparison, two big-flare days from 2024) start only after every P0 acceptance criterion passes. A new request during the 8 days goes to the open items list and is not built unless the project lead removes something of equal size.

## 14. Open items

| ID | Open item | Needed by |
| --- | --- | --- |
| OI-1 | Confirm Total Rows for SoLEXS and HEL1OS in the chosen windows | Before bulk download |
| OI-2 | Measure the real SoLEXS and HEL1OS overlap | After the manifest is built |
| OI-3 | Confirm GOES 2026 file availability and the format, or choose the fallback; set Model G training dates | Before labelling |
| OI-4 | Test the live GOES feed (reachability and format) and prepare the recorded sample | Before the dashboard build |
| OI-7 | Confirm the exact demo date (submission about 12 Oct 2026) | Now |
| OI-8 | Decide whether to add two big-flare days from 2024 | After the pilot |
| OI-9 | Check whether SoLEXS can be calibrated to GOES flare classes (FR-14) | During nowcast build |
| OI-10 | Closed on 4 Oct 2026: the full BRD windows are being downloaded, so the compact windows in section 9.2 are not used | Before bulk download |
| OI-11 | Confirm with the evaluator which definition of false alarm rate they expect | Before the report |
| OI-12 | Record the laptop operating system, Python and Node versions, and free disk space | Before the repository setup |

## 15. Approval

| Role | Name | Decision | Date |
| --- | --- | --- | --- |
| Project lead |  |  |  |
| Professor or evaluator (optional) |  |  |  |
