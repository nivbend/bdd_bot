"""Setuptools setup script for the package."""

from setuptools import setup

def _get_version():
    # pylint: disable=missing-docstring
    with open(".version") as version:
        return version.read().rstrip("\n")

setup(
    name = "bdd_bot",
    version = _get_version(),
    description = "An automatic BDD scenarios delivery system",
    url = "http://github.com/nivbend/bdd_bot",
    author = "Niv Ben-David",
    author_email = "nivbend@gmail.com",
    license = "MIT",
    packages = ["bddbot", ],
    install_requires = [
        "PyYAML",
    ],
    classifiers = [
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development",
        "Topic :: Software Development :: Testing",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ],
    keywords = [
        "testing",
        "test",
        "bdd",
        "behavior-driven developement"
        "behavior"
    ])
