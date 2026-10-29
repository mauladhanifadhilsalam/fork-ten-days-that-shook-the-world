"""The 3D map's extent, projection and 1917 rules, shared by the map tools.

The detailed city (buildings, streets, water) covers CORE: from the Petrograd Side yunker schools
to Smolny, and from the Finland Station down to the Nicolai and Tsarskoye Selo stations. Reed's
places outside it (the southern gates and stations, the front, Moscow) are pins on the plain.
"""
import math

CORE = (30.280, 59.917, 30.405, 59.962)   # W, S, E, N
ORIGIN = (59.9395, 30.3425)               # local (0, 0), lat/lon: the middle of the core
KX = math.cos(math.radians(ORIGIN[0])) * 111320.0
KY = 110574.0 + (111694.0 - 110574.0) * (ORIGIN[0] / 90.0)


def P(lat, lon):
    """lat/lon -> local metres (x east, y north) around ORIGIN."""
    return ((lon - ORIGIN[1]) * KX, (lat - ORIGIN[0]) * KY)


def extent_m():
    w, s, e, n = CORE
    x0, y0 = P(s, w)
    x1, y1 = P(n, e)
    return x0, y0, x1, y1


# Bridges standing today that did not stand in November 1917. Matched against the names of ways
# and relations tagged as bridges only, so streets that merely share a name are kept.
NOT_IN_1917 = ('Бетанкура', 'Александра Невского')
