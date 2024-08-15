/**
 * js.Pastebin
 * ~~~~~~~~~~~
 *
 * Implements some useful functions for the pastebin.
 *
 * :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
 * :license: BSD, see LICENSE for more details.
 */

$(document).ready(function () {
  $('ul.paste_actions').append($('<li />').append(
  $('<a href="#">Zeilennummern ein-/ausschalten</a>').click(function () {
    $('.syntaxtable .linenos').toggle();
    return false;
  }))).append($('<li />').append(
  $('<a href="#">Syntaxhighlighting ein-/ausschalten</a>').click(function () {
    $('.syntaxtable td.code > div').toggleClass('syntax');
    return false;
  })));
});
