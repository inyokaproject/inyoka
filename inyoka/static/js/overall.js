/**
 * js.overall
 * ~~~~~~~~~~
 *
 * Some general scripts for the whole portal (requires jQuery).
 *
 * :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
 * :license: GNU GPL, see LICENSE for more details.
 */

$(document).ready(function () {
  var loginForm = null;

  // preload images
  (function () {
    var container = $('<div>').appendTo('body').css({
      height: 0,
      overflow: 'hidden'
    });
    $.each([], function () {
      $('<img />').attr('src', $STATIC_URL + this).appendTo(container);
    });
  })();
  // Display the countdown
  (function () {
    var now = new Date ();
    var release = new Date ("October 13, 2011");
    var diff = release.getTime() - now.getTime();
    var days = Math.floor(diff / (1000*60*60*24))+1;
    var block = $("#counter");
    if (days > 21) {
      block.html('<a href="http://wiki.ubuntuusers.de/Oneiric_Ocelot"><img src="' + $STATIC_URL + 'img/portal/countdown/oneiricbanner_start.png" alt="Ubuntu 11.10"></a>');
    }
    if (days >= 1 && days<=21) {
      block.html('<a href="http://wiki.ubuntuusers.de/Oneiric_Ocelot"><img src="' + $STATIC_URL + 'img/portal/countdown/oneiricbanner_' + days + '.png" alt="Ubuntu 11.10"></a>');
    }
    if (days == 0) {
      block.html('<a href="http://wiki.ubuntuusers.de/Oneiric_Ocelot"><img src="' + $STATIC_URL + 'img/portal/countdown/oneiricbanner_soon.png" alt="Ubuntu 11.10"></a>');
    }
    if (days < 0) {
      block.html('<a href="http://wiki.ubuntuusers.de/Oneiric_Ocelot"><img src="' + $STATIC_URL + 'img/portal/countdown/oneiricbanner_here.png" alt="Ubuntu 11.10"></a>');
    }
  })();

  // add a hide message link to all flash messages
  $.each($('div.message'), function (i, elm) {
    $(elm).prepend($('<a href="#" class="hide" />').click(function () {
      if ($(this).parent().hasClass('global')) {
        $.post('/?__service__=portal.hide_global_message', {});
      }
      $(this).parent().slideUp('slow');
      return false;
    }));
  });

  // hide search words on click
  $('a.hide_searchwords').click(function () {
    $(this).parent().slideUp('slow');
    $('span.highlight').removeClass('highlight');
    return false;
  });

  // Make TOC links expandable.
  (function () {
    //Execute this function only when if there are tocs.
    if (!$('.toc').length) return;
    if (navigator.userAgent.match(/konqueror/i)) return;
    if (document.location.href.indexOf('/full/') >= 0) return;

    // create a link to hide a toc
    $('.toc .head').append(
    $('<a> [-]</a>').toggle(function () {
      $(this).text(' [+]').parent().next().slideUp('fast');
    }, function () {
      $(this).text(' [-]').parent().next().slideDown('fast');
    }));

    $('.toc').each(function () {
      toc = $(this);
      // find out depth of old toc, so we can make ours look the same in the beginning
      var _classes = this.className.split(/\s+/);
      for (var i = 0; i < _classes.length; i++) {
        if (_classes[i].match(/^toc-depth-(\d+)$/)) {
          tocDepth = parseInt(_classes[i].slice(10), 10);
          break;
        }
      }
      if (typeof tocDepth === 'undefined') return;

      // mark old toc for later deletion
      toc.find('ol').addClass('originaltoc');

      // create first level
      newtoc = $('<ol class="arabic"></ol>').hide().insertAfter(toc.find('.head'));

      // Create the whole tocTree
      var
      tocTree = "",
           // becomes Elementtree
          level = 1,
           // which toc-level am I?
          headerLinks = $('.headerlink'); // Give me all the headers
      for (var i = 0; i < headerLinks.length; i++) {
        var link = $(headerLinks[i]).parent().attr("id");
        var linkText = $(headerLinks[i]).parent().text();
        var linkText = linkText.substring(0, linkText.length - 1).htmlEscape();
        var thisClass = $(headerLinks[i]).parent().parent().attr("class");

        if (i < headerLinks.length - 1) {
          // we are not the last headline
          nextClass = $(headerLinks[i + 1]).parent().parent().attr("class");
        } else {
          // after the last headline a first-level HL would follow
          nextClass = "section_1";
        }

        nextLevel = parseInt(nextClass.match(/^section_(\d+)$/)[1], 10);
        if (nextLevel > level) {
          // append "<li><ol>" !! without closing tags !!
          tocTree += '<li><a href="#' + link + '" class="crosslink">' + linkText + '</a>';
          tocTree += '<ol class="arabic toc-item-depth-' + level + '">';
          level++;
        } else {
          //  There is no deeper level
          tocTree += '<li><a href="#' + link + '">' + linkText + '</a></li>';
          while (nextLevel < level) {
            tocTree += '</ol></li>';
            level--;
          }
        }
      }
      newtoc.append(tocTree);

      toc.find('.originaltoc').remove();
      newtoc.show();
      //we have to hide all sublevels, create [+/-], and the click-event
      toc.find(":not(.originaltoc) ol").each(function () {
        folder = $('<a class="toctoggle"> [-] </a>');
        folder.insertBefore($(this));
        folder.toggle(

        function () {
          $(this).text(' [+] ').next().slideUp('fast');
        }, function () {
          $(this).text(' [-] ').next().slideDown('fast');
        });

        var _classes = this.className.split(/\s+/);
        for (var i = 0; i < _classes.length; i++) {
          if (_classes[i].match(/^toc-item-depth-(\d+)$/)) {
            curDepth = parseInt(_classes[i].slice(15), 10);
            break;
          }
        }
        if (curDepth >= tocDepth) {
          folder.click();
        }
      });

    });
  }());

  // if we have JavaScript we style the search bar so that it looks
  // like a firefox search thingy and apply some behavior
  (function () {
    if (navigator.appName.toLowerCase() == 'konqueror') return;
    var
    initialized = false,
        $currentSearchArea = $('select.search_area').val(),
        $currentAreaName = $('select.search_area option:selected').html(),
        areaPopup = $('<ul class="search_area" />'),
        searchArea = $('select.search_area').hide();
    $('.search_query').addClass('area_' + $currentSearchArea);
    $('form.search').submit(function () {
      var url = $(this).attr('action'),
          tmp = $('input.search_query').val();
      if ($('input.search_query').hasClass('default_value')) tmp = '';
      if (tmp) {
        url += '?query=' + encodeURIComponent(tmp) + '&area=' + $currentSearchArea;
      }
      document.location.href = url;
      return false;
    }).append($('<div class="search_expander" />').click(function () {
      if (!initialized) {
        initialized = true;
        $('option', searchArea).each(function () {
          var currentArea = $(this).val();
          var item = $('<li />').text($(this).text()).addClass('area_' + $(this).val()).click(function () {
            $currentAreaName = $(this).html();
            $('.search_query').removeClass('area_' + $currentSearchArea);
            $currentSearchArea = currentArea;
            $currentAreaName = $('select.search_area option[value=' + $currentSearchArea + ']').html();
            $('.search_query').addClass('area_' + $currentSearchArea);
            $('li', areaPopup).each(function () {
              $(this).removeClass('active');
            });
            $(this).addClass('active').parent();
            $('.search_query').focus();
            areaPopup.hide();
            return false;
          }).appendTo(areaPopup);
          if (currentArea == $currentSearchArea) item.addClass('active');
        });
        areaPopup.prependTo('form.search');
      } else areaPopup.toggle();
      return false;
    }));
    $('.search_query').addClass('search_query_js').blur(function () {
      var e = $(this);
      if (e.val() == '' || e.val() == $currentAreaName) e.addClass('default_value').val($currentAreaName);
    }).focus(function () {
      var e = $(this);
      if (e.hasClass('default_value')) e.val('').removeClass('default_value');
    });
    $('.search_query').blur();
    $(document).click(function () {
      if (areaPopup.is(':visible')) areaPopup.hide();
      if (loginForm && loginForm.is(':visible')) loginForm.slideUp();
    });
  })();

  // add a sidebar toggler if there is an sidebar
  (function () {
    var sidebar = $('.navi_sidebar');
    if (!sidebar.length) return;
    var togglebutton =
    $('<button class="navi_toggle_up" title="Navigation ausblenden" />').click(function () {
      $('.content').toggleClass('content_sidebar');
      sidebar.toggle();
      togglebutton.toggleClass('navi_toggle_up').toggleClass('navi_toggle_down');
      if ($IS_LOGGED_IN) $.get('/?__service__=portal.toggle_sidebar', {
        hide: !sidebar.is(':visible'),
        component: window.location.hostname.split('.')[0]
      });
      return false;
    }).insertAfter('form.search');
    if ($SIDEBAR_HIDDEN) togglebutton.click();
  })();

  // use javascript to deactivate the submit button on click
  // we don't make the elements really disabled because then
  // the button won't appear in the form data transmitted
  (function () {
    var submitted = false;
    $('form').submit(function () {
      if ($(this).hasClass('nosubmitprotect')) return true;
      if (submitted) return false;
      $('input[type="submit"]').addClass('disabled');
      submitted = true;
    });
  })();

  // add links to the "package" macro
  $('.package-list, .builddeps').each(function (i, elm) {
    var tmp = $('.bash', elm);
    var apt = tmp[0];
    var aptitude = tmp[1];
    $(aptitude).hide();
    $($('p', elm)[0]).append(
      $('<a>apt-get</a>').click(function () {
        $(this).parent().children().css('font-weight', '');
        $(this).css('font-weight', 'bold');
        $(apt).show();
        $(aptitude).hide();
      }).click(),
      ' ',
      $('<a>aptitude</a>').click(function () {
        $(this).parent().children().css('font-weight', '');
        $(this).css('font-weight', 'bold');
        $(aptitude).show();
        $(apt).hide();
     })
    );
    if ($(elm).hasClass('package-list')) {
      $($('p', elm)[0]).append(
        ' ',
        $('<a>apturl</a>').attr('href', 'apt://' + $.trim($(apt).text()).split(' ').slice(3).join(','))
      );
    }
  });

  $('div.code').add('pre').each(function () {
    if (this.clientHeight < this.scrollHeight) {
      $(this).before('<div class="codeblock_resizer" title="vergrößern">vergrößern</div>')
             .css('height', '15em').css('max-height', 'none')
             .data('original_height', this.clientHeight);
    }
  });

  (function () {
    if (navigator.appName.toLowerCase() == 'konqueror') return;
    $('.codeblock_resizer').click(function () {
      $codeblock = $(this).next();
      if (!$codeblock.hasClass('codeblock_expanded')) {
        $codeblock.addClass('codeblock_expanded');
        $codeblock.animate({
          'height': $codeblock[0].scrollHeight
        }, 500);
        this.innerHTML = this.title = 'verkleinern';
      } else {
        $codeblock.removeClass('codeblock_expanded');
        $codeblock.animate({
          'height': $codeblock.data('original_height')
        }, 500);
        this.innerHTML = this.title = 'vergrößern';
      }
    });
  })();

  // Add a version switcher to the `PPA` template.
  (function () {
    var SHORT_NOTATION_VERSIONS = ['karmic', 'lucid', 'maverick'];

    var set_version = function (dom) {
      var link = $(dom);
      group = link.parent().parent();
      version = link.text().toLowerCase();
      group.find('.ppa-code').remove();
      sel = group.find('.selector');

      link.addClass('active').siblings('a').removeClass('active');

      sel.after('<pre class="ppa-code">' + group.data('long_notation_text').replace(/VERSION/, version) + '</div></pre>');
      if ($.inArray(version, SHORT_NOTATION_VERSIONS) > -1) {
        sel.after('<p class="ppa-code">Für die <strong>sources.list</strong>:</p>');
        sel.after('<p class="ppa-code">' + group.data('short_notation_text') + '</p>');
      }
      return false;
    };

    $('.ppa-list-outer').each(function () {
      $this = $(this);
      var versions = [],
          version;
      classes = this.className.split(/\s+/);
      for (var i = 0; i < classes.length; i++) {
        if (classes[i].match(/^ppa-version-/)) {
          version = classes[i].slice(12);
          versions.push(version);
        }
      }

      $this.data('short_notation_text', $this.find('.ppa-list-short-code .contents p').html());
      $this.data('long_notation_text', $this.find('.ppa-list-long-code .contents pre').html());

      $this.children('.contents').remove();
      sel = $('<p class="selector">').appendTo($this);
      sel.prepend('<strong>Version: </strong>');
      var set_version_callback = function () {
        return set_version(this);
      };
      for (var i = 0; i < versions.length; i++) {
        version = versions[i];
        latest_link = $('<a href="#">').text(version.substr(0, 1).toUpperCase() + version.substr(1))
                                       .click(set_version_callback).appendTo(sel).after('<span class="linklist"> | </span>');
      }
      latest_link.next('.linklist').remove(); // remove last |
      set_version(latest_link[0]);
    });
  })();

  // Add a version switcher to the `Fremdquelle` template.
  (function () {
    var set_version = function (link) {
      version = $(link).text().toLowerCase();
      $(link).addClass('active').siblings('a').removeClass('active');
      sel = $(link).parent();
      sel.siblings('pre').text(sel.data('deb-url-orig').replace(/VERSION/, version));
      return false;
    };

    $('.thirdpartyrepo-outer').each(function () {
      var versions = [],
          set_version_callback = function () {
          return set_version(this);
          },
          last_link;
      classes = this.className.split(/\s+/);
      for (var i = 0; i < classes.length; i++) {
        if (classes[i].match(/^thirdpartyrepo-version-/)) {
          version = classes[i].slice(23);
          versions.push(version);
        }
      }
      sel = $('<div class="selector">').insertBefore($(this).find('.contents pre'));
      sel.prepend('<strong>Version: </strong>').data('deb-url-orig', $(this).find('.contents pre').text());
      for (var i = 0; i < versions.length; i++) {
        last_link = $('<a href="#">').text(versions[i].substr(0, 1).toUpperCase() + versions[i].substr(1))
                                      .click(set_version_callback).appendTo(sel).after('<span class="linklist"> | </span>');
      }
      last_link.next().remove(); // remove last |
      set_version(last_link[0]);
      return true;
    });
  })();

  // the following lines add the JavaScript administration layer. Therefor we first remove
  // css legacy support (hover tags and icons will be visible) and add each element a JS class.
  // Later, each click on `#admin_layer_button` will iterate through all tags with `admin_link_js`
  // class and toggle their visibility.
  // alert(document.cookie);
  var result = /admin_menu\=([01])/.exec(document.cookie);
  var menu_status = (result != null) ? result[1] : 1;
  if (menu_status == 1) {
    $('.admin_link').removeClass('admin_link').addClass('admin_link_js').show();
    $('#admin_layer_button').addClass('highlight');
  } else {
    $('.admin_link').removeClass('admin_link').addClass('admin_link_js').hide();
  }
  $('.admin_link_hover').removeClass('admin_link_hover');
  $('#admin_layer_button').click(function () {
    $('.admin_link_js').each(function() {
      if ($(this).css('display') != 'none') {
        $(this).fadeOut("fast", function () {$(this).hide();});
      } else {
        $(this).fadeIn("fast", function () {$(this).show();});
      }
    });
    menu_status = (menu_status == 0) ? 1 : 0;
    if (menu_status == 1) {
      $('#admin_layer_button').addClass('highlight');
    } else {
      $('#admin_layer_button').removeClass('highlight');
    }
    var admin_cookie = new Date();
    var admin_cookie_expires = admin_cookie.getTime() + (365 * 24 * 60 * 60 * 1000);
    admin_cookie.setTime(admin_cookie_expires);
    var exp = "expires=" + admin_cookie.toGMTString();
    var dom;
    if ($BASE_DOMAIN_NAME.indexOf(":") > 0) {
      dom = "domain=." + $BASE_DOMAIN_NAME.substring(0, $BASE_DOMAIN_NAME.indexOf(":"));
    } else {
      dom = "domain=." + $BASE_DOMAIN_NAME;
    }
    document.cookie = "admin_menu=" + menu_status + "; " + exp + "; " + dom + "; path=/";
  });
});

