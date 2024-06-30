# Collections Import Generator

Tool to create an Axiell Collections Import Sheet from DROID CSV and an external
CSV.

Based on the [archwayimportgenerator][archway-1] tool developed by
@ross-spencer.

[archway-1]: https://github.com/archives-new-zealand/archwayimportgenerator

## Usage Information

The Collections Import Generator needs to be configured with an INI file and
provided to the app as an argument.

The sections required in the config file are:

```text
    [droid mapping],
    [static values],
    [additional values],
    [external mapping config],
    [external mapping],
```

> The script will provide more information if you are missing any information.

Sections describe different map configurations, for example, `[static values]`
can be used to define constants that will be shared across an import sheet, e.g.
Agency is likely to be a consistent field.

You can list fields you can map to with:

```sh
python import_generator.py --list
```

Otherwise the command line arguments look as follows:

```sh
usage: import_generator.py [-h] [--csv CSV] [--ext EXT] [--conf CONF] [--list]

Generate Archway Import Sheet and Rosetta Ingest CSV from DROID CSV Reports.

options:
  -h, --help            show this help message and exit
  --csv CSV, -c CSV     DROID CSV to read.
  --ext EXT, --external EXT
                        insert data from an arbitrary CSV.
  --conf CONF, --config CONF
                        import mapping configuration.
  --list, -l            list Collection CSV fields.
```

The scripts rely primarily on a DROID spreadsheet and is biased to digital
transfers.

An optional external metadata sheet can be provided for which additional mapping
needs to be configured.

An example import might look as follows (assuming all sheets are in a
directory called `sheets`):

```sh
python import_generator.py \
 --ext sheets/external.csv \
 --csv sheets/droid.csv \
 --conf sheets/conf.cfg > import.csv
```

### Troubleshooting

#### Encoding

If there are any problems running this script with UTF-8 characters you may need
to configure your environment differently. Windows is most likely to raise
issues. If so you can change your codepage and default encoding with:

```sh
chcp 65001
set PYTHONIOENCODING=utf-8
```

### Dependencies

`pyproject.toml` and `requirements/requirements.txt` can be inspected for
dependencies. If we have done our job correctly, you should find 🙅‍♀️ none!

One of the goals of this project is to ensure that it can be installed in a
secure operating environment and one of the ways to continue to keep a secure
environment is to minimize the number of dependencies that are used which
potentially open up more surface area for attack and misuse.

No dependencies also means the scripts can be used (and installed with the
`.whl` below) without the need to access the internet.

### Installing from a Python Wheel

The [Python wheel][wheel-1] `.whl` that is distributed the the repository can be
installed using pip. Given a .whl file:

[wheel-1]: https://realpython.com/python-wheels/

```sh
python -m pip install collections_import-0.0.0rc1-py3-none-any.whl
```

This makes it easy to run the script using aliases in the virtual environment
e.g. with:

```sh
import_generator -h
```

or

```sh
import-generator -h
```

> NB. it is recommended to use a virtual environment locally, described below
in developer instructions.

#### Creating a .whl

Two methods can be used to create a new wheel with changes to the code. The
recommended approach is to use the release action in GitHub which is triggered
when a new tag is created in the app.

```sh
git tag -a 0.0.x-rc.x -m 0.0.x-rc.x
git push origin 0.0.x-rc.x
```

> it is recommended to use [semantic versioning][semver-1] to create version
numbers. On top of `major.minor.path` the suffix `-rc.x` can be used to create
release candidates for testing and signal to the user the utility is not ready
to be used in production just yet.

[semver-1]: https://semver.org/

When the action completes a package and corresponding release will have been
created and availabnle on the repository release page.

`make package-source` can also be used to build locally and this package will
be available in the `dist/` folder.

### Viewing CSV files

A useful utility you can view different CSV files with is CSVLens:
[here][csv-lens].

[csv-lens]: https://github.com/YS-L/csvlens

## Developer install

### pip

Setup a virtual environment `venv` and install the local development
requirements as follows:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements/local.txt
```

#### Upgrade dependencies

A `make` recipe is included, simply call `make upgrade`. Alternatively run
`pip-upgrader` once the local requirements have been installed and follow the
prompts. `requirements.txt` and `local.txt` can be updated as desired.

### tox

#### Run tests (all)

```bash
python -m tox
```

#### Run tests-only

```bash
python -m tox -e py3
```

#### Run linting-only

```bash
python -m tox -e linting
```

### pre-commit

Pre-commit can be used to provide more feedback before committing code. This
reduces reduces the number of commits you might want to make when working on
code, it's also an alternative to running tox manually.

To set up pre-commit, providing `pip install` has been run above:

* `pre-commit install`

This repository contains a default number of pre-commit hooks, but there may
be others suited to different projects. A list of other pre-commit hooks can be
found [here][pre-commit-1].

[pre-commit-1]: https://pre-commit.com/hooks.html

## Packaging

The `Makefile` contains helper functions for packaging and release.

Makefile functions can be reviewed by calling `make`  from the root of this
repository:

```make
clean                          Clean the package directory
docs                           Generate documentation
help                           Print this help message
package-check                  Check the distribution is valid
package-deps                   Upgrade dependencies for packaging
package-source                 Package the source code
package-upload                 Upload package to pypi
package-upload-test            Upload package to test.pypi
pre-commit-checks              Run pre-commit-checks.
serve-docs                     Serve the documentation
tar-source                     Package repository as tar for easy distribution
upgrade                        Upgrade project dependencies
```

### pyproject.toml

Packaging consumes the metadata in `pyproject.toml` which helps to describe
the project on the official [pypi.org][pypi-2] repository. Have a look at the
documentation and comments there to help you create a suitably descriptive
metadata file.

### Local packaging

To create a python wheel for testing locally, or distributing to colleagues
run:

* `make package-source`

A `tar` and `whl` file will be stored in a `dist/` directory. The `whl` file
can be installed as follows:

* `pip install <your-package>.whl`

### Publishing

Publishing for public use can be achieved with:

* `make package-upload-test` or `make package-upload`

`make-package-upload-test` will upload the package to [test.pypi.org][pypi-1]
which provides a way to look at package metadata and documentation and ensure
that it is correct before uploading to the official [pypi.org][pypi-2]
repository using `make package-upload`.

[pypi-1]: https://test.pypi.org
[pypi-2]: https://pypi.org
