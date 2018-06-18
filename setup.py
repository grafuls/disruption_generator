#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
        'Click>=6.0',
        'python-rrmngmnt',
        'configparser',
        'pyyaml',
        'jinja2',
        'requests',
]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="Gonzalo Rafuls",
    author_email='grafuls@gmail.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    description="Providing an extendable and easy to use tool for developers "
                "and QE to ensure the highest resilience of their products by "
                "disrupting normal workflows during test execution.",
    entry_points={
        'console_scripts': [
            'disruption_generator=disruption_generator.cli:main',
        ],
    },
    install_requires=requirements,
    license="Apache Software License 2.0",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='disruption_generator',
    name='disruption_generator',
    packages=find_packages(include=['disruption_generator']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/grafuls/disruption_generator',
    version='0.1.0',
    zip_safe=False,
)
