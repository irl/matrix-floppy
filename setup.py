from os import path

from setuptools import find_packages
from setuptools import setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    install_requires = f.read().splitlines()

setup(
    name="matrix-floppy",
    version="0.1a1",
    packages=find_packages(exclude=['docs']),
    scripts=["matrix-floppy.py"],
    install_requires=install_requires,
    author="Iain Learmonth",
    author_email="iain@learmonth.me",
    description="Save your Matrix history.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="matrix history archive",
    url="https://github.com/irl/matrix-floppy",
    classifiers=["License :: OSI Approved :: BSD License"]
)
