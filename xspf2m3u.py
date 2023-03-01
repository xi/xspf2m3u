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

__version__ = '0.0.0'


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
        return None, None
    if not info['entries']:
        return None, None
    info = info['entries'][0]
    try:
        _format = next(ydl_selector({'formats': info['formats']}))
    except StopIteration:
        return None, None
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


def main():
    args = parse_args()

    target = "M3U"
    if 'target' in  args and args.target == "M3UEXT":
        target = 'M3UEXT'
        print("#EXTM3U")

    files = list(iter_files(args.folder))

    if args.outdir:
        os.makedirs(args.outdir)

    with DownloadPool() as pool:
        for track in iter_tracks(args.src):
            location = track['location']

            if location is None:
                context_key = ['creator', 'annotation']
                context = [track[k] for k in context_key if track[k]]
                location = find_by_title(track['title'], context, files)
                if location and args.outdir:
                    location = hard_link(location, args.outdir)

            if location is None and args.youtube and youtube_dl:
                url, filename = search_youtube(
                    [q for q in track.values() if q]
                )
                if url is None:
                    location = None
                elif args.outdir:
                    location = os.path.join(args.outdir, filename)
                    pool.download(url, location)
                else:
                    location = url

            if location is None:
                s = ' - '.join('{}: {}'.format(k, v) for k, v in track.items())
                print('# Warning: ' + s)
            else:
                 if target == "M3U":
                    print(location)
                 if target == "M3UEXT":
                    duration = int(track['duration'], 10) // 1000
                    title = track['title']
                    logo = track['image']
                    print("#EXTINF:{},{},logo={}"'{}: {}'.format(str(duration), title ,logo))
                    print(location)


if __name__ == '__main__':
    main()
