/**
 * static.js.forum.m
 * ~~~~~~~~~~~~~~~~~
 *
 * JavaScript for the mobile forum.
 *
 * :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
 * :license: GNU GPL, see LICENSE for more details.
 */

$(document).ready(function() {
  $('.attachments ul').hide()
  $('.attachments .title').click(function() {
    $(this).next('ul').toggle()
  });

  // expand and collapse button for categories
  $('a.collapse').click(function() {
    $(this).next().toggle();
    // TODO: send the toggled categroy to the server and check for already
    // hidden ones
    /*$.get('/', {
      __service__: 'forum.toggle_categories',
      hidden:
    }); */
    return false;
  });
});
