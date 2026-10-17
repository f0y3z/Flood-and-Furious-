import time
import requests
import pandas as pd

ZONES = {   # approximate (lat, lon), verify on a map
    "Sylhet Sadar":  (24.90, 91.87),
    "Dakshin Surma": (24.83, 91.85),
    "Osmani Nagar":  (24.80, 91.98),
    "Balaganj":      (24.67, 92.00),
    "Beanibazar":    (24.82, 92.15),
    "Bishwanath":    (24.78, 91.73),
    "Companiganj":   (25.00, 91.75),
    "Fenchuganj":    (24.70, 91.93),
    "Golapganj":     (24.85, 92.02),
    "Gowainghat":    (25.10, 92.00),
    "Jaintiapur":    (25.13, 92.12),
    "Kanaighat":     (24.99, 92.27),
    "Zakiganj":      (24.87, 92.36),
}
START, END = "2010-01-01", "2018-12-31"
URL = "https://archive-api.open-meteo.com/v1/archive"

frames = []
for name, (lat, lon) in ZONES.items():
    r = None
    for attempt in range(3):
        r = requests.get(URL, params={
            "latitude": lat, "longitude": lon,
            "start_date": START, "end_date": END,
            "daily": "precipitation_sum,precipitation_hours",
            "timezone": "Asia/Dhaka",
        }, timeout=60)
        if r.status_code == 429:      # rate limited, wait and retry
            time.sleep(30)
            continue
        break
    r.raise_for_status()
    j = r.json()
    d = j["daily"]

    df = pd.DataFrame({
        "date": pd.to_datetime(d["time"]),
        "rain_1d": d["precipitation_sum"],
        "rain_hours": d["precipitation_hours"],
    })
    df["zone"] = name
    df["elevation_m"] = j.get("elevation")
    for n in (3, 7, 14, 30):
        df[f"rain_{n}d"] = df["rain_1d"].rolling(n).sum()
    df["month"] = df["date"].dt.month
    frames.append(df)
    print("done:", name, len(df))
    time.sleep(1)

out = pd.concat(frames, ignore_index=True)
out.to_csv("rainfall_sylhet.csv", index=False)
print(out.shape)
print(out.head())
