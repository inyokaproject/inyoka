#!/bin/sh

# Installation of the development environment for Inyoka.

set -xe

src_dir=$(readlink -f "$(dirname "$0")/..")
env_dir="$HOME/.venvs/inyoka"

mkdir -p "$env_dir"
cd "$src_dir"

# install virtualenv
which virtualenv-2.7 >/dev/null && virtualenv-2.7 "$env_dir" || virtualenv "$env_dir"
. "$env_dir/bin/activate"
pip install -r extra/requirements/test.txt

set +x

echo
echo "################################################"
echo "Please add the following line to your /etc/hosts"
echo "127.0.0.1     ubuntuusers.local forum.ubuntuusers.local paste.ubuntuusers.local wiki.ubuntuusers.local planet.ubuntuusers.local ikhaya.ubuntuusers.local static.ubuntuusers.local media.ubuntuusers.local"
echo "################################################"
