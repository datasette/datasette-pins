# datasette-pins

[![PyPI](https://img.shields.io/pypi/v/datasette-pins.svg)](https://pypi.org/project/datasette-pins/)
[![Changelog](https://img.shields.io/github/v/release/datasette/datasette-pins?include_prereleases&label=changelog)](https://github.com/datasette/datasette-pins/releases)
[![Tests](https://github.com/datasette/datasette-pins/actions/workflows/test.yml/badge.svg)](https://github.com/datasette/datasette-pins/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/datasette/datasette-pins/blob/main/LICENSE)

Pin databases, tables, and other items to the Datasette homepage

## Installation

Install this plugin in the same environment as Datasette.
```bash
datasette install datasette-pins
```
## Usage

Usage instructions go here.

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:
```bash
cd datasette-pins
python3 -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
pip install -e '.[test]'
```
To run the tests:
```bash
pytest
```
