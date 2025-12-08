# hflav-python-library

To run this project you firstly must create a virtual environment and install all the dependencies inside:

1. `python -m venv .venv`
2. `source .venv/bin/activate`

To install all the dependencies (including tests):
- `pip install ".[test]"`

Or if you want to edit the source code and see the changes instantly without installing the project (editable mode):
- `pip install -e ".[test]"`

And only dev dependencies:
- `pip install .`

Or:
- `pip install -e ".[dev]"`

## Documentation

If you want to check the full documentation of this project, go to the docs folder.

The class structure is as it can be seen in this picture:

![Class diagram](docs/Class%20Diagram.png)

## Configuring environment variables

These are all the environment variables available:

```env
# Cache configuration

HFLAV_CACHE_NAME="hflav_cache"
HFLAV_CACHE_EXPIRE_AFTER="86400"
```

If you want to use it in your code you should add these lines before anything:

```python
from dotenv import load_dotenv

load_dotenv()
```

## Tests

To launch all the tests:

- `pytest tests`

To launch a specific test:

- `pytest tests/test.py`

And to check the coverage:

- `pytest --cov=hflav_zenodo.module`

Where module is a specific module.

e.g: `pytest --cov=hflav_zenodo.source`