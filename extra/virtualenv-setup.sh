#!/bin/bash
# A simple Script for creating virtual environments without magic things ;-)

PIL_VERSION='1.1.7'
XAPIAN_VERSION='1.2.5'
BASE_DIRECTORY=`pwd`

if [ ! -z $1 ]; then
    VIRTUAL_ENV=$1
else
    if [ -z $VIRTUAL_ENV ]; then
        if [ -z $1 ]; then
            VIRTUAL_ENV='../inyoka-prod-virtualenv'
        else
            VIRTUAL_ENV=$1
        fi
    fi
fi

echo "Using $VIRTUAL_ENV to create the virtual environment"

# Step 0: Create Virtualenv and source directory
if [ ! -d $VIRTUAL_ENV/bin ]; then virtualenv $VIRTUAL_ENV; fi
if [ ! -d $VIRTUAL_ENV/src ]; then mkdir $VIRTUAL_ENV/src; fi
VIRTUAL_ENV=`readlink -m -n $VIRTUAL_ENV`
# Step 1: Activate Virtualenv
. $VIRTUAL_ENV/bin/activate
cd $VIRTUAL_ENV/src
## Step 2: Setup PIL
wget -c "http://effbot.org/downloads/Imaging-$PIL_VERSION.tar.gz"
if [ ! -d Imaging-$PIL_VERSION ]; then tar xzvf Imaging-$PIL_VERSION.tar.gz; fi
cd "Imaging-$PIL_VERSION"
python setup.py install
cd ..

# Step 3: Setup Xapian
wget -c "http://oligarchy.co.uk/xapian/$XAPIAN_VERSION/xapian-core-$XAPIAN_VERSION.tar.gz"
wget -c "http://oligarchy.co.uk/xapian/$XAPIAN_VERSION/xapian-bindings-$XAPIAN_VERSION.tar.gz"
if [ ! -d xapian-core-$XAPIAN_VERSION.tar.gz ]; then
 tar xzvf xapian-core-$XAPIAN_VERSION.tar.gz;
fi
if [ ! -d xapian-bindings-$XAPIAN_VERSION.tar.gz ]; then
 tar xzvf xapian-bindings-$XAPIAN_VERSION.tar.gz;
fi
cd $VIRTUAL_ENV/src/xapian-core-$XAPIAN_VERSION
./configure --prefix=$VIRTUAL_ENV
make -j8
make install
cd $VIRTUAL_ENV/src/xapian-bindings-$XAPIAN_VERSION
./configure --prefix=$VIRTUAL_ENV --with-python
make -j8
make install

# Step 4: Install requirements via pip
cd $BASE_DIRECTORY
pip install --upgrade -r extra/requirements.txt
