###############################################################################
# Description:
# This is for mass downloading the seismic event waveform data
# Central Anatolia from 2013 to 2015

# FDSN web service: AUSPASS, BGR, EMSC, ETH, GEOFON, GEONET, GFZ, ICGC, IESDMC,
# INGV, IPGP, ISC, KNMI, KOERI, LMU, NCEDC, NIEP, NOA, RESIF, RESIFPH5, SCEDC,
# TEXNET, UIB-NORSAR, USGS, USP, ORFEUS, IRIS
###############################################################################
import obspy, os
from obspy.clients.fdsn.mass_downloader import (
    RectangularDomain,
    Restrictions,
    MassDownloader,
)

###############################################################################
MINLAT = 36.50
MAXLAT = 40.00
MINLON = 32.00
MAXLON = 36.50

pre_event_min = 0.5
aft_event_min = 2.5

if os.path.exists("data"):
    pass
else:
    os.mkdir("data")

if os.path.exists("response"):
    pass
else:
    os.mkdir("response")

###############################################################################
elf = open("catlog/KOERI_catlog.par", "r")
el = elf.read().splitlines()
elf.close()

i = 0
while i < len(el):
    event = el[i].split()

    event_dir = event[0]
    ymd = event[1]
    hour = event[2]
    mini = event[3]
    msec = event[4]

    lat = event[5]
    lon = event[6]
    depth = event[7]

    origin_time = obspy.UTCDateTime(ymd + " " + hour + ":" + mini + ":" + msec)

    # event_dir = ymd + '.' + hour.zfill(2) + '.' + mini.zfill(2)

    print("\033[1;34m Start downloading data for a new event \033[0m")
    print("event number: " + str(i) + "; " + event_dir)

    # Circular domain around the epicenter. This will download all data between
    # 70 and 90 degrees distance from the epicenter. This module also offers
    # rectangular and global domains. More complex domains can be defined by
    # inheriting from the Domain class.
    # domain = CircularDomain(latitude=37.52, longitude=143.04,
    #                         minradius=70.0, maxradius=90.0)

    # Rectangular domain
    domain = RectangularDomain(
        minlatitude=MINLAT,
        maxlatitude=MAXLAT,
        minlongitude=MINLON,
        maxlongitude=MAXLON,
    )

    restrictions = Restrictions(
        # Get data from 5 minutes before the event to one hour after the
        # event. This defines the temporal bounds of the waveform data.
        starttime=origin_time - pre_event_min * 60,
        endtime=origin_time + aft_event_min * 60,
        # You might not want to deal with gaps in the data. If this setting is
        # True, any trace with a gap/overlap will be discarded.
        reject_channels_with_gaps=True,
        # And you might only want waveforms that have data for at least 95 % of
        # the requested time span. Any trace that is shorter than 95 % of the
        # desired total duration will be discarded.
        minimum_length=0.90,
        network="YB",
        # No two stations should be closer than 10 km to each other. This is
        # useful to for example filter out stations that are part of different
        # networks but at the same physical station. Settings this option to
        # zero or None will disable that filtering.
        minimum_interstation_distance_in_m=10e2,
        # Only HH or BH channels. If a station has HH channels, those will be
        # downloaded, otherwise the BH. Nothing will be downloaded if it has
        # neither. You can add more/less patterns if you like.
        channel_priorities=["HH[ENZ]","BH[ENZ]"],
        # Location codes are arbitrary and there is no rule as to which
        # location is best. Same logic as for the previous setting.
        location_priorities=["", "00", "10"],
    )

    # No specified providers will result in all known ones being queried.

    mdl = MassDownloader(
        providers=[
            # "KOERI",
            "IRIS",
        ]
    )

    # The data will be downloaded to the ``./waveforms/`` and ``./stations/``
    # folders with automatically chosen file names.
    mdl.download(
        domain,
        restrictions,
        mseed_storage="data/" + event_dir,
        stationxml_storage="response/" + event_dir,
    )

    i = i + 1
