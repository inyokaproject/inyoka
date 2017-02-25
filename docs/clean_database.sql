SET FOREIGN_KEY_CHECKS = 0;
# Remove unused tabels
DROP TABLE IF EXISTS celery_taskmeta;
DROP TABLE IF EXISTS celery_tasksetmeta;
DROP TABLE IF EXISTS django_openid_association;
DROP TABLE IF EXISTS django_openid_nonce;
DROP TABLE IF EXISTS djcelery_crontabschedule;
DROP TABLE IF EXISTS djcelery_intervalschedule;
DROP TABLE IF EXISTS djcelery_periodictask;
DROP TABLE IF EXISTS djcelery_periodictasks;
DROP TABLE IF EXISTS djcelery_taskstate;
DROP TABLE IF EXISTS djcelery_workerstate;
DROP TABLE IF EXISTS djkombu_message;
DROP TABLE IF EXISTS djkombu_queue;
DROP TABLE IF EXISTS south_migrationhistory;

# Remove content from user sensetive tabels
DELETE FROM portal_privatemessage;
DELETE FROM portal_privatemessageentry;
DELETE FROM portal_sessioninfo;
DELETE FROM django_session;

# Remove personal user informations
UPDATE portal_user SET password = 'invalid';
UPDATE portal_user SET email = CONCAT(username, '@ubuntuusers.invalid');
UPDATE portal_user SET jabber = '', signature = '', location = '', gpgkey = '', website = '', launchpad = '';
SET FOREIGN_KEY_CHECKS = 1;
