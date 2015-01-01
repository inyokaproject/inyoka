/**
 * js.ikhaya
 * ~~~~~~~~~~
 *
 * Some javascript functions for the ikhaya application.
 *
 * :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
 * :license: BSD, see LICENSE for more details.
 */

function makeCommentLinks(elm) {
  $('p', elm).each(function (i, comment) {
    $(comment).html($(comment).html().replace(/@(\d+)/g, '<a href="#comment_$1" class="comment_link">@$1</a>'));
  });
  $('.comment_link').mouseover(function () {
    var id = $(this).html().slice(1);
    var userinfo = $('#comment_' + id + ' td.author p.username a').html();
    userinfo = userinfo + ' schrieb:<br />';
    var html = $.map($('#comment_' + id + ' td.comment p'), function (e) {
      return $(e).html();
    }).join('<br />');
    this.tooltip = $('<div class="tooltip"></div>').html(userinfo + html).css({
      'left': $(this).position().left,
      'top': $(this).position().top + 20,
      'position': 'absolute'
    }).appendTo($('body'));
  }).mouseout(function () {
    this.tooltip.remove();
  });
}

$(function () {
  if (navigator.appName.toLowerCase() == 'konqueror') return;
  makeCommentLinks($('ul.comments > li.comment'));


  var doAssignmentAction = function (tag, username) {
    var url = "/?__service__=ikhaya.change_suggestion_assignment";
    if (username == '-')
      text = 'Niemand';
    else
      text = username;
    $.post(url, {
      username: username,
      suggestion: $(tag).attr('id')
    }, function (data, status, xhr) {
      // Bind new events and change button's text.
      if (xhr.status == 200) {
        var info = $('.articleinfo span.suggestion-' + $(tag).attr('id'));
        $(info).fadeOut('fast');
        $(info).text('Zugewiesen an: ' + text);
        $(info).fadeIn('fast');
      }
    });
  };

  $('.suggestionlist a.assign').click(function() {
    doAssignmentAction($(this), $CURRENT_USER);
    return false;
  });

  $('.suggestionlist a.unassign').click(function() {
    doAssignmentAction($(this), '-');
    return false;
  });

});
