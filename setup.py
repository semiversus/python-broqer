#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" The setup script."""

from setuptools import find_packages, setup


with open('README.rst', 'rb') as readme_file:
    readme = readme_file.read().decode('utf-8')


setup(
    author='Günther Jena',
    author_email='guenther@jena.at',
    use_scm_version={"write_to": "broqer/_version.py"},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description='Carefully crafted library to operate with continuous ' +
                'streams of data in a reactive style with publish/subscribe ' +
                'and broker functionality.',
    license='MIT license',
    long_description=readme,
    include_package_data=True,
    keywords='broker publisher subscriber reactive frp observable',
    name='broqer',
    packages=find_packages(include=['broqer*']),
    url='https://github.com/semiversus/python-broqer',
    zip_safe=False,
)
