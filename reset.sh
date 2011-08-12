#!/bin/bash
#echo "Dropping database tables..." ### TODO
#python manage-inyoka.py dropdb

# create the media folders
rm -Rf ./inyoka/media
mkdir ./inyoka/media
mkdir ./inyoka/media/forum
mkdir ./inyoka/media/forum/attachments
mkdir ./inyoka/media/forum/attachments/temp
mkdir ./inyoka/media/forum/thumbnails
mkdir ./inyoka/media/planet
mkdir ./inyoka/media/planet/icons
mkdir ./inyoka/media/wiki
mkdir ./inyoka/media/wiki/attachments
mkdir ./inyoka/media/portal
mkdir ./inyoka/media/portal/avatars
mkdir ./inyoka/media/portal/team_icons
echo "Created media directories"

echo "Syncronize database"
python manage.py syncdb
echo "Run migrations"
python manage.py migrate
echo "finished basic database creation"

# make sure that the xapian database is recreated
rm -rf $(python -c 'from django.conf import settings; print "\"%s\"" % settings.XAPIAN_DATABASE')
python -c 'import xapian; from django.conf import settings; xapian.WritableDatabase(settings.XAPIAN_DATABASE, xapian.DB_CREATE_OR_OPEN)'
echo "Created xapian database"
