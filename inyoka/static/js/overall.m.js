/**
 * js.overall.m
 * ~~~~~~~~~~~~
 *
 * Some general scripts for the whole mobile portal (requires jQuery).
 *
 * :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
 * :license: BSD, see LICENSE for more details.
 */

$(document).ready(function() {
  // toggle of top menu containing main navigation
  $('a.toggle_menu').click(function() {
    $('#top_menu').toggle();
  });

  // watch hashchanges to make the back button on android work for the menu
  $(window).hashchange(function() {
    if (location.hash == '#menu') {
      $('#top_menu').show();
    } else if (location.hash === '') {
      $('#top_menu').hide();
    }
  });

  $('.pagination').each(function() {
    $(this).find('select').change(function() {
      var page = $(this).find('option:selected').text();
      var url = $(this).parent().parent().find('span.link_base').text();
      if (page != '1') {
        url += page;
      }
      window.location = url;
    });
  });
});
