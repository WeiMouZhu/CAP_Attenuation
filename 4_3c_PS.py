###############################################################################
# Description:
# This script sets the theoretical P and S wave arrival times for SAC files.
# It prepares SAC files for further AI-based picking methods like PhaseNet.
# It specifically handles BHZ, BHN, and BHE components.
###############################################################################
import os
import glob
import subprocess
import shutil
import csv
import re
import datetime
###############################################################################
def parse_sac_filename(filename):
    pattern = r'(\d{4}\.\d{3}\.\d{2}\.\d{2}\.\d{2}\.\d{3})\.([^.]+)\.([^.]+)\.\.(BH[ZNE])\.SAC'
    match = re.match(pattern, filename)
    if match:
        timestamp, network, station, channel = match.groups()
        return timestamp, network, station, channel
    return None

def process_events(base_dir, cap_sac_dir):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    with open(os.path.join(script_dir, "log", "KOERI_catlog_updated.par"), "r") as elf:
        event_lines = elf.read().splitlines()

    os.makedirs(cap_sac_dir, exist_ok=True)

    processed_stations = set()

    for line in event_lines:
        event = line.split()
        event_dir = event[0]

        event_path = os.path.join(base_dir, event_dir)
        if not os.path.isdir(event_path):
            print(f"The records of {event_dir} have been deleted or do not exist, skipping.")
            continue

        sac_files = glob.glob(os.path.join(event_path, "*.SAC"))
        if not sac_files:
            print(f"No SAC files found in {event_dir}, skipping.")
            continue

        try:
            subprocess.run(
                ["taup", "setsac", "-mod", "prem", "-evdpkm", "-ph", "P-1,S-2"] + sac_files,
                check=True
            )
            print(f"Processed SAC files in {event_dir}.")
        except subprocess.CalledProcessError as e:
            print(f"Error processing SAC files in {event_dir}: {e}")

        station_files = {}
        for sac_file in sac_files:
            parsed = parse_sac_filename(os.path.basename(sac_file))
            if parsed:
                timestamp, network, station, channel = parsed
                if channel in ['BHZ', 'BHN', 'BHE']:
                    key = f"{timestamp}.{network}.{station}"
                    if key not in station_files:
                        station_files[key] = []
                    station_files[key].append((sac_file, channel))

        for key, files in station_files.items():
            if len(files) == 3 and set(channel for _, channel in files) == {'BHZ', 'BHN', 'BHE'}:
                for sac_file, _ in files:
                    dest_path = os.path.join(cap_sac_dir, os.path.basename(sac_file))
                    shutil.copy2(sac_file, dest_path)
                    print(f"Copied: {os.path.basename(sac_file)}")
                processed_stations.add(f"{key}.BH*")
            else:
                print(f"Station {key} does not have all three components (BHZ, BHN, BHE), skipping.")

    return processed_stations

def rename_sac_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".SAC"):
            old_path = os.path.join(directory, filename)
            parts = filename.split('.')
            year = parts[0]
            day_of_year = parts[1]
            hour = parts[2]
            minute = parts[3]
            second = parts[4]
            network = parts[6]
            station = parts[7]
            channel = parts[9]

            date = datetime.datetime(int(year), 1, 1) + datetime.timedelta(days=int(day_of_year) - 1)

            new_filename = f"{network}.{station}.{date.strftime('%Y-%m-%d')}T{hour}:{minute}.{channel}.SAC"
            new_path = os.path.join(directory, new_filename)

            os.rename(old_path, new_path)
            print(f"Renamed: {filename} -> {new_filename}")

def write_filenames_to_csv(folder_path, output_csv):  
    if not os.path.exists(folder_path):  
        print(f"Error: Folder '{folder_path}' does not exist.")  
        return  

    files = [f for f in os.listdir(folder_path) if f.endswith('.SAC')]  
    unique_station_files = set()  

    for file in files:  
        match = re.match(r'(.+)\.BH[ENZ]\.SAC$', file)  
        if match:  
            main_part = match.group(1)  
            station_file = f"{main_part}.BH*"  
            unique_station_files.add(station_file) 

    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['fname'])
        for station_file in sorted(unique_station_files):
            writer.writerow([station_file])

    print(f"Station filenames have been written to '{output_csv}'.")

def run_phasenet(data_list, data_dir, result_dir):
    command = [
        "python", "phasenet/predict.py",
        "--model=model/190703-214543",
        f"--data_list={data_list}",
        f"--data_dir={data_dir}",
        "--format=sac",
        "--batch_size=1",
        "--plot_figure",
        f"--result_dir={result_dir}"
    ]
    subprocess.run(command, check=True)

def main():
    base_directory = os.path.abspath("local_vel_data")  # Base path for event directories
    cap_sac_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CAP_4Pick_3SAC")
    output_csv = os.path.join(cap_sac_dir, "sac.csv")
    result_dir = os.path.join(cap_sac_dir, "results")

    # Step 1: Process events and copy SAC files
    processed_stations = process_events(base_directory, cap_sac_dir)

    # Step 2: Rename SAC files in place
    rename_sac_files(cap_sac_dir)

    # Step 3: Generate CSV file
    write_filenames_to_csv(cap_sac_dir, output_csv)

    # Step 4: Run phasenet
    run_phasenet(output_csv, cap_sac_dir, result_dir)

    print(f"Processed {len(processed_stations)} stations")
    print(f"Created {output_csv} with the list of processed stations")
    print(f"PhaseNet results are in {result_dir}")

if __name__ == "__main__":
    main()
