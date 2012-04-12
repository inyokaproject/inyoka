/*
static.js.forum.m
~~~~~~~~~~~~~~~~~

JavaScript for the mobile forum.

:copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
:license: GNU GPL, see LICENSE for more details.
*/

$(document).ready(function() {
  $('.attachments ul').hide()
  $('.attachments .title').click(function() {
    $(this).next('ul').toggle()
  });
});
