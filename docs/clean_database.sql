-- Remove content from user sensetive tabels
TRUNCATE portal_privatemessage, portal_privatemessageentry, django_session;

-- Remove personal user informations
UPDATE portal_user SET password = 'invalid';
UPDATE portal_user SET email = CONCAT(username, '@ubuntuusers.invalid');
UPDATE portal_user SET jabber = '', signature = '', location = '', gpgkey = '', website = '', launchpad = '';
