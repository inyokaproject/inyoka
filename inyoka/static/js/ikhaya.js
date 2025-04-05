/**
 * js.ikhaya
 * ~~~~~~~~~~
 *
 * Some javascript functions for the ikhaya application.
 *
 * :copyright: (c) 2007-2025 by the Inyoka Team, see AUTHORS for more details.
 * :license: BSD, see LICENSE for more details.
 */

function makeCommentLinks(elm) {
  $('p', elm).each(function (i, comment) {
    $(comment).html($(comment).html().replace(/@(\d+)/g, '<a href="#comment_$1" class="comment_link">@$1</a>'));
  });
}

$(function () {
  makeCommentLinks($('ul.comments > li.comment'));
});
