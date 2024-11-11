###############################################################################
# This is for plotting and visual inspection of the earthquake catlog download
# Central Anatolia from 2013 to 2015

###############################################################################
import pygmt
import pandas as pd

###############################################################################
pygmt.config(
    MAP_FRAME_TYPE="plain",
    MAP_GRID_PEN_PRIMARY="0.3p,dimgrey",
    MAP_ANNOT_OBLIQUE="30",
    MAP_ANNOT_OFFSET_PRIMARY="5p",
    MAP_ANNOT_OFFSET_SECONDARY="5p",
    FONT_ANNOT_PRIMARY="10p,5",
    FONT_LABEL="10p,28,black",
    MAP_FRAME_WIDTH="2p",
    MAP_FRAME_PEN="0.5p",
    MAP_TICK_LENGTH_PRIMARY="5p",
    MAP_LABEL_OFFSET="5.5p",
)

MINLAT = 36.50
MAXLAT = 40.00
MINLON = 32.00
MAXLON = 36.50

region_Ana = [MINLON, MAXLON, MINLAT, MAXLAT]
##########################################################################
# visualizing the events
meta_Ana_events = pd.read_csv(
    # "events/CAP_20130501_20150503_IRIS.csv",
    "catlog/KOERI_catlog.csv",
    delimiter=",",
    usecols=[1, 2, 3, 4],
)
#
Ana_event_new = pd.DataFrame(
    {
        "latitude": meta_Ana_events.iloc[:, 0],
        "longitude": meta_Ana_events.iloc[:, 1],
        "depth": meta_Ana_events.iloc[:, 2],
        "mag": meta_Ana_events.iloc[:, 3],
    }
)

# visualizing the events
meta_YB_station = pd.read_csv("fig/station.csv")

##############################################################################
# begin plot
fig = pygmt.Figure()

fig.basemap(region=region_Ana, projection="M15c", frame=["af", f"WsNe"])

fig.coast(
    land="gray55",
    water="gray70",
)

fig.grdimage(
    grid="@earth_relief_03s",
    shading=True,
    region=region_Ana,
    projection="M15c",
    cmap="earth",
)

fig.plot(
    data="fig/gem_active_faults.txt",
    style="qn1:+Lh+f6p",
    pen="0.5p,black",
)

pygmt.makecpt(
    cmap="batlow",
    series=[0, 20],
    # reverse=True,
)

# fig.plot(
#     x=Ana_event_new.longitude,
#     y=Ana_event_new.latitude,
#     size=0.035 * (2**Ana_event_new.mag),
#     fill=Ana_event_new.depth,
#     cmap=True,
#     style="cc",
#     pen="0.1p,black",
# )
fig.plot(
    x=meta_YB_station["Longitude"],
    y=meta_YB_station["Latitude"],
    style="i0.55c",
    fill="SNOW",
    pen="1.5p,black",
    # no_clip=True,
    
)

# fig.plot(
#     data="catlog/KOERI_catlog.par",
#     incols=[6, 5],
#     style="x0.15c",
#     pen="0.65p,red",
# )

# fig.plot(
#     data="fig/YB_CAP.csv",
#     incols=[1, 2],
#     style="i0.55c",
#     fill="SNOW",
#     pen="1.5p,black",
#     no_clip=True,
    
# )
# fig.plot(
#     data="fig/KO_CAP.csv",
#     incols=[1, 2],
#     style="i0.55c",
#     fill="blue",
#     pen="1.5p,black",
# )

fig.plot(
    data="fig/VHolo.csv",
    style="kvolcano/0.8c",
    fill="red",
    pen="1.5p,black",
)

# save figure
fig.savefig("fig/CAP_py.pdf", dpi=600, crop=True, show=True)
fig.savefig("fig/CAP_py.jpg", dpi=300, crop=True)
