/**
 * js.mobile
 * ~~~~~~~~~
 *
 * Some scripts for the mobile Inyoka version
 *
 * :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
 * :license: GNU GPL, see LICENSE for more details.
 */

function hide_mobile_notice() {
  var d = new Date();
  var d_exp = d.getTime() + (365 * 24 * 60 * 60 * 1000);
  d.setTime(d_exp);
  var exp = "expires=" + d.toGMTString();
  var dom;
  if ($BASE_DOMAIN_NAME.indexOf(":") > 0) {
    dom = "domain=." + $BASE_DOMAIN_NAME.substring(0, $BASE_DOMAIN_NAME.indexOf(":"));
  } else {
    dom = "domain=." + $BASE_DOMAIN_NAME;
  }
  document.cookie = "hide_mobile_notice=0; " + exp + "; " + dom + "; path=/";
  $("#mobile-notice").slideUp("slow");
}
$(document).ready(function () {
  (function () {
    var result = /hide_mobile_notice\=([01])/.exec(document.cookie);
    if (result != null) {
      $("#mobile-notice").slideUp("fast");
    }
  })();
});
