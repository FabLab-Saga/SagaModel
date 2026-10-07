"""Sun position for the site, in compass terms and in model coordinates.

Model frame (from OSM + the floor plan): model +Y points to bearing 116 deg,
model +X to bearing 206 deg. Iceland is UTC+0 all year.
"""
import math
from datetime import datetime, timezone

LAT, LON = 64.142, -21.955
PLUS_Y_BEARING = 116.0


def solar_position(when_utc, lat=LAT, lon=LON):
    """Return (azimuth_deg clockwise from north, elevation_deg). NOAA approximation."""
    doy = when_utc.timetuple().tm_yday
    hour = when_utc.hour + when_utc.minute / 60 + when_utc.second / 3600
    g = 2 * math.pi / 365 * (doy - 1 + (hour - 12) / 24)
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                       - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    tst = hour * 60 + eqtime + 4 * lon
    ha = math.radians(tst / 4 - 180)
    phi = math.radians(lat)
    cos_zen = math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.cos(ha)
    zen = math.acos(max(-1.0, min(1.0, cos_zen)))
    az = math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(phi) - math.tan(decl) * math.cos(phi))) + 180
    return az % 360, 90 - math.degrees(zen)


def bearing_to_model(bearing_deg):
    """Unit horizontal vector (x, y) in model space for a compass bearing."""
    a = math.radians(bearing_deg - PLUS_Y_BEARING)
    return math.sin(a), math.cos(a)


def sun_vector(when_utc):
    """Unit vector from the scene towards the sun, in model coordinates."""
    az, el = solar_position(when_utc)
    x, y = bearing_to_model(az)
    ce = math.cos(math.radians(el))
    return (x * ce, y * ce, math.sin(math.radians(el))), az, el


def sky_angles(when_utc):
    """(sun_elevation, sun_rotation) in radians for Blender's Sky Texture.

    sun_rotation is measured clockwise from model +Y (verified with a panorama
    render against a marker placed along sun_vector).
    """
    (x, y, _), _az, el = sun_vector(when_utc)
    return math.radians(el), math.atan2(x, y)


if __name__ == "__main__":
    for h in (11, 13, 15, 17, 19):
        v, az, el = sun_vector(datetime(2026, 5, 15, h, tzinfo=timezone.utc))
        print(f"{h:02d}:00 az {az:6.1f} el {el:5.1f}  model {tuple(round(c, 3) for c in v)}")
