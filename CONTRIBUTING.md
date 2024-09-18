# Contributing

## Welcome

If you are here, it means you are interested in helping us out. A hearty welcome and thank you! There are many ways you can contribute to Vasim:

* Offer PR's to fix bugs or implement new features
* There are a LOT of TODOs in the code, any help is welcome!
* Give us feedback and bug reports regarding the software or help setup documentation
* Improve our examples, and documentation.
This project welcomes contributions and suggestions.

## Getting Started

### Pull requests

If you are new to GitHub [here](https://help.github.com/categories/collaborating-with-issues-and-pull-requests/) is a detailed help source on getting involved with development on GitHub.

As a first time contributor, you will be invited to sign the Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com. You will only need to do this once across all repos using our CLA.

Your pull request needs to reference a filed issue. Please fill in the template that is populated for the pull request. Only pull requests addressing small typos can have no issues associated with them.

All commits in a pull request will be [squashed](https://github.blog/2016-04-01-squash-your-commits/) to a single commit with the original creator as author.

### Code of Conduct

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Developing

### Setup

The simplest setup (assuming you already have Python installed) is as follows:

> Note: you are encouraged to use a virtual environment with either [`conda`](https://docs.anaconda.com/miniconda/) or [`venv`](https://docs.python.org/3/library/venv.html) to avoid conflicts with other Python packages.

#### `venv`

```sh
# Clone the repo:
git clone https://github.com/microsoft/vasim.git
cd vasim
# Create a virtual environment (venv example):
python -m venv .venv
# Activate the virtual environment:
source .venv/bin/activate
# Install the package in editable mode with dev dependencies:
python -m pip install -e ".[dev]"
```

#### `conda`

```sh
# Clone the repo:
git clone https://github.com/microsoft/vasim.git
cd vasim
# Create a virtual environment (conda example):
conda create -n vasim python=3.10
# Activate the virtual environment:
conda activate vasim
# Install the package in editable mode with dev dependencies:
python -m pip install -e ".[dev]"
```

### Tools

#### Pre-commit

This project uses [pre-commit](https://pre-commit.com/) hooks.

To setup `pre-commit` to your `git` hook do the following:

```sh
python -m pip install pre-commit
pre-commit install
```

And before you commit, you can run it like this `pre-commit run --all-files` and should see output such as:

```txt
Flake8...........................Passed
```

If you have installed your pre-commit hooks successfully, you should see something like this if you try to commit something non-conformant:

```txt
$ git commit -m "testing"
Flake8............................Failed
- hook id: flake8
- exit code: 1
```

#### Naming Convention

Scripts should be named in `snake_case` and classes in `CamelCase`.

#### Formatting

We generally use all pep8 checks, with the exception of line length 127.

To do a quick check-up before commit, try:

```sh
flake8 . --count  --max-complexity=10 --max-line-length=127 --statistics
```

#### Coverage

For coverage, we use [coverage.py](https://coverage.readthedocs.io/en/) in our Github Actions.
Run  `python -m pip install coverage` if you don't already have this, and any code you commit should generally not significantly impact coverage.

We strive to not let check-ins decrease coverage.
To run all unit tests:

```sh
coverage run -m pytest tests
```