(function() {
  /* OpenID Integration */
  OpenIDHelper = Class.$extend({
    __init__: function(target, openid_providers) {
      var self = this;
      var target = $(target);

      // hide password field if it looks like we're getting and openid
      var elements = ['input[name="password"]', 'label[for="id_password"]', 'label[for="js_login_password"]'];
      $(target).keydown(function() {
        if ($(target).val().slice(0, 4) == 'http') {
          $('input[name="password"]').val('');
          for (idx in elements)
            $(elements[idx]).hide();
        } else {
          for (idx in elements)
            $(elements[idx]).show();
        }
      });

      // Add common OpenID providers
      for (var provider in openid_providers) {
        var name = openid_providers[provider].name;
        var element = $('<img src="' + $STATIC_URL + 'img/openid/' + provider + '.png" class="openid_logo" id="openid_' + provider + '" alt="' + name + '" title="' + name + ' benutzen" />')
          .click(function() {
            $(target).val('');
            p = $(this).attr('id').substring(7);
            if (openid_providers[p]['url'] == null) {
              $(target).val('http://');
              $(target).focus();
            } else {
              self.setSelection($(target), openid_providers[p]['url'], '{username}', true);
            }
          })
          .css('cursor', 'pointer');

        element.insertAfter($(target));
      }
    },

    setSelection: function(area, text, match, reselect) {
      var t = $(area)[0];
      if (typeof t.selectionStart != 'undefined') {
        var
          start = text.indexOf(match),
          end = text.indexOf(match) + match.length;
        var
          s1 = t.value.substring(0, start),
          s2 = t.value.substring(end);

        t.value = s1 + text + s2;
        if (start == -1) {
          area.closest('form').submit();
          return;
        }
        t.focus();
        if (reselect) {
          t.selectionStart = start;
          t.selectionEnd = end;
        }
        else
          t.selectionEnd = t.selectionStart = start + text.length;
      }
      else if (typeof document.selection != 'undefined') {
        t.focus();
        var range = document.selection.createRange();
        range.text = text;
      }
    }
  });
})();

String.prototype.htmlEscape = function () {
  return this.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/, "&quot;");
};

String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
};
