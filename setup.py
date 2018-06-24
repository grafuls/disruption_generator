#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Note: To use the 'upload' functionality of this file, you must:
#   $ pip install twine

"""The setup script."""

import io
import os
import sys

from setuptools import setup, find_packages, Command

# Package meta-data.
NAME = "disruption_generator"
DESCRIPTION = "Providing an extendable and easy to use tool for developers and QE to ensure the highest resilience " \
              "of their products by disrupting normal workflows during test execution."
URL = "https://github.com/grafuls/disruption_generator"
EMAIL = "grafuls@gmail.com"
AUTHOR = "Gonzalo Rafuls"
REQUIRES_PYTHON = ">=3.4.0"
VERSION = "0.1.0"

# What packages are required for this module to be executed?
REQUIRED = [
    "click>=6.0",
    "python-rrmngmnt",
    "configparser",
    "pyyaml",
    "jinja2",
    "requests",
    "six",
    "zope.interface",
    "attrs",
    "asyncio",
    'asyncssh',
]

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
with io.open(os.path.join(here, "README.rst"), encoding="utf-8") as f:
    README = "\n" + f.read()
with io.open(os.path.join(here, "HISTORY.rst"), encoding="utf-8") as f:
    HISTORY = "\n" + f.read()


SETUP_REQUIREMENTS = ["pytest-runner"]

TEST_REQUIREMENTS = ["pytest", "pytest-asyncio"]


class UploadCommand(Command):
    """Support setup.py upload."""

    description = "Build and publish the package."
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print("\033[1m{0}\033[0m".format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status("Removing previous builds…")
            rmtree(os.path.join(here, "dist"))
        except OSError:
            pass

        self.status("Building Source and Wheel (universal) distribution…")
        os.system("{0} setup.py sdist bdist_wheel --universal".format(sys.executable))

        self.status("Uploading the package to PyPi via Twine…")
        os.system("twine upload dist/*")

        self.status("Pushing git tags…")
        os.system("git tag v{0}".format(about["__version__"]))
        os.system("git push --tags")

        sys.exit()


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=README + "\n\n" + HISTORY,
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=("tests",)),
    install_requires=REQUIRED,
    include_package_data=True,
    license="Apache Software License 2.0",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    entry_points={
        "console_scripts": ["disruption_generator=disruption_generator.cli:main"]
    },
    keywords="disruption_generator",
    setup_requires=SETUP_REQUIREMENTS,
    test_suite="tests",
    tests_require=TEST_REQUIREMENTS,
    zip_safe=False,
    cmdclass={"upload": UploadCommand},
)
