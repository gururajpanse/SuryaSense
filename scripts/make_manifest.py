"""Build data manifest + daily coverage from filenames in data/raw. Read-only."""
import argparse, hashlib, re
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
SLX = re.compile(r"AL1_SLX_L1_(\d{8})_v[\d.]+\.zip$")
HLS = re.compile(r"HLS_(\d{8})_(\d{6})_(\d+)sec_lev1_.*\.zip$")
GAV = re.compile(r"avg1m_g\d+_d(\d{8})_")

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def scan(do_hash):
    rows = []
    for p in sorted(RAW.rglob("*")):
        if not p.is_file() or p.name == ".gitkeep":
            continue
        start = end = None
        if (m := SLX.match(p.name)):
            inst = "solexs"
            start = datetime.strptime(m[1], "%Y%m%d")
            end = start + timedelta(days=1)
        elif (m := HLS.match(p.name)):
            inst = "hel1os"
            start = datetime.strptime(m[1] + m[2], "%Y%m%d%H%M%S")
            end = start + timedelta(seconds=int(m[3]))
        elif "avg1m" in p.name and (m := GAV.search(p.name)):
            inst = "goes_avg1m"
            start = datetime.strptime(m[1], "%Y%m%d")
            end = start + timedelta(days=1)
        elif "flsum" in p.name:
            inst = "goes_flsum"
        else:
            inst = "unknown"
        rows.append(dict(
            instrument=inst, filename=p.name,
            path=p.as_posix(), size_mb=round(p.stat().st_size / 1e6, 2),
            start_utc=start, end_utc=end,
            sha256=sha256(p) if do_hash else ""))
    return pd.DataFrame(rows)

def merged_hours_per_day(df):
    """HEL1OS hours covered per UTC day, overlapping files merged."""
    iv = sorted(zip(df.start_utc, df.end_utc))
    merged = []
    for s, e in iv:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    hours = {}
    for s, e in merged:
        d = s.normalize()
        while d < e:
            nxt = d + pd.Timedelta(days=1)
            seg = (min(e, nxt) - max(s, d)).total_seconds() / 3600
            hours[d] = hours.get(d, 0) + seg
            d = nxt
    return hours

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-07-01")
    ap.add_argument("--end", default="2026-09-15")
    ap.add_argument("--hash", action="store_true")
    a = ap.parse_args()

    man = scan(a.hash)
    man.to_csv("data/data_manifest.csv", index=False)
    print(man.groupby("instrument").agg(files=("filename", "count"),
                                        size_mb=("size_mb", "sum")))

    days = pd.date_range(a.start, a.end, freq="D")
    slx = set(man[man.instrument == "solexs"].start_utc.dt.normalize())
    gav = set(man[man.instrument == "goes_avg1m"].start_utc.dt.normalize())
    hl = merged_hours_per_day(man[man.instrument == "hel1os"].copy())
    cov = pd.DataFrame({"date": days})
    cov["solexs"] = cov.date.isin(slx)
    cov["hel1os_hours"] = cov.date.map(lambda d: round(hl.get(d, 0), 1))
    cov["goes_avg1m"] = cov.date.isin(gav)
    cov["both"] = cov.solexs & (cov.hel1os_hours >= 20)
    cov.to_csv("data/coverage_daily.csv", index=False)

    print("\nDays with no SoLEXS:", list(cov[~cov.solexs].date.dt.strftime("%Y-%m-%d")))
    print("Days with HEL1OS < 20 h:", cov[cov.hel1os_hours < 20][["date", "hel1os_hours"]]
          .assign(date=lambda x: x.date.dt.strftime("%Y-%m-%d")).values.tolist())
    print("Days with both instruments (HEL1OS >= 20 h):", int(cov.both.sum()), "of", len(cov))

if __name__ == "__main__":
    main()