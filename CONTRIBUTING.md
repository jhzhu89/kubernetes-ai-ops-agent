# Contributing to Kubernetes AI Operations

Thank you for your interest in contributing to the Kubernetes AI Operations project! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and considerate of others.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with the following information:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior and what actually happened
- Environment details (OS, Python version, etc.)
- Any relevant logs or screenshots

### Feature Requests

We welcome feature requests! Please create an issue with:

- A clear description of the feature
- Why this feature would be useful to the project
- Any ideas for implementation

### Pull Requests

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature-name` or `fix/your-fix-name`
3. Make your changes and add appropriate tests
4. Run tests to ensure they pass
5. Update documentation as needed
6. Submit a pull request

### Pull Request Process

1. Ensure your PR includes tests for new functionality
2. Update the README.md or documentation with details of changes if needed
3. The PR will be merged once it's reviewed and approved

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/k8s_ai_ops.git
   cd k8s_ai_ops
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt  # If available
   ```

## Coding Standards

- Follow PEP 8 style guide for Python code
- Write docstrings for all functions, classes, and modules
- Include type hints where appropriate
- Keep functions small and focused

## Testing

- Write tests for new functionality
- Run tests before submitting a PR:
  ```bash
  pytest
  ```

## Documentation

- Update documentation when adding or changing features
- Use clear, concise language
- Include examples where helpful

Thank you for contributing to Kubernetes AI Operations!