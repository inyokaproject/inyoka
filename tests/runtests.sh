#!/bin/bash

basedir=$(dirname $0)
interpreter=python
manage="${basedir}/../manage.py test --noinput"
settings=()
verbosity=1

function usage {
    echo "Usage:"
    echo "${0}"
    echo "        [-i | --interpreter INTERPRETER]"
    echo "        [-s | --settings SETTINGS]"
    echo "        [--test-mysql]"
    echo "        [--test-postgresql]"
    echo "        [--test-sqlite]"
    echo "        [-v | --verbosity VERBOSE_LEVEL]"
    echo "        [--with-coverage]"
    echo "        [-h | --help]"
}

while [ "$1" != "" ]; do
    case $1 in
        -i|--interpreter)
            shift
            interpreter=${1}
            ;;
        -s|--settings)
            shift
            settings+=("${1}")
            ;;
        --test-mysql)
            settings+=("tests.settings.mysql")
            ;;
        --test-postgresql)
            settings+=("tests.settings.postgresql")
            ;;
        --test-sqlite)
            settings+=("tests.settings.sqlite")
            ;;
        -v|--verbosity)
            shift
            verbosity="${1}"
            ;;
        --with-coverage)
            interpreter="coverage run --branch"
            ;;
        -h|--help)
            usage
            exit
            ;;
        *)
            usage
            exit 1
    esac
    shift
done

if [ ${#settings[@]} -eq 0 ] ; then
    echo "No settings defined!"
    exit 1
fi

uniq_settings=($(printf "%s\n" "${settings[@]}" | sort -u))

for setting in "${uniq_settings[@]}" ; do
    echo -en "\n\n--------------------------------------------------\nrunning tests for $setting"
    $interpreter $manage --settings=$setting --verbosity=$verbosity
done

