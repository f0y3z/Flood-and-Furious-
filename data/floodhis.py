import ee
import pandas as pd

ee.Authenticate()                          # first run only: opens a browser
ee.Initialize(project="floodguard-ai-511911")   # put your Cloud project ID here

gfd = ee.ImageCollection("GLOBAL_FLOOD_DB/MODIS_EVENTS/V1")

# Rough box around Sylhet District (west, south, east, north); verify on a map
SYLHET = ee.Geometry.Rectangle([91.5, 24.5, 92.5, 25.3])
events = gfd.filterBounds(SYLHET)
print("Events whose footprint touches the box:", events.size().getInfo())

# Show which properties exist on one event (to catch any naming surprises)
print(ee.Image(events.first()).propertyNames().getInfo())

def summarize(img):
    flooded = (img.select("flooded")
               .updateMask(img.select("jrc_perm_water").Not())   # drop permanent water
               .unmask(0))
    frac = flooded.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=SYLHET,
        scale=250, maxPixels=1e9).get("flooded")
    return ee.Feature(None, {
        "event_id":  img.get("id"),
        "start":     ee.Date(img.get("system:time_start")).format("YYYY-MM-dd"),
        "end":       ee.Date(img.get("system:time_end")).format("YYYY-MM-dd"),
        "country":   img.get("dfo_country"),
        "displaced": img.get("dfo_displaced"),
        "severity":  img.get("dfo_severity"),
        "cause":     img.get("dfo_main_cause"),
        "flooded_frac_in_box": frac,
    })

fc = ee.FeatureCollection(events.map(summarize)).getInfo()
df = pd.DataFrame([f["properties"] for f in fc["features"]])
df = df.sort_values("start")
df.to_csv("sylhet_flood_events.csv", index=False)
print(df.to_string())
