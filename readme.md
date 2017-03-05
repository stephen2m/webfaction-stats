## Development

### First-time setup
Set up packages and the pre-commit hook `pip install -r requirements/development.txt && ln -s ../../commit-checks.sh .git/hooks/pre-commit`
This checks all commits for well written code ( via
[pep8](https://pypi.python.org/pypi/pycodestyle),
[pyflakes](https://pypi.python.org/pypi/pyflakes) and
[Cyclomatic complexity](https://pypi.python.org/pypi/mccabe) checks,
read more => <https://pypi.python.org/pypi/flake8>)
