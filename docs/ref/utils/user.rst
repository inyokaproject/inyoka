.. _utils-user:

==============
User Utilities
==============

.. py:module:: inyoka.utils.user

.. py:currentmodule:: inyoka.utils.user

Serveral utilities to work with users.

Some parts are ported from the django auth-module.

.. py:data:: _username_re

    Defaults to a case insensitive, unicode and compiled regular expression:
    ``ur'^[@\-\.a-z0-9 öäüß]{1,30}$'``

    This regular expression validates the username.


.. py:data:: _username_url_re

    Defaults to a case insensitive, unicode and compiled regular expression:
    ``ur'^[@\-\._a-z0-9 öäüß]{1,30}$'``


.. py:data:: _username_split_re

    Defaults to a case insensitive, unicode and compiled regular expression:
    ``ur'[\s_]+'``


.. py:function:: is_valid_username(name)

    Check if the username entered is a valid one.


.. py:function:: normalize_username(name)

    Either returns a url normalized username or raises a ``ValueError``.

    :return: The normalized username
    :raise: A ValueError if the username is not valid for a URL.


.. py:function:: gen_activation_key(user)

    It's calculated using a sha1 hash of the user id, the username, the users
    email and our secret key and shortened to ensure the activation link has
    less then 80 chars.

    :param user: The user that the key will be generated for.
    :type user: :py:class:`~inyoka.portal.user.User`


.. py:function:: check_activation_key(user, key)

    Check if an activation key is correct

    :param user: The user that needs to be checked.
    :param key: The key that needs to be checked for the *user*.
    :type user: :py:class:`~inyoka.portal.user.User`
    :type key: str


.. py:function:: get_hexdigest(salt, raw_password)

    Returns a string of the hexdigest of the given plaintext password and salt
    using the sha1 algorithm.


.. py:function:: check_password(raw_password, enc_password[, convert_user=None])

    Returns a boolean of whether the raw_password was correct. Handles
    encryption formats behind the scenes.
