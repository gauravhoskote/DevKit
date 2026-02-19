# MyCLI

A sample CLI tool template built with [Click](https://click.palletsprojects.com/).

## Requirements

- Python 3.8+

## Installation

```bash
pip install -e .
```

## Usage

### Top-level help

```bash
mycli --help
```

### Commands

#### `process`

Process an input file.

```bash
mycli process --input path/to/file.txt
```

With verbose output:

```bash
mycli process --input path/to/file.txt --verbose
```

#### `status`

Show system status.

```bash
mycli status
```

## Running without installing

```bash
python -m mycli --help
python -m mycli process --input path/to/file.txt
python -m mycli status
```
