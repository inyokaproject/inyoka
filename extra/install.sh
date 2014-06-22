#!/bin/sh

# Installation of the development environment for Inyoka.

set -xe

src_dir=$(readlink -f "$(dirname "$0")/..")
env_dir="$HOME/.venvs/inyoka"
xapian_version="1.2.12"

mkdir -p "$env_dir"
cd "$src_dir"

# install virtualenv
which virtualenv-2.7 >/dev/null && virtualenv-2.7 "$env_dir" || virtualenv "$env_dir"
. "$env_dir/bin/activate"
pip install -r extra/requirements/test.txt

# get and install xapian
cd /tmp
wget "http://oligarchy.co.uk/xapian/${xapian_version}/xapian-core-${xapian_version}.tar.gz"
wget "http://oligarchy.co.uk/xapian/${xapian_version}/xapian-bindings-${xapian_version}.tar.gz"

tar -xzf "xapian-core-${xapian_version}.tar.gz"
tar -xzf "xapian-bindings-${xapian_version}.tar.gz"

cd "/tmp/xapian-core-${xapian_version}"
./configure --prefix="$env_dir"
make && make install

cd "/tmp/xapian-bindings-${xapian_version}"
./configure --prefix="$env_dir" \
  --with-python \
  PYTHON="$env_dir/bin/python" \
  XAPIAN_CONFIG="$env_dir/bin/xapian-config" \
  PYTHON_INC="$env_dir/include/python2.7" \
  PYTHON_LIB="$env_dir/lib/python2.7"
make && make install

cd "$src_dir"
[ ! -f development_settings.py ] && cp example_development_settings.py development_settings.py

rm -r "/tmp/xapian-core-${xapian_version}"*
rm -r "/tmp/xapian-bindings-${xapian_version}"*

echo 
echo "################################################"
echo "Please add the following line to your /etc/hosts"
echo "127.0.0.1     ubuntuusers.local forum.ubuntuusers.local paste.ubuntuusers.local wiki.ubuntuusers.local planet.ubuntuusers.local ikhaya.ubuntuusers.local static.ubuntuusers.local media.ubuntuusers.local"
echo "################################################"
