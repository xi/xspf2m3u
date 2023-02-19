#!/usr/bin/env python3

import os
import re
import sys
import argparse
import subprocess
from time import sleep
from xml.etree import ElementTree

try:
    import youtube_dl

    ydl = youtube_dl.YoutubeDL(params={
        'noplaylist': True,
        'quiet': True,
    })
    ydl_selector = ydl.build_format_selector('bestaudio/best')
except ImportError:
    youtube_dl = None

NS = '{http://xspf.org/ns/0/}'
EXTS = ['mp3', 'ogg', 'opus', 'mp4', 'm4a', 'wav', 'flac', 'wma']
CHARS = re.compile('[^a-z0-9 ]')

#Bump version 0.1.0 with example and M3UEXT support
__version__ = '0.1.0'


class DownloadPool(set):
    def log(self, s):
        print(s, file=sys.stderr, end='\r')

    def download(self, url, path):
        self.add(subprocess.Popen(['curl', url, '-s', '-o', path]))

    def poll(self):
        for p in list(self):
            if p.poll() is not None:
                self.remove(p)
        return len(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            while self.poll():
                self.log('{} downloads still active'.format(len(self)))
                sleep(5)
        else:
            for p in self:
                p.kill()


def iter_files(folder):
    for dirpath, dirnames, filenames in os.walk(folder):
        for filename in filenames:
            if filename.rsplit('.', 1)[-1] in EXTS:
                yield dirpath, filename


def simplify(s):
    s = s.lower()
    s = s.encode('ascii', errors='replace').decode('ascii')
    return CHARS.sub('', s)


def find_by_title(title, fields, files):
    for dirpath, filename in files:
        path = os.path.join(dirpath, filename)
        if (
            simplify(title) in simplify(filename)
            and all(simplify(o) in simplify(path) for o in fields)
        ):
            return path


def search_youtube(q):
    # result expires in 6h
    try:
        info = ydl.extract_info('ytsearch:' + ' '.join(q), download=False)
    except youtube_dl.utils.DownloadError:
        return None
    info = info['entries'][0]
    try:
        _format = next(ydl_selector({'formats': info['formats']}))
    except StopIteration:
        return None
    filename = '{}-{}.{}'.format(
        info['title'].replace('/', '_'),
        info['id'],
        _format['ext'],
    )
    return _format['url'], filename


def iter_tracks(src):
    root = ElementTree.parse(src).getroot()
    for e in root.iter(NS + 'track'):
        track = {}
        for tag in ['location', 'title', 'creator', 'album', 'annotation', 'image', 'duration']:
            field = e.find(NS + tag)
            if field is None:
                track[tag] = None
            else:
                track[tag] = field.text
        yield track


def hard_link(location, outdir):
    os.makedirs(outdir, exist_ok=True)
    filename = os.path.basename(location)
    path = os.path.join(outdir, filename)
    os.link(location, path)
    return path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('src')
    parser.add_argument('folder')
    parser.add_argument('-Y', '--youtube', action='store_true')
    parser.add_argument('-O', '--outdir')
    parser.add_argument('-T', '--target')
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
            
    target = "M3U"
    if 'target' in  args and args.target == "M3UEXT":
        target = 'M3UEXT'
        o.print("#EXTM3U")
            
    files = list(iter_files(args.folder))

    if args.outdir and not os.path.exists(args.outdir) :
        os.makedirs(args.outdir)

    if os.path.exists(args.folder):
        src=os.path.join(args.folder, args.src) 
    
    with DownloadPool() as pool:
        if os.path.exists(src) :
            for track in iter_tracks(src):
                location = track['location']

                if location is None:
                    context_key = ['creator', 'annotation']
                    context = [track[k] for k in context_key if track[k]]
                    location = find_by_title(track['title'], context, files)
                    if location and args.outdir:
                        location = hard_link(location, args.outdir)

                if location is None and args.youtube and youtube_dl:
                    url, filename = search_youtube([q for q in track.values() if q])
                    if args.outdir:
                        location = os.path.join(args.outdir, filename)
                        pool.download(url, location)
                    else:
                        location = url

                if location is None:
                    s = ' - '.join('{}: {}'.format(k, v) for k, v in track.items())
                    print('# Warning: ' + s)
                else:
                    if target == "M3U":
                        o.print(location)
                    if target == "M3UEXT":
                        duration = int(int(track['duration']) / 1000) #I am not sure about this
                        title = track['title']
                        logo = track['image']
                        o.print("#EXTINF:"+str(duration)+","+title+",logo="+logo)
                        o.print(location)
        else:
            print("Can not open file '"+ src +"'")



if __name__ == '__main__':
    try:
        #print(sys.argv)
        args = parse_args()
    except:
        if len(sys.argv) == 1 : #Use our example
            filename =  "example.xspf"  
            # seems not used and confusing imho
            indir  = "in"
            print('Using example: "chmod u+x xspf2m3u.py;./xspf2m3u.py  "'+filename+'" "'+indir+'" --target=M3UEXT" gives:')
            # Save into <outdir>/<filename>.m3u 
            outdir = "out"  
            # Choose your target
            #target="M3UEXT"
            target= "M3U"
            args = argparse.Namespace(src= filename, folder=indir, outdir=outdir, target=target)   
            sys.argv.append(filename)
        elif len(sys.argv) == 2 : #We assume the script is in the current directory
            filename = str(sys.argv[1])
            indir  = "."
            #We just dump the output content
            outdir = None
            # Choose your target
            target="M3UEXT"
           # target= "M3U"
            args = argparse.Namespace(src= filename, folder=indir, outdir=outdir, target="M3U")   
            sys.argv.append(filename)
   
    main(args)
            
    if  'outdir' in args and args.outdir is not None:
        filename = str(sys.argv[1]).replace(".xspf",".m3u")
        if args.target is None:
                target = "M3U"
        else:
                target = "M3UEXT"
        print("Saved "+target+" output into "+ os.path.join(args.outdir, filename))
        o.flush(os.path.join(args.outdir, filename))
    else:
        o.flush()
