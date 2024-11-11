
###############################################################################
# Description:
# This script is for pre-processing seismic event waveform data
# CAP from 2013 to 2015
###############################################################################
import os
import subprocess
import logging
from obspy import read, read_inventory, UTCDateTime
import multiprocessing as mp

###############################################################################
# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_directories(*dirs):
    # Create directories if they don't exist
    for dir in dirs:
        os.makedirs(dir, exist_ok=True)

def process_mseed(event_dir, mseed, origin_time, evla, evlo, evdp, hour, mini, msec, error_resp_station):
    # Process a single MiniSEED file
    # Read the MiniSEED file, remove instrument response, and write processed data to SAC files
    
    # Read the MiniSEED file
    st = read(f"data/{event_dir}/{mseed}")
    head = st[0]
    
    station_id = f"{head.stats.network}.{head.stats.station}"
    logger.info(f"Event: {event_dir} ; Station: {station_id}")
    
    # Attempt to read the response file
    resp = f"response/{event_dir}/{station_id}.xml"
    try:
        inv = read_inventory(resp)
    except FileNotFoundError:
        logger.error(f"Can't find the response file for {station_id}, skipping")
        return f"{event_dir}: {station_id}.{head.stats.channel}", None
    
    if station_id in error_resp_station:
        logger.warning(f"{station_id} response file is wrong, skip")
        return None, None
    
    # Extract station coordinates
    stla, stlo, stel = inv.networks[0].stations[0].latitude, inv.networks[0].stations[0].longitude, inv.networks[0].stations[0].elevation
    
    # Pre-process the waveform
    st.detrend(type="demean")
    st.detrend(type="linear")
    st.taper(max_percentage=0.05)
    
    # Remove instrument response
    try:
        st.remove_response(inventory=inv, output="VEL", pre_filt=[0.5, 1.0, 20, 25])
    except Exception:
        logger.error(f"The response file for {station_id} is wrong, skipping")
        return None, f"{event_dir}: {station_id}.{head.stats.channel}"
    
    logger.info(f"Finished removing response for {station_id}")
    
    # Create SAC filename and write to file
    newsacname = f"{origin_time.year}.{origin_time.julday:03d}.{hour}.{mini}.{msec}.{station_id}..{head.stats.channel}.SAC"
    output_path = f"vel_data/{event_dir}/{newsacname}"
    st.write(output_path, format="SAC")
    
    # Update SAC headers
    update_sac_headers(output_path, evlo, evla, evdp, stlo, stla, stel, origin_time, hour, mini, msec)
    
    # Write local data if within 110 km
    local_st = read(output_path)
    if 10 <= local_st[0].stats.sac.dist <= 100:
        local_st.write(f"local_vel_data/{event_dir}/{newsacname}", format="SAC")
        if newsacname.endswith(".BHZ.SAC"):
            local_st.write(f"local_vel_data_BHZ/{event_dir}/{newsacname}", format="SAC")
    
    return None, None

def update_sac_headers(sac_file, evlo, evla, evdp, stlo, stla, stel, origin_time, hour, mini, msec):
    # Update SAC headers using SAC commands
    s = f"""
    wild echo off
    r {sac_file}
    ch LCALDA True
    ch evlo {evlo} evla {evla} evdp {evdp}
    ch stlo {stlo} stla {stla} stel {stel}
    ch t1 0.0 t2 0.0 t3 0.0 t4 0.0
    ch o gmt {origin_time.year} {origin_time.julday} {hour} {mini} {msec.split('.')[0]} {msec.split('.')[1]}
    wh
    q
    """
    subprocess.run(["sac"], input=s.encode(), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def process_event(event_line, ievent):
    event = event_line.split()

    event_dir = event[0]
    ymd = event[1]
    hour = event[2]
    mini = event[3]
    msec = event[4]
    evla = event[5]
    evlo = event[6]
    evdp = event[7]

    origin_time = UTCDateTime(f"{ymd} {hour}:{mini}:{msec}")
    
    logger.info(f"Pre-processing event: {event_dir}, number is {ievent}")
    logger.info(f"Origin time: {origin_time}")
    
    # Create event-specific directories
    create_directories(f"vel_data/{event_dir}", f"local_vel_data/{event_dir}", f"local_vel_data_BHZ/{event_dir}")
    
    # List MiniSEED files for the event
    os.system(f"ls data/{event_dir}/*.mseed > data/{event_dir}/mseedfiles.txt")
    
    with open(f"data/{event_dir}/mseedfiles.txt", "r") as mseedlf:
        mseedl = mseedlf.read().splitlines()
    
    error_resp_station = set()
    no_resp_station = []
    
    # Process each MiniSEED file
    for mseed in mseedl:
        no_resp, error_resp = process_mseed(event_dir, os.path.basename(mseed), origin_time, evla, evlo, evdp, hour, mini, msec, error_resp_station)
        if no_resp:
            no_resp_station.append(no_resp)
        if error_resp:
            error_resp_station.add(error_resp)
    
    return no_resp_station, list(error_resp_station)

def main():
    # Main function to process all seismic events
    
    # Create necessary directories
    create_directories("vel_data", "local_vel_data", "local_vel_data_BHZ")
    
    # Read the event catalog
    with open("catlog/KOERI_catlog.par", "r") as eplf:
        epls = eplf.read().splitlines()
    
    # Set up multiprocessing pool
    pool = mp.Pool(processes=mp.cpu_count())
    
    # Process events in parallel
    results = pool.starmap(process_event, [(event_line, i) for i, event_line in enumerate(epls, 1)])
    
    # Close the pool and wait for the work to finish
    pool.close()
    pool.join()
    
    # Aggregate results
    no_resp_station = []
    error_resp_station = set()
    for no_resp, error_resp in results:
        no_resp_station.extend(no_resp)
        error_resp_station.update(error_resp)

    # Write log file with stations that had issues
    with open("1_remove_resp_log.txt", "w") as log:
        log.write("--------------------------------------------------------------------------\n")
        log.write(f"{len(no_resp_station)} stations have no response file, listed as follows:\n")
        log.write("\n".join(no_resp_station) + "\n")
        log.write(f"{len(error_resp_station)} stations have wrong response file, listed as follows:\n")
        log.write("\n".join(error_resp_station) + "\n")

if __name__ == "__main__":
    main()
