/**
 * js/jQuery.extensions
 * ~~~~~~~~~~~~~~~~~~~~
 *
 * Various small jQuery extensions.
 *
 * :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
 * :license: GNU GPL, see LICENSE for more details.
 */


/**
 * Fetch all the nodes as long as a new node is found.
 */
jQuery.fn.nextWhile = function (expr) {
  var next = this.next(expr);
  var pos = 0;
  while (next.length > 0) {
    pos++;
    next = next.next(expr);
  }
  return this.nextAll(expr).slice(0, pos);
};
