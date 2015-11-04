#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name='formatstring',
    version='1.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'fmtstr_pattern_create = formatstring.pattern_create:main',
            'fmtstr_pattern_offset = formatstring.pattern_offset:main',
        ]
    },
    author='Maxime Arthaud',
    author_email='maxime@arthaud.me',
    description='Format string exploitation helper',
    license='MIT',
    keywords='format string security exploit payload vulnerability ctf',
    url='https://github.com/arthaud/formatstring',
    extras_require={
        'elf': 'pyelftools',
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Topic :: Security',
    ],
)
