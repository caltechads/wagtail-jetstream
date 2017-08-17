import os
from setuptools import setup

from jetstream import __version__

setup(
    name='wagtail-jetstream',
    version=__version__,
    description='A set of complex layout blocks for use in Wagtail Streamfields',
    url='https://github.com/caltechads/wagtail-jetstream',
    author='Caltech ADS',
    author_email='imss-ads@caltech.edu',
    license='GPL-3.0',
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Programming Language :: Python",
        "Programming Language :: Python 2.7",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)
