/*
    static.js.FeedSelector
    ~~~~~~~~~~~~~~~~~~~~~~~~

    JavaScript for the feed selector.

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
*/

(function () {
  if (navigator.userAgent.indexOf('KHTML') >= 0) return;

  var FEED_COUNTS = [10, 20, 30, 50, 75, 100];
  var FORUM_URL = 'http://forum.' + $BASE_DOMAIN_NAME + '/';
  var WIKI_URL = 'http://wiki.' + $BASE_DOMAIN_NAME + '/';
  var IKHAYA_URL = 'http://ikhaya.' + $BASE_DOMAIN_NAME + '/';
  var PLANET_URL = 'http://planet.' + $BASE_DOMAIN_NAME + '/';

  $(document).ready(function () {
    $('#id_forum_forum').change(function () {
      $('#id_forum_component_forum')[0].checked = true;
    });
    $('#forum').change(makeForumFeedURL);
    $('#ikhaya').change(makeIkhayaFeedURL);
    $('#planet').change(makePlanetFeedURL);
    $('.feed_count').after(' <span class="feed_count_adjust">');
    $('.feed_count_adjust').append('<img class="feed_count_increase" src="' + $STATIC_URL + 'img/arrow-up.gif" />')
                           .append('<img class="feed_count_decrease" src="' + $STATIC_URL + 'img/arrow-down.gif" />');
    $('.feed_count_increase').click(function () {
      var count = document.getElementById($(this).parent().siblings()[0].htmlFor);
      count.value = _next(count.value, FEED_COUNTS);
      $(count.form).change();
    }).css('cursor', 'pointer');
    $('.feed_count_decrease').click(function () {
      var count = document.getElementById($(this).parent().siblings()[0].htmlFor);
      count.value = _previous(count.value, FEED_COUNTS);
      $(count.form).change();
    }).css('cursor', 'pointer');
  });

  function makeForumFeedURL() {
    var
    errors = {},
        data = {},
        form = $('#forum')[0];

    if (form.component[0].checked) data.component = '*';
    else if (form.component[1].checked) {
      data.component = 'forum';
      if (form.forum.selectedIndex <= 0) errors.forum = 'Bitte ein Forum auswählen!';
      else data.forum = form.forum.options[form.forum.options.selectedIndex].value;
    } else errors.component = 'Ungültige Auswahl!';

    _getCountMode(form, data, errors);
    var OK = true;
    for (var _ in errors) {
      OK = false;
      break;
    }
    if (OK) {
      if (data.component == '*') feed_url = FORUM_URL + 'feeds/' + data.mode + '/' + data.count + '/';
      else feed_url = FORUM_URL + 'feeds/' + data.component + '/' + data.forum + '/' + data.mode + '/' + data.count + '/';
      if (!$('#forum_feed_url').length) {
        $('#forum_submit_p').prepend('<strong>Adresse des Feeds:</strong> ' + '<a id="forum_feed_url" href="about:blank">-</a></span><br/>');
      }
      $('#forum_feed_url').text(feed_url).attr('href', feed_url);
      return feed_url;
    } else
    return false;
  }

  function makeIkhayaFeedURL() {
    var errors = {};
    var data = {};
    var form = document.getElementById('ikhaya');

    data.category = form.category.options[form.category.options.selectedIndex].value;
    _getCountMode(form, data, errors);

    var OK = true;
    for (var _ in errors) {
      OK = false;
      break;
    }
    if (OK) {
      if (data.category == '*') feed_url = IKHAYA_URL + 'feeds/' + data.mode + '/' + data.count + '/';
      else feed_url = IKHAYA_URL + 'feeds/' + data.category + '/' + data.mode + '/' + data.count + '/';
      if (!$('#ikhaya_feed_url').length) {
        $('#ikhaya_submit_p').prepend('<strong>Adresse des Feeds:</strong> ' + '<a id="ikhaya_feed_url" href="about:blank">-</a></span><br/>');
      }
      $('#ikhaya_feed_url').text(feed_url).attr('href', feed_url);
      return feed_url;
    } else
    return false;
  }

  function makePlanetFeedURL() {
    var
    errors = {},
        data = {},
        OK = true,
        form = document.getElementById('planet');
    _getCountMode(form, data, errors);

    for (var _ in errors) {
      OK = false;
      break;
    }
    if (OK) {
      feed_url = PLANET_URL + 'feeds/' + data.mode + '/' + data.count + '/';
      if ($('#planet_feed_url').length) {
        $('#planet_submit_p').prepend('<strong>Adresse des Feeds:</strong> ' + '<a id="planet_feed_url" href="about:blank">-</a></span><br/>');
      }
      $('#planet_feed_url').text(feed_url).attr('href', feed_url);
      return feed_url;
    } else
    return false;
  }

  function _closest(n, l) {
    if (n < l[0]) return l[0];
    for (var i = 0; i <= l.length; ++i) {
      if (n < l[i]) return (n - l[i - 1] < l[i] - n && l[i - 1] || l[i]);
    }
    return l[l.length - 1];
  }

  function _previous(n, l) {
    for (var i = 0; i < l.length; i++)
    if (n == l[i]) break;
    return i >= 1 ? l[i - 1] : l[i];
  }

  function _next(n, l) {
    for (var i = 0; i < l.length; i++)
    if (n == l[i]) break;
    return i < (l.length - 1) ? l[i + 1] : l[i];
  }

  function _getCountMode(form, data, errors) {
    // fetches count and mode from form, putting the data into ``data`` and adding error messages to ``errors``
    for (var i = 0; i < form.mode.length; ++i) {
      if (form.mode[i].checked) data.mode = form.mode[i].value;
    }
    if (!data.mode) errors.mode = 'Bitte eine Art auswählen!';

    if (isNaN(form.count.value) || form.count.value.length < 1) {
      errors.count = 'Bitte eine Zahl zwischen 10 und 100 eingeben!';
      form.count.value = data.count || '20';
    } else data.count = form.count.value = _closest(form.count.value, FEED_COUNTS);
  }
})();
