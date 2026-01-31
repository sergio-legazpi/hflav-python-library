# Testing Guide

## Running Tests

### Run All Tests

To launch all the tests in the project:

```bash
pytest tests
```

### Run Specific Tests

To launch a specific test file:

```bash
pytest tests/test_file.py
```

To run a specific test class or function:

```bash
pytest tests/test_file.py::TestClassName::test_method_name
```

### Run Tests by Marker

To run tests filtered by a specific marker (e.g., performance tests):

```bash
pytest -m performance
```

To exclude specific markers:

```bash
pytest -m "not performance"
```

## Test Coverage

### Check Coverage for Specific Modules

To check the coverage for a specific module:

```bash
pytest --cov=hflav_fair_client.module
```

Where `module` is a specific module name.

Example:

```bash
pytest --cov=hflav_fair_client.source
```

### Generate Coverage Report

To run all tests with coverage and generate an XML report:

```bash
coverage run -m pytest
coverage xml
```

For an HTML coverage report:

```bash
coverage run -m pytest
coverage html
```

The HTML report will be generated in the `htmlcov` directory.

## Types of Tests

### Unit Tests

Unit tests are located in the `tests/` directory and organized by module. They test individual components in isolation using mocks when necessary.

- **Location**: `tests/<module_name>/test_*.py`
- **Purpose**: Verify individual functions and classes work correctly
- **Run**: `pytest tests/<module_name>`

Examples:
- `tests/conversors/test_conversor.py`
- `tests/models/test_models.py`
- `tests/services/test_service.py`

### Integration Tests

Integration tests verify that different components work together correctly.

- **Location**: `tests/integration.py`
- **Purpose**: Test interactions between multiple components
- **Run**: `pytest tests/integration.py`

### Performance Tests

Performance tests validate that the system meets non-functional requirements (NFR) for response time, data processing, and visualization.

- **Location**: `tests/performance_tests.py`
- **Purpose**: Ensure performance thresholds are met
- **Run**: `pytest -m performance`

**Performance Test Categories:**

1. **NFR-01: Zenodo Query Performance**
   - Small datasets (<10MB): Must complete in under 5 seconds
   - Large datasets: Must complete in under 30 seconds

2. **NFR-02: Data Processing Performance**
   - Data transformation: Handle datasets up to 1GB in memory
   - Execution time: Under 10 seconds

3. **NFR-03: Plot Generation Performance**
   - Visualizations: Must render in under 3 seconds for up to 10,000 data points

To run performance tests with benchmark results:

```bash
pytest tests/performance_tests.py --benchmark-only
```
