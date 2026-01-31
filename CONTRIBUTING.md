# Contributing to HFLAV FAIR Client

Thank you for your interest in contributing to the HFLAV FAIR Client project! This document provides guidelines and information for contributors.

## Getting Started

To get started with development, please refer to our comprehensive documentation:

- **[Development Guide](docs/DEVELOPMENT.md)** - Setting up your development environment and running the project
- **[Testing Guide](docs/TESTING.md)** - Running tests, checking coverage, and understanding different test types
- **[Code Analysis Guide](docs/CODE_ANALYSIS.md)** - Configuring and running code quality analysis with SonarQube

## Quick Start

1. **Set up your environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

2. **Run tests**:
   ```bash
   pytest tests
   ```

3. **Check code quality**:
   ```bash
   coverage run -m pytest
   coverage xml
   ```

For detailed instructions, see the [Development Guide](docs/DEVELOPMENT.md).

## Contribution Workflow

1. **Fork and clone** the repository
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** with appropriate tests
4. **Run tests and code analysis** to ensure quality
5. **Commit your changes** with clear, descriptive messages
6. **Push to your fork** and submit a pull request

## Code Standards

- Follow PEP 8 style guidelines
- Write tests for new functionality
- Maintain or improve code coverage (target: >80%)
- Add docstrings to classes and functions
- Update documentation as needed

## Running Code Analysis

Before submitting a pull request:

1. Ensure all tests pass: `pytest tests`
2. Check coverage: `pytest --cov=hflav_fair_client`
3. Run SonarQube analysis (see [Code Analysis Guide](docs/CODE_ANALYSIS.md))

## Documentation

- [Development Guide](docs/DEVELOPMENT.md) - Development setup and workflows
- [Testing Guide](docs/TESTING.md) - Testing procedures and best practices
- [Code Analysis Guide](docs/CODE_ANALYSIS.md) - Code quality and static analysis
- [Logging Documentation](docs/LOGGING.md) - Logging configuration
- [Architecture](docs/c4.png) - C4 architecture diagram
- [Class Structure](docs/Class_Diagram.png) - Class diagram

## Questions or Issues?

If you have questions or encounter issues:

1. Check the documentation guides listed above
2. Review existing issues in the repository
3. Create a new issue with detailed information

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing to HFLAV FAIR Client!