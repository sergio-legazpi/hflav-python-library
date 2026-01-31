# Development Guide

## Setting Up the Development Environment

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment tool (venv)

### Initial Setup

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd hflav-python-library
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**:
   - On Linux/MacOS:
     ```bash
     source .venv/bin/activate
     ```
   - On Windows:
     ```bash
     .venv\Scripts\activate
     ```

4. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

   This installs the package in editable mode with all development dependencies, including:
   - Testing frameworks (pytest, pytest-cov, pytest-benchmark)
   - Code quality tools
   - Documentation tools

## Configuration

### Environment Variables

All available environment variables can be seen in the `EnvironmentVariables` enum inside the [config.py](../hflav_fair_client/config.py) file.

To use environment variables in your code:

1. Create a `.env` file in the project root (if not already present)
2. Add your environment variables
3. Load them in your Python code:
   ```python
   from dotenv import load_dotenv
   
   load_dotenv()
   ```

### Logging

The project includes a logging configuration. For more details, see [LOGGING.md](LOGGING.md).

## Debugging

### Using VS Code

1. Create a `.vscode/launch.json` file with debug configurations
2. Set breakpoints in your code
3. Press F5 to start debugging

### Using Print Debugging

The project uses a logging system. Instead of print statements, use:

```python
from hflav_fair_client.logger import logger
...
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

## Additional Resources

- [Testing Guide](TESTING.md) - How to run and write tests
- [Code Analysis Guide](CODE_ANALYSIS.md) - How to analyze code quality
- [Logging Documentation](LOGGING.md) - Logging configuration and usage
- [Architecture Documentation](c4.png) - C4 architecture diagram
- [Class Diagram](Class_Diagram.png) - Class structure overview
