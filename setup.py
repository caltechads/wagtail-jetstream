from setuptools import setup

setup(
    name='wagtail-jetstream',
    version='2.2.0',
    description='A set of complex layout blocks for use in Wagtail Streamfields.',
    url='https://github.com/caltechads/wagtail-jetstream',
    author='Caltech ADS',
    author_email='imss-ads@caltech.edu',
    license='GPL-3.0',
    install_requires=['django-bleach>=0.3.0'],
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Programming Language :: Python",
        "Programming Language :: Python 2.7",
        "Programming Language :: Python 3.6",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)
