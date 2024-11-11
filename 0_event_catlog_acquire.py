###############################################################################  
# Description:  
# This is for acquiring the seismic event catalog for Central Anatolia  
# from 2013 to 2015  
###############################################################################  

from obspy.clients.fdsn import Client  
import pandas as pd  
import csv  
from datetime import datetime, timedelta  
import re  
import time  
from dateutil.relativedelta import relativedelta  

###############################################################################  

class Event:  
    # Define an Event class to hold earthquake event catalog details  
    def __init__(self, time, name, ymd, year, nsd, h, m, s, lat, lon, dep, mb):  
        self.time = time  
        self.name = name  
        self.ymd = ymd  
        self.year = year  
        self.nsd = nsd  # Day of the year  
        self.h = h  
        self.m = m  
        self.s = s  
        self.lat = lat  
        self.lon = lon  
        self.dep = dep  
        self.mb = mb  

    def __repr__(self):  
        # Representation of the Event object for debugging  
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

def fetch_events(client, minlat, maxlat, minlon, maxlon, stime, etime):  
    # Fetch seismic events from the FDSN web services  
    return client.get_events(  
        minlatitude=minlat,  
        maxlatitude=maxlat,  
        minlongitude=minlon,  
        maxlongitude=maxlon,  
        starttime=stime,  
        endtime=etime,  
        minmagnitude=2.1,  # Minimum magnitude for events  
        maxmagnitude=3.5,  # Maximum magnitude for events  
        maxdepth=30.0,  # Maximum depth for events in km  
    )  

def save_events_to_csv(events_list, csv_file):  
    # Save event details to a CSV file  
    event_info = []  
    for events in events_list:  
        for event in events:  
            origin = event.origins[0]  # Get the first origin (location) of the event  
            magnitude = event.magnitudes[0]  # Get the first magnitude  
            event_info.append(  
                [  
                    origin.time,  
                    origin.latitude,  
                    origin.longitude,  
                    origin.depth / 1000,  # Depth in km  
                    magnitude.mag,  
                    magnitude.magnitude_type,  # Type of magnitude (mb, Mw, etc.)  
                ]  
            )  
    # Create a DataFrame and save it as CSV  
    df = pd.DataFrame(  
        event_info,  
        columns=[  
            "Time",  
            "Latitude",  
            "Longitude",  
            "Depth",  
            "Magnitude",  
            "Magnitude_type",  
        ],  
    )  
    df.to_csv(csv_file, index=False)  # Save DataFrame to a CSV file without indices  

def convert_csv_to_custom_format(input_file, output_file):  
    # Convert the CSV file to a custom output format with correct time filtering  
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

    # Sort events chronologically  
    events.sort(key=lambda x: x[0])  

    last_kept_time = None  
    for time_obj, row in events:  
        if last_kept_time is None or (time_obj - last_kept_time) >= timedelta(minutes=20):  
            time_str, lat, lon, depth, magnitude, mag_type = row  
            new_time_str = time_obj.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  
            # This my custom catlog format following the our group tradition  
            # Change and replace the placeholders if you want  
            output_row = [  
                "xxxxx",  # Placeholder for the first column  
                new_time_str,  # Formatted time  
                lat,  
                lon,  
                depth,  
                "xxxx",  # Placeholder  
                "yyyyy",  # Placeholder  
                mag_type,  
                magnitude,  
                " ",  # Placeholder  
            ]  
            data.append((time_obj, output_row))  
            last_kept_time = time_obj  

    # Sort the kept data in reverse chronological order  
    data.sort(key=lambda x: x[0], reverse=True)  

    with open(output_file, "w", newline="", encoding="utf-8") as outfile:  
        csvwriter = csv.writer(outfile)  
        for _, output_row in data:  
            csvwriter.writerow(output_row)  # Write formatted rows to the output file  

def parse_custom_format(input_file, output_file):  
    # Parse the custom formatted input file and save it to a new output file  
    # This my custom catlog format following the our group tradition  
    # Change and replace the placeholders if you want  
    with open(input_file, "r") as el:  
        evps = el.read().splitlines()  

    event_tuples = []  
    for evp in evps:  
        parameters = evp.split(",")  
        t = re.findall("\d+", parameters[1])  # Extract numerical values from the time string  
        ymd = t[0] + t[1] + t[2]  # Create a string YYYYMMDD  
        h = t[3]  # Hour  
        m = t[4]  # Minute  
        s = t[5] + "." + t[6]  # Second with fractions  
        edir = ymd + "." + h + "." + m  # Create directory-like naming  
        timeArray = time.strptime(ymd + "." + h + m, "%Y%m%d.%H%M")  # Convert to time struct  
        year = t[0]  # Year  
        nsd = timeArray.tm_yday  # Day of the year  
        evtime = int(time.mktime(timeArray))  # Convert time struct to timestamp  
        lat = parameters[2]  
        lon = parameters[3]  
        dep = parameters[4]  
        mb = parameters[8]  
        event_tuples.append(  
            Event(evtime, edir, ymd, year, nsd, h, m, s, lat, lon, dep, mb)  
        )  

    sort_event_tuples = sorted(  
        event_tuples, key=lambda event: int(event.time), reverse=True  
    )  # Sort by event time  

    with open(output_file, "w") as out:  
        for event in sort_event_tuples:  
            # Write each event to the output file in the specified format  
            # This my custom catlog format following the our group tradition  
            # Change and replace the placeholders if you want  
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

def main():  
    # Main function to execute the workflow  
    client = Client("KOERI")  
    # Connect to the IRIS FDSN service  
    # "USGS" or "ISC" or "IRIS" or "EMSC"  
    # Define geographic boundaries  
    MINLAT = 37.00  
    MAXLAT = 39.00  
    MINLON = 33.00  
    MAXLON = 36.00  

    # Define event time range  
    start_date = datetime(2013, 5, 20)  
    end_date = datetime(2015, 5, 10)  

    current_date = start_date  
    all_events = []  

    while current_date < end_date:  
        next_month = current_date + relativedelta(months=1)  
        STIME = current_date.strftime("%Y-%m-%d %H:%M:%S")  
        ETIME = next_month.strftime("%Y-%m-%d %H:%M:%S")  

        events = fetch_events(client, MINLAT, MAXLAT, MINLON, MAXLON, STIME, ETIME)  
        all_events.append(events)  

        current_date = next_month  

    # Output paths  
    output_csv = "events/CAP_20130501_20150503_IRIS.csv"  
    output_txt = "events/CAP_IRIS_catlog.txt"  
    output_par = "events/CAP_IRIS_catlog.par"  

    save_events_to_csv(all_events, output_csv)  
    convert_csv_to_custom_format(output_csv, output_txt)  
    parse_custom_format(output_txt, output_par)  

if __name__ == "__main__":  
    main()  # Execute main function when the script is run