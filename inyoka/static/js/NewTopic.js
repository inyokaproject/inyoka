/**
 * js.newtopic
 * ~~~~~~~~~~~
 *
 * Adds support for inserting quotes into the WikiEditor.
 *
 * :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
 * :license: BSD, see LICENSE for more details.
 */

var set_quote_links = (function () {
  $('table.topic div.postinfo').each(function () {
    if ($(this).children('div.linklist.floatright').length === 0) {
      var post_id = $(this).parent().parent()[0].id.substring(5);
      $('<a href="#" class="action action_quote">Zitat einfügen</a>').click(function () {
        $.getJSON('/?__service__=forum.get_post', {
          post_id: post_id
        }, function (post) {
          if (post) {
            var editor = $('#id_text')[0].inyokaWikiEditor;
            editor.setSelection("[user:" + post.author + ":] [post:" + post_id + ": schrieb]:\n" + editor.quoteText(post.text));
            editor.focus();
          }
        });
        return false;
      }).appendTo($('<div class="linklist floatright" />').prependTo(this));
    }
  });
});
$(set_quote_links);

$(function () {
  $('th#recent_posts').append(' (<a href="#" id="recent_posts_reload">aktualisieren</a>)');

  var remove_note = function () {
    $('#no_recent_posts_note').find('div').slideUp(400, function () {
      $('#no_recent_posts_note').remove();
      $('#recent_posts_reload').data('loading', false);
    });
    return false;
  };

  var add_new_posts = function (data) {
    if (data) {
      $('.latest_posts tbody').prepend(data);
      $('#recent_posts_reload').data('loading', false);
      set_quote_links();
    } else {
      $('<tr id="no_recent_posts_note"><td colspan="2"><div style="display: none">' + 
        '<div style="margin:0.3em 0">Keine neuen Beiträge</div></div></td></tr>')
        .appendTo($('#recent_posts').parent().parent())
        .children('td').css('padding', 0)
        .children('div').css('padding', '0 0').slideDown(400);
      window.setTimeout(remove_note, 5000);
      $('#no_recent_posts_note').click(remove_note);
    }
    return false;
  };

  $('#recent_posts_reload').click(function () {
    if ($(this).data('loading')) return false;
    $(this).data('loading', true);
    remove_note();

    latest_post_id = Number($('.latest_posts tr')[0].id.substr(5));
    $.post('/?__service__=forum.get_new_latest_posts', {
      post: latest_post_id
    }, add_new_posts);
    return false;
  });
});
