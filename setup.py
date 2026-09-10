#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" The setup script."""

from setuptools import find_packages, setup


with open('README.rst', 'rb') as readme_file:
    readme = readme_file.read().decode('utf-8')


setup(
    author='Günther Jena',
    author_email='guenther@jena.at',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
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
    python_requires='>=3.10',
    url='https://github.com/semiversus/python-broqer',
    zip_safe=False,
)
