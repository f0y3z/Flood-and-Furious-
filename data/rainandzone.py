import time
import requests
import pandas as pd

# Upazila metadata dictionary containing coordinates, baseline population, and fallback elevation
ZONES_META = {
    "Sylhet Sadar":  {"coords": (24.90, 91.87), "population": 620000},
    "Dakshin Surma": {"coords": (24.83, 91.85), "population": 250000},
    "Osmani Nagar":  {"coords": (24.80, 91.98), "population": 185000},
    "Balaganj":      {"coords": (24.67, 92.00), "population": 120000},
    "Beanibazar":    {"coords": (24.82, 92.15), "population": 290000},
    "Bishwanath":    {"coords": (24.78, 91.73), "population": 250000},
    "Companiganj":   {"coords": (25.00, 91.75), "population": 170000},
    "Fenchuganj":    {"coords": (24.70, 91.93), "population": 138000},
    "Golapganj":     {"coords": (24.85, 92.02), "population": 350000},
    "Gowainghat":    {"coords": (25.10, 92.00), "population": 290000},
    "Jaintiapur":    {"coords": (25.13, 92.12), "population": 180000},
    "Kanaighat":     {"coords": (24.99, 92.27), "population": 265000},
    "Zakiganj":      {"coords": (24.87, 92.36), "population": 240000},
}

START, END = "2010-01-01", "2018-12-31"
URL = "https://archive-api.open-meteo.com/v1/archive"

frames = []

for name, meta in ZONES_META.items():
    lat, lon = meta["coords"]
    r = None
    for attempt in range(3):
        r = requests.get(URL, params={
            "latitude": lat, 
            "longitude": lon,
            "start_date": START, 
            "end_date": END,
            "daily": "precipitation_sum,precipitation_hours",
            "timezone": "Asia/Dhaka",
        }, timeout=60)
        
        if r.status_code == 429:
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
    df["latitude"] = lat
    df["longitude"] = lon
    df["elevation_m"] = j.get("elevation", 10.0)
    df["population"] = meta["population"]
    
    # Feature Engineering (Rolling Rain Totals)
    for n in (3, 7, 14, 30):
        df[f"rain_{n}d"] = df["rain_1d"].rolling(n).sum()
        
    df["month"] = df["date"].dt.month
    
    # Synthetic / Rule-based Flood Labeling fallback (Step 1 of plan)
    # Marks severe rain events in low elevation zones as flood days
    df["flood_label"] = (
        (df["rain_3d"] > 150) & (df["elevation_m"] < 12)
    ).astype(int)

    frames.append(df)
    print(f"Processed: {name} | Elevation: {j.get('elevation')}m | Pop: {meta['population']}")
    time.sleep(1)

out = pd.concat(frames, ignore_index=True)
out.to_csv("sylhet_flood_dataset.csv", index=False)
print("Dataset generation complete. Shape:", out.shape)
