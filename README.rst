xspf2m3u - simple XSPF to M3U conversion

Playlists tend to break whenever you reorder your music collection. The
`XSPF <https://xspf.org/spec>`_ format allows to specify songs by
metadata rather than file location, so it theoretically solves that problem.
Unfortnately, most audio players do not support that format.

This script allows to convert XSPF to M3U by finding file locations that match
the given metadata. It is *not* a full content resolver. In fact, it is rather
dumb. It uses the following strategies:

-   If the input file specifies a location, use that.
-   If the path of a file on the local computer looks like it could match, use
    that.
-   If youtube-dl is installed, use it to search youtube. The resulting URL
    will expire after 6 hours.

Usage::

    xspf2m3u input.xspf /my/music > output.m3u

    if you need M3UEXT support, then

    xspf2m3u input.xspf /my/music --target M3UEXT > output.m3u
