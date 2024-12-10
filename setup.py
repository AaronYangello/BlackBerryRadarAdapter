# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='bb_label_adapter',
    version='0.1.0',
    description='BlackBerry Radar Label adapter',
    long_description=readme,
    author='Aaron Yangello',
    author_email='ayangello@gmail.com',
    url='https://github.com/AaronYangello/BlackBerryRadarAdapter',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

