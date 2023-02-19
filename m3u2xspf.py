#!/usr/bin/env python

import os
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
    #m3uext
    'image': 'image',
    'duration' : 'duration'
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

import re

def iter_lines(path):
    root = os.path.dirname(path)
    track= {}
    target = 'M3U'
    with open(sys.argv[1]) as fh:
        for line in fh:
            line = line.rstrip()
            if line.startswith('#EXTM3U'):
                 target = 'M3UEXT'   
            elif line.startswith('#EXTINF'):
                matches = re.compile('#EXTINF:(\d*),([^,]+),(?:logo=(.*))?', re.IGNORECASE).findall(line) 
                duration, title, logo =zip(matches[0])
                track= { 
                        'title' : title[0], 
                        'image' : logo[0],
                        'duration' : str(int(duration[0])*1000)
                        }
            elif line.startswith('#'):
                pass
            elif line.startswith('http'):
                if target == 'M3UEXT':
                    track['location'] = line
                else:
                    track={'location': line}
                yield track
            else:
                if not line.startswith('/'):
                    line = os.path.join(root, line)
                yield get_tags(line)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('src')
    parser.add_argument('-O', '--outdir')
    return parser.parse_args()

class OutputBuffer():
    output = []

    def print(self, line):
       self.output.append(line)

    def __str__(self):
        return "\n".join(self.output)
            
    def flush(self, file=''):
        content = str(self)
        if file == "":
            print(content)
        else:
            f = open(file, 'w')
            f.write(content)
            f.close()
   
o = OutputBuffer()   

def main(args):

    if os.path.exists(args.src) :

        o.print('<?xml version="1.0" ?>')
        o.print('<playlist version="1" xmlns="http://xspf.org/ns/0/">')
        o.print(' <trackList>')
        for entry in iter_lines(args.src):
            o.print('		<track>')
            for k, v in sorted(entry.items()):
                if k in KEYS:
                    o.print('			<{key}>{value}</{key}>'.format(
                        key=escape(KEYS[k]),
                        value=escape(unlist(v)),
                    ))
            o.print('		</track>')
        o.print('	</trackList>')
        o.print('</playlist>')

    else:
        print("Can not open file '"+args.src+"'")

if __name__ == '__main__':
    try:
        #print(sys.argv)
        args = parse_args()
    except:
        if len(sys.argv) == 1 : #Use our example
            filepath ="in/example.m3u"
            print('Using example: "chmod u+x m3u2xspf.py;./xspf2m3u.py in/example.m3u" gives:')
            args = argparse.Namespace(src=filepath)
            sys.argv.append(filepath)
    main(args)
    if  'outdir' in args and args.outdir is not None:
        filename =os.path.basename(str(sys.argv[1])).replace(".m3u",".xspf")
        print("Saved xspf output into "+ os.path.join(args.outdir, filename))
        o.flush(os.path.join(args.outdir, filename))
    else:
        o.flush()
        