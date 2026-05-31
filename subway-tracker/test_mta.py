# Quick check: can we pull live F-train arrivals at Delancey St-Essex St,
# split into uptown (N, toward Queens) and downtown (S, toward Brooklyn)?
# Uses the feed's own generated-time as "now" so it works in any Mac timezone.
from nyct_gtfs import NYCTFeed

feed = NYCTFeed("F")
ref = feed.last_generated
print("feed generated:", ref)
print("num trips:", len(feed.trips))

up, down = [], []
matched = set()
for t in feed.trips:
    if getattr(t, "route_id", None) != "F":
        continue
    direction = getattr(t, "direction", "?")
    for stu in t.stop_time_updates:
        sid = getattr(stu, "stop_id", "") or ""
        name = getattr(stu, "stop_name", "") or ""
        if "delancey" in name.lower() or sid.startswith("F15"):
            matched.add((sid, name))
            arr = getattr(stu, "arrival", None)
            if arr is None:
                continue
            mins = (arr - ref).total_seconds() / 60.0
            if mins < -1:
                continue
            (up if direction == "N" else down).append(round(mins, 1))

print("matched Delancey stops:", matched)
up.sort()
down.sort()
print("UPTOWN (N, toward Queens) next mins:", up[:6])
print("DOWNTOWN (S, toward Brooklyn) next mins:", down[:6])

if not matched:
    print("NO DELANCEY MATCH - sample F stops follow:")
    cnt = 0
    for t in feed.trips:
        if getattr(t, "route_id", None) != "F":
            continue
        for stu in t.stop_time_updates[:3]:
            print("  ", getattr(stu, "stop_id", ""), "|",
                  getattr(stu, "stop_name", ""))
            cnt += 1
        if cnt > 12:
            break
