
import pandas as pd
from datetime import datetime, timedelta
import csv
import time
import re
from shapely.geometry import Point, Polygon

# Read the data using tab as the separator
data = pd.read_csv(
    # "catlog/20130520_20150510_KOERI.txt",
    "catlog/2013520_2015510_1_3.5_23_163.txt", 
    sep="\t", 
    header=0,
    usecols=['Date', 'Origin Time', 'Latitude', 'Longitude', 'Depth(km)', 'ML']
)

# Rename columns for consistency
data.columns = ["Date", "Time", "Latitude", "Longitude", "Depth", "Magnitude"]

# Merge date and time, then format to ISO 8601
data["Time"] = pd.to_datetime(data["Date"] + " " + data["Time"]).dt.strftime(
    "%Y-%m-%dT%H:%M:%S.%fZ"
)

# Select and rename required columns
CAP_seismicity_updated = data[
    ["Time", "Latitude", "Longitude", "Depth", "Magnitude"]
].copy()
CAP_seismicity_updated["Magnitude_type"] = "ML"  # Add Magnitude type column and set to "ML"

# Define the polygon for the area of interest
# Replace these coordinates with the actual polygon coordinates for your area of interest
polygon_coords = [
    (32.00, 38.50), (33.5, 39.75), (35.75, 39.75), (36.50, 38.00), (36.50, 37.0), (34.75, 37.0), (34.0, 36.70), (33.5, 36.70), (32.25, 37.50), (32.00, 38.50)
]



polygon = Polygon(polygon_coords)

# Function to check if a point is within the polygon
def is_within_polygon(row):
    point = Point(row['Longitude'], row['Latitude'])
    return polygon.contains(point)

# Filter data based on geographical, magnitude, and depth criteria
CAP_seismicity_updated = CAP_seismicity_updated[
    (CAP_seismicity_updated.apply(is_within_polygon, axis=1)) &
    (CAP_seismicity_updated["Magnitude"] >= 1.5) &
    (CAP_seismicity_updated["Magnitude"] <= 3.5) &
    (CAP_seismicity_updated["Depth"] <= 20.0) &
    (CAP_seismicity_updated["Depth"] > 1.0) &
    (CAP_seismicity_updated["Depth"] != 5.0) 
]

# Sort by time
CAP_seismicity_updated = CAP_seismicity_updated.sort_values(by="Time")

class Event:
    def __init__(self, time, name, ymd, year, nsd, h, m, s, lat, lon, dep, mb):
        self.time = time
        self.name = name
        self.ymd = ymd
        self.year = year
        self.nsd = nsd
        self.h = h
        self.m = m
        self.s = s
        self.lat = lat
        self.lon = lon
        self.dep = dep
        self.mb = mb

    def __repr__(self):
        return repr(
            (
                self.time,
                self.name,
                self.ymd,
                self.year,
                self.nsd,
                self.h,
                self.m,
                self.s,
                self.lat,
                self.lon,
                self.dep,
                self.mb,
            )
        )

def convert_csv_to_custom_format(input_file, output_file):
    data = []
    with open(input_file, "r", encoding="utf-8") as infile:
        csvreader = csv.reader(infile)
        next(csvreader)  # Skip headers in the input CSV

        events = []
        for row in csvreader:
            time_str, lat, lon, depth, magnitude, mag_type = row
            try:
                time_obj = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                events.append((time_obj, row))
            except ValueError as e:
                print(f"Time format error for row: {row}, error: {e}")
                continue

    events.sort(key=lambda x: x[0])

    last_kept_time = None
    for time_obj, row in events:
        if last_kept_time is None or (time_obj - last_kept_time) >= timedelta(minutes=5):
            time_str, lat, lon, depth, magnitude, mag_type = row
            new_time_str = time_obj.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            output_row = [
                "xxxxx",
                new_time_str,
                lat,
                lon,
                depth,
                "xxxx",
                "yyyyy",
                mag_type,
                magnitude,
                " ",
            ]
            data.append((time_obj, output_row))
            last_kept_time = time_obj

    data.sort(key=lambda x: x[0], reverse=True)

    with open(output_file, "w", newline="", encoding="utf-8") as outfile:
        csvwriter = csv.writer(outfile)
        for _, output_row in data:
            csvwriter.writerow(output_row)

def parse_custom_format(input_file, output_file):
    with open(input_file, "r") as el:
        evps = el.read().splitlines()

    event_tuples = []
    for evp in evps:
        parameters = evp.split(",")
        t = re.findall("\d+", parameters[1])
        ymd = t[0] + t[1] + t[2]
        h = t[3]
        m = t[4]
        s = t[5] + "." + t[6]
        edir = ymd + "." + h + "." + m
        timeArray = time.strptime(ymd + "." + h + m, "%Y%m%d.%H%M")
        year = t[0]
        nsd = timeArray.tm_yday
        evtime = int(time.mktime(timeArray))
        lat = parameters[2]
        lon = parameters[3]
        dep = parameters[4]
        mb = parameters[8]
        event_tuples.append(
            Event(evtime, edir, ymd, year, nsd, h, m, s, lat, lon, dep, mb)
        )

    sort_event_tuples = sorted(
        event_tuples, key=lambda event: int(event.time), reverse=True
    )

    with open(output_file, "w") as out:
        for event in sort_event_tuples:
            out.write(
                "%-11s %-9s %-3s %-3s %-8s %-10s %-10s %-4s  8.4 25.6   %3s  ML\n"
                % (
                    event.name,
                    event.ymd,
                    event.h,
                    event.m,
                    event.s,
                    event.lat,
                    event.lon,
                    event.dep,
                    event.mb,
                )
            )

# Output paths
output_csv = "catlog/KOERI_catlog.csv"
output_txt = "catlog/KOERI_catlog.txt"
output_par = "catlog/KOERI_catlog.par"

# Save the final data as a CSV file, using comma as separator
CAP_seismicity_updated.to_csv(output_csv, index=False, sep=",")
convert_csv_to_custom_format(output_csv, output_txt)
parse_custom_format(output_txt, output_par)
print("Data processing completed.")
