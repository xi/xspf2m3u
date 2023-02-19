xspf2m3u - simple XSPF to M3U conversion (and back)

Playlists tend to break whenever you reorder your music collection. The
`XSPF <http://www.xspf.org/xspf-v1.html>`_ format allows to specify songs by
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

  xspf2m3u:

    # convert in/example.xspf to m3u and outputs result to the console
    ./xspf2m3u.py example.xspf in

    # choose M3UEXT format as target 
    ./xspf2m3u.py example.xspf in -T M3UEXT

    # saves into 'out' directory as the 'example.m3u' file
    ./xspf2m3u.py example.xspf in -O out

  m3u2xspf:

     # convert in/example.m3u to xspf and outputs result to the console
     ./xspf2m3u.py in/example.m3u

    # saves into the 'example.xspf' file in the 'out' directory
    ./xspf2m3u.py example.xspf in -O out


