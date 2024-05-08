# datasette-pins

[![PyPI](https://img.shields.io/pypi/v/datasette-pins.svg)](https://pypi.org/project/datasette-pins/)
[![Changelog](https://img.shields.io/github/v/release/datasette/datasette-pins?include_prereleases&label=changelog)](https://github.com/datasette/datasette-pins/releases)
[![Tests](https://github.com/datasette/datasette-pins/actions/workflows/test.yml/badge.svg)](https://github.com/datasette/datasette-pins/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/datasette/datasette-pins/blob/main/LICENSE)

Pin databases, tables, queries, and more to the Datasette homepage!

<img src="https://datasette-cloud-assets.s3.amazonaws.com/blog/2024/datasette-pins/hero.png"/>

## Installation

`datasette-pins` requires a recent 1.0 alpha version of Datasette to work.

```bash
pip install datasette>=1.0a13
```

Afterwards, install this plugin in the same environment as Datasette.

```bash
datasette install datasette-pins
```

## Usage

`datasette-pins` has two permissions `datasette-pins-write` and
`datasette-pins-read`. Actors with the `datasette-pins-write` permissions can
pin and reorder items, while actors with `datasette-pins-read` permissions can
only view pinned items.

Here's an example
[`datasette.yaml` file](https://docs.datasette.io/en/latest/configuration.html#datasette-yaml-reference)
where all actors can view pins, but only the `root` actor can pin items:

```yaml
permissions:
  datasette-pins-read:
    id: "*"
    unauthenticated: true
  datasette-pins-write:
    id: "root"
```

Once logged in, the `root` use will see new pin/unpin option under the database,
table, and query actions menu:

<img src="https://datasette-cloud-assets.s3.amazonaws.com/blog/2024/datasette-pins/table-example.png"/>

## Development

To set up this plugin locally, first checkout the code. Then create a new
virtual environment:

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
