# Contributing to LLM Text Preprocessing Tool

Thank you for your interest in contributing to the LLM Text Preprocessing Tool! This document provides guidelines and instructions for contributing to this project.

## Code Style and Guidelines

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code style
- Write clear, self-explanatory code with descriptive variable and function names
- Use type hints consistently throughout the codebase
- Keep functions small and focused on a single responsibility
- Add docstrings to all modules, classes, and functions

## Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Run the test suite to ensure everything passes
6. Commit your changes (`git commit -m 'Add some amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the documentation if you're changing functionality
3. The PR should work for Python 3.9 and above
4. Ensure all tests pass before submitting the PR

## Testing

- Write unit tests for all new functionality
- Run the existing test suite before submitting changes
- Use pytest for test organization

## Documentation

- Keep documentation up to date with code changes
- Document any new features or changes in behavior
- Provide examples for new functionality

## Adding New File Format Support

When adding support for a new file format:

1. Create a new converter class in the `converters` directory
2. Implement the `BaseConverter` interface
3. Register the new converter in the converter registry
4. Add appropriate tests for the new converter
5. Update documentation to reflect the new supported format

Thank you for contributing!
