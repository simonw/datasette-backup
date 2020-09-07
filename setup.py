from setuptools import setup
import os

VERSION = "0.1"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="datasette-backup",
    description="Plugin adding backup options to Datasette",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/simonw/datasette-backup",
    project_urls={
        "Issues": "https://github.com/simonw/datasette-backup/issues",
        "CI": "https://github.com/simonw/datasette-backup/actions",
        "Changelog": "https://github.com/simonw/datasette-backup/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["datasette_backup"],
    entry_points={"datasette": ["backup = datasette_backup"]},
    install_requires=["datasette", "sqlite-dump>=0.1.1"],
    extras_require={"test": ["pytest", "pytest-asyncio", "httpx", "sqlite-utils"]},
    tests_require=["datasette-backup[test]"],
)
