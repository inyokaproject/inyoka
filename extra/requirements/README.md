To make the handling with requirements easier, Inyoka uses [pip-tools](https://github.com/jazzband/pip-tools).

An requirements file has to be generated for each environment.
According to the pip-tools documentation a environment is
“the combination of Operating System, Python version (2.7, 3.6, etc.), and Python implementation (CPython, PyPy, etc.)”

To generate the requirement files run

```
pip-compile --allow-unsafe --generate-hashes --output-file extra/requirements/<os>-py<version>-production.txt
pip-compile --allow-unsafe --generate-hashes extra/requirements/development.in --output-file extra/requirements/<os>-py<version>-development.txt
```
  * For production the dependencies are defined in `setup.py`
  * The (additional) development dependencies are defined via `extra/requirements/development.in`

To update all packages run

```
pip-compile --upgrade --allow-unsafe --generate-hashes --output-file extra/requirements/<os>-py<version>-production.txt
```

To update a specific package (in this example `django`) run

```
pip-compile --upgrade-package django --allow-unsafe --generate-hashes --output-file extra/requirements/<os>-py<version>-production.txt
```

`development.txt` and `production.txt` are just symlinks to the environment used on ubuntuusers.de.
Please check, if you have another python version installed and need to use another requirements file.
All available requirements files can be found in `extra/requirements/`.

# Installation of packages

For the first time run

```
pip install -r extra/requirements/production.txt
```

Then you can run either
 * on production
```
$ pip-sync extra/requirements/production.txt
```

 * or for development
```
$ pip-sync extra/requirements/production.txt extra/requirements/development.txt
```

The latter are also of interest, if the content of the requirement-files changed.

# TODO

Create a management command as a wrapper? Latter could build the `{production,development}.txt` with only one command.
(`CUSTOM_COMPILE_COMMAND` should be set accordingly)
