# Contributing to Home Assistant FMD

Thank you for considering contributing to the Home Assistant FMD integration! We welcome contributions from everyone.

## Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/your-username/home-assistant-fmd.git
    cd home-assistant-fmd
    ```
3.  **Set up your environment**:
    This project uses a standard Python environment. We recommend using a virtual environment.
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements_test.txt
    ```
4.  **Install pre-commit hooks**:
    This ensures your code is formatted correctly before you commit.
    ```bash
    pre-commit install
    ```

## Development Workflow

1.  **Create a branch** for your feature or bugfix:
    ```bash
    git checkout -b feature/my-awesome-feature
    ```
2.  **Make your changes**.
3.  **Run tests** to ensure everything is working:
    ```bash
    pytest
    ```
    To run with coverage:
    ```bash
    pytest --cov=custom_components.fmd --cov-report=term-missing
    ```
4.  **Commit your changes**. Pre-commit hooks will run automatically to format your code.
    ```bash
    git add .
    git commit -m "Add my awesome feature"
    ```
5.  **Push to your fork**:
    ```bash
    git push origin feature/my-awesome-feature
    ```
6.  **Open a Pull Request** on GitHub.

## Coding Standards

- **Formatting**: We use `black` and `isort`. Pre-commit handles this for you.
- **Linting**: We use `flake8`.
- **Typing**: We use type hints throughout the codebase.
- **Tests**: We aim for 100% test coverage. Please add tests for any new features or bug fixes.

## Project Structure

- `custom_components/fmd/`: The integration source code.
- `tests/`: Unit tests.
- `docs/`: Documentation.

## Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub using the provided templates.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
