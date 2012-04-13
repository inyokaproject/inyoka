/**
 * js.overall.m
 * ~~~~~~~~~~~~
 *
 * Some general scripts for the whole mobile portal (requires jQuery).
 *
 * :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
 * :license: GNU GPL, see LICENSE for more details.
 */

$(document).ready(function() {
  // toggle of top menu
  $('a.toggle_menu').click(function() {
    $('#top_menu').toggle();
    return false;
  });
});
