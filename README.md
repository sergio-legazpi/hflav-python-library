# HFLAV FAIR Client

## Overview

The HFLAV FAIR Client is a Python library designed to facilitate access to and processing of HFLAV (Heavy Flavor Averaging Group) data from various sources, including Zenodo and GitLab repositories. The library provides a unified interface for querying, transforming, and visualizing physics data while adhering to FAIR (Findable, Accessible, Interoperable, Reusable) principles.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Install from source


1. `git clone ssh://git@gitlab.cern.ch:7999/hflav/shared/hflav-fair-client.git`
2. `cd hflav-fair-client`
3. `python -m venv .venv`
4. `source .venv/bin/activate`
5. `pip install .`

### Install in editable mode (for development)

```bash
pip install -e ".[dev]"
```

## Quick Start

Below are simple examples showing how to retrieve and work with results from an HFLAV Zenodo record.

### Example 1: Search for HFLAV records on Zenodo and load data

```python
from hflav_fair_client.filters.search_filters import QueryBuilder, SortOptions
from hflav_fair_client.services.service import Service

# Get the service
service = Service()

# Build a query to search for HFLAV records on Zenodo
query = (
    QueryBuilder()
    .with_text(field="title", value="HFLAV")
    .with_pagination(size=5, page=1)
    .order_by(field=SortOptions.MOSTRECENT)
    .build()
)

# Search Zenodo and automatically load the first matching data file
data = service.search_and_load_data_file(query=query)

# Access the loaded data (returned as a SimpleNamespace object)
print(data)
```

### Example 2: Load a specific record by ID

```python
from hflav_fair_client.services.service import Service

service = Service()

# Load a specific file from a known Zenodo record
data = service.load_data_file(
    record_id=12345,       # Replace with the actual Zenodo record ID
    filename="HFLAV.json", # Replace with the actual filename
)

# Access fields on the loaded data object
print(data)
```

### Example 3: Load a local data file and search within it

```python
from hflav_fair_client.services.service import Service
from hflav_fair_client.models.hflav_data_searching import HflavDataSearching, SearchOperators

service = Service()

# Load a local JSON data file (schema validation is optional)
data = service.load_local_data_file_from_path(
    file_path="HFLAV.json",
    schema_path="HFLAV.schema",
    validate=False,
)

# Search within the loaded data
searcher = HflavDataSearching(data)
results = searcher.get_data_object_from_key_and_value(
    object_name="groups",
    key_name="ndf",
    operator=SearchOperators.EQUALS,
    value=156,
)
print(results)
```

### Example 4: Combine multiple filters using merge

```python
from hflav_fair_client.filters.search_filters import (
    QueryBuilder,
    SortOptions,
    AndFilter,
    OrFilter,
    NotFilter,
)
from hflav_fair_client.services.service import Service
import datetime

service = Service()

# First query builder: filter by version number with NOT combinator
query1 = (
    QueryBuilder()
    .with_number(field="version", value=2, operator=">=")
    .apply_combinator(NotFilter)
)

# Second query builder: filter by title and date range with OR combinator
query2 = (
    QueryBuilder()
    .with_text(field="title", value="HFLAV")
    .with_date_range(
        field="created",
        start_date=datetime.datetime(2022, 1, 1),
        end_date=datetime.datetime(2025, 12, 31),
    )
    .apply_combinator(OrFilter)
)

# Create a new query builder and merge both previous queries
combined_query = (
    QueryBuilder()
    .with_pagination(size=5, page=1)
    .order_by(field=SortOptions.MOSTRECENT)
    .merge_filters(query1)
    .merge_filters(query2)
    .build()  # Uses AndFilter by default to combine the merged filters
)

# Use the combined query to search and load data
data = service.search_and_load_data_file(query=combined_query)
print(data)

```

## Use Cases

This library supports several key use cases for physics data management and analysis:

1. **Data Discovery and Retrieval** - Search and download HFLAV datasets from multiple sources
2. **Data Transformation** - Convert between different data formats and schemas
3. **Data Visualization** - Generate plots and visualizations from physics measurements
4. **Cache Management** - Efficiently cache and reuse downloaded datasets (cached responses are stored locally and persist for 30 days by default, since Zenodo record files are immutable)
5. **Quality Assurance** - Validate data integrity and schema compliance

For detailed use case descriptions and diagrams, see [docs/use-cases.pdf](docs/use-cases.pdf).

## Architecture & Documentation

Full documentation is available in the [docs](docs/) folder.

The C4 architecture diagram can be checked in this picture:

![C4 diagram](docs/c4.png)

And the class structure is as it can be seen in this image:

![Class diagram](docs/Class_Diagram.png)

The Mermaid code for these diagrams is available in [c4.md](docs/c4.md) and [class_diagram.md](docs/class_diagram.md) respectively. Additionally, a draw.io version of the class diagram is available in [Class_Diagram_drawio](docs/Class_Diagram_drawio).

### About the GitLab integration

The library optionally connects to the [hflav-fair GitLab repository](https://gitlab.cern.ch/hflav/shared/hflav-fair) to retrieve the JSON schema used for data validation. This is **not** a code dependency — the hflav-fair package is not imported or used as a library. The GitLab integration is only an optional mechanism to dynamically fetch the schema file, so that the client always validates against the latest published schema. If the schema cannot be retrieved from GitLab, the library falls back to alternative strategies (e.g., retrieving it from Zenodo or using a local template).

## Configuring environment variables

All the environment variables available can be seen in the `EnvironmentVariables` enum inside the [config](hflav_fair_client/config.py) file.

| Variable                   | Description                  | Default             |
| -------------------------- | ---------------------------- | ------------------- |
| `HFLAV_CACHE_NAME`         | Name of the local HTTP cache | `hflav_cache`       |
| `HFLAV_CACHE_EXPIRE_AFTER` | Cache expiry time in seconds | `2592000` (30 days) |

To use environment variables in your code, simply modify the `.env` file:

```env
HFLAV_CACHE_NAME=my_cache
HFLAV_CACHE_EXPIRE_AFTER=2592000
```