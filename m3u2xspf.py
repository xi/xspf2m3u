import os
import re
import sys
import argparse
from xml.sax.saxutils import escape

try:
    import mutagen
except ImportError:
    mutagen = None

KEYS = {
    'location': 'location',
    'album': 'album',
    'artist': 'creator',
    'title': 'title',
    'duration': 'duration',
}


def unlist(s):
    return s if isinstance(s, str) else '; '.join(s)


def get_tags(path):
    if not mutagen or not os.path.exists(path):
        return {'location': path}
    data = mutagen.File(path, easy=True)
    if data:
        return data
    else:
        return {'location': path}


def parse_extinf(line):
    match = re.fullmatch(r'#EXTINF:([0-9]+),(.*)', line)
    extinf = {}
    if match:
        extinf['title'] = match[2].strip()
        if match[1] not in ['0', '-1']:
            extinf['duration'] = str(int(match[1], 10) * 1000)
    return extinf


def iter_lines(path):
    root = os.path.dirname(path)
    track = {}
    with open(sys.argv[1]) as fh:
        for line in fh:
            line = line.rstrip()
            if line.startswith('#'):
                if line.startswith('#EXTINF:'):
                    track = parse_extinf(line)
            else:
                if line.startswith('http'):
                    track['location'] = line
                elif line:
                    if not line.startswith('/'):
                        line = os.path.join(root, line)
                    track.update(get_tags(line))
                yield track
                track = {}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('src')
    return parser.parse_args()


def main():
    args = parse_args()

    print('<?xml version="1.0" ?>')
    print('<playlist version="1" xmlns="http://xspf.org/ns/0/">')
    print('  <trackList>')
    for entry in iter_lines(args.src):
        print('    <track>')
        for k, v in sorted(entry.items()):
            if k in KEYS:
                print('      <{key}>{value}</{key}>'.format(
                    key=escape(KEYS[k]),
                    value=escape(unlist(v)),
                ))
        print('    </track>')
    print('  </trackList>')
    print('</playlist>')


if __name__ == '__main__':
    main()
