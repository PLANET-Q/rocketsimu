# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='rocketsimu',
    version='0.1.0',
    description='6-dof High-power rocket simulator.',
    long_description=readme,
    author='Yusuke Yamamoto',
    author_email='motsulab@gmail.com',
    url='https://github.com/PLANET-Q/rocketsimu',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    install_requirements=['numpy', 'scipy', 'pandas', 'numpy-quaternion']
)
