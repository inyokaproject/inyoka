To make the handling with requirements easier, Inyoka uses [pip-tools](https://github.com/jazzband/pip-tools).

An requirements file has to be generated for each environment.
According to the pip-tools documentation a environment is
“the combination of Operating System, Python version (2.7, 3.6, etc.), and Python implementation (CPython, PyPy, etc.)”

To generate the requirement files run

```
python manage.py generate_requirements
```
  * For production the dependencies are defined in `setup.py`
  * The (additional) development dependencies are defined via `extra/requirements/development.in`

To update all packages run

```
python manage.py generate_requirements --upgrade
```

To update a specific package (in this example `django`) run

```
python manage.py generate_requirements --upgrade django
```

`development.txt` and `production.txt` are just symlinks to the environment used on ubuntuusers.de.
Please check, if you have another python version installed and need to use another requirements file.
All available requirements files can be found in `extra/requirements/`.

If you want to generate the requirements for a python version you have not installed, there are tools
like [pyenv](https://github.com/pyenv/pyenv). They allow to have multiple versions of python installed
in parallel.

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
