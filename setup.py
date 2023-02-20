import os
import re
from setuptools import setup

DIRNAME = os.path.abspath(os.path.dirname(__file__))
rel = lambda *parts: os.path.join(DIRNAME, *parts)

README = open(rel('README.rst')).read()
CODE = open(rel('xspf2m3u.py')).read()
VERSION = re.search("__version__ = '([^']+)'", CODE).group(1)
NAME, DESCRIPTION = README.split('\n')[0].split(' - ')


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=README,
    url='https://github.com/xi/xspf2m3u',
    author='Tobias Bengfort',
    author_email='tobias.bengfort@posteo.de',
    py_modules=['xspf2m3u', 'm3u2xspf'],
    extras_require={
        'youtube': ['youtube_dl'],
        'mutagen': ['mutagen'],
    },
    entry_points={'console_scripts': [
        'xspf2m3u=xspf2m3u:main',
        'm3u2xspf=m3u2xspf:main',
    ]},
    license='GPLv2+')
