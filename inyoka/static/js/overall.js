/**
 * js.overall
 * ~~~~~~~~~~
 *
 * Some general scripts for the whole portal (requires jQuery).
 *
 * :copyright: (c) 2007-2025 by the Inyoka Team, see AUTHORS for more details.
 * :license: BSD, see LICENSE for more details.
 */

$(document).ready(function () {
  // add a hide message link to all flash messages
  $.each($('div.message'), function (i, elm) {
    const button = $('<button class="hide" aria-label="close"><span aria-hidden="true">×</span></button>');
    $(elm).prepend(button.click(function () {
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

  // searchintegration for duckduckgo
  // only temporarily, done fast and thus a bit hacky!
  (function () {
    // object that lists, in which locations the user can search
    // schema: { internalID : displayedTextToUser }
    const searchAreas = {"portal": "Überall", "forum": "Forum", "ikhaya": "Ikhaya",
                       "planet": "Planet", "wiki": "Wiki"};

    // search area in which the user wants to find something; defaults to active app
    let selectedArea = $("form.search").attr("data-active-app");

    // via the popup a different searcharea is selected
    let popup = $('<ul class="search_area" />');
    let popupBuild = false;

    // init the values of searchField with default values
    const searchField = $('.search_query')
    searchField.addClass('area_' + selectedArea);
    searchField.attr('placeholder', searchAreas[selectedArea]);

    /* as the user wants to start the search, the search is limited to the
     * selected subdomain. The last information is added by prefixing the
     * search words with `site:example.org` in a hidden field.
     * The search engine will only recognize the value of the hidden input.
     */
    document.getElementsByClassName("search")[0].onsubmit = (function() {
      $('form.search input[name=q]').val(function() {
        const searchWords = searchField.val();

        switch(selectedArea) {
          case "forum":
          case "ikhaya":
          case "planet":
          case "wiki":
            return "site:" + selectedArea + "." + $BASE_DOMAIN_NAME + " " + searchWords;
          default: // equals "portal"
            return "site:" + $BASE_DOMAIN_NAME + " " + searchWords;
        }
      });

      $('form.search input[name=host]').remove(); // remove to prevent two site:-parameters
    });

    const expander = $('<div class="search_expander" />');
    expander.click(function () {
      if (!popupBuild) {
        popupBuild = true;

        // build popup
        // for each area the user can search, insert a li to the ul/popup
        $.each(searchAreas, function (key, value) {
          const listItemArea = key;

          const item = $('<li />').text(value);
          item.addClass('area_' + key);
          item.click(function() {
            // update classes of searchField → change icon of area
            searchField.removeClass('area_' + selectedArea);
            selectedArea = listItemArea;
            searchField.addClass('area_' + selectedArea);

            // update .active-class in the popup list
            // → current selected item will be displayed bold
            $('li.active', popup).removeClass('active');
            $(this).addClass('active');

            searchField.attr('placeholder', value);
            searchField.focus();

            popup.toggle();
          }).appendTo(popup);

          if (listItemArea === selectedArea) item.addClass('active');
        });

        popup.prependTo('form.search');
      } else { // popupBuild = true
         popup.toggle();
      }
    });
    expander.insertAfter(searchField);

    $(document).click(function (e) {
      if(e.target.className !== "search_expander") {
        popup.hide();
      }
    });

    /* quickfix for Firefox
     * otherwise the search button will stay disabled, if you go back one page
     * see https://bugzilla.mozilla.org/show_bug.cgi?id=443289#c6
     */
    window.addEventListener('pageshow', PageShowHandler, false);
    window.addEventListener('unload', UnloadHandler, false);

    function PageShowHandler() {
        window.addEventListener('unload', UnloadHandler, false);
    }

    function UnloadHandler() {
        window.removeEventListener('unload', UnloadHandler, false);
    }
  })();

  // add a sidebar toggler if there is a sidebar
  (function () {
    const sidebar = $('.navi_sidebar');
    if (!sidebar.length) return;
    const togglebutton = $('<button class="navi_toggle" aria-label="Navigation ausblenden">↑</button>').click(function () {
      $('.content').toggleClass('content_sidebar');
      sidebar.toggle();
      if (sidebar.is(':visible')) {
        this.innerText = "↑";
      } else {
        this.innerText = "↓";
      }

      if ($IS_LOGGED_IN) $.get('/?__service__=portal.toggle_sidebar', {
        hide: !sidebar.is(':visible'),
        component: window.location.hostname.split('.')[0]
      });

      return false;
    }).insertAfter('.breadcrumb.-top > ol');
    if ($SIDEBAR_HIDDEN) togglebutton.click();
  })();

  // use javascript to deactivate the submit button on click
  // we don't make the elements really disabled because then
  // the button won't appear in the form data transmitted
  let form_submitted = false;
  $('form').submit(function () {
    if ($(this).hasClass('nosubmitprotect')) {
      return true;
    }
    if (form_submitted) {
      return false;
    }
    $('input[type="submit"]').addClass('disabled');
    form_submitted = true;
  });

  // Warn users from leaving the page with unsaved form data
  // https://github.com/inyokaproject/inyoka/issues/1036
  window.addEventListener("beforeunload", function(event) {
    if (form_submitted) {
      // if a form was submitted, no dialogue should show
      return undefined;
    }

    function _show_dialog() {
        // Cancel the event.
        event.preventDefault();
    }

    // check if checkbox values changed
    for (const element of document.querySelectorAll('input[type="checkbox"]')) {
      if (element.checked !== element.defaultChecked) {
        _show_dialog();
        // abort on first changed input field
        return;
      }
    }

    // check if select values changed
    for (const element of document.querySelectorAll('select')) {
      const default_selected = element.querySelector('option[selected]');
      if (default_selected !== null && default_selected.value !== element.value) {
        _show_dialog();
        // abort on first changed input field
        return;
      }
    }

    // check if other input values changed
    for (const element of document.querySelectorAll('input:not([type="checkbox"]), textarea')) {
      if (element.value !== element.defaultValue) {
        _show_dialog();
        // abort on first changed input field
        return;
      }
    }
  });

  $('div.code').add('pre.notranslate').each(function () {
    if (this.clientHeight < this.scrollHeight) {
      $(this).before('<div class="codeblock_resizer">vergrößern</div>')
             .css('height', '15em').css('max-height', 'none')
             .data('original_height', this.clientHeight);
    }
  });

  (function () {
    $('.codeblock_resizer').click(function () {
      const codeblock = $(this).next();
      if (!codeblock.hasClass('codeblock_expanded')) {
        codeblock.addClass('codeblock_expanded');
        codeblock.animate({
          'height': codeblock[0].scrollHeight
        }, 500);
        $(this).text('verkleinern');
      } else {
        codeblock.removeClass('codeblock_expanded');
        codeblock.animate({
          'height': codeblock.data('original_height')
        }, 500);
        $(this).text('vergrößern');
      }
    });
  })();

  // Add a version switcher to the `Fremdquelle` template.
  (function () {
    function set_version(link) {
      const version = $(link).text().toLowerCase();
      $(link).addClass('active').siblings('a').removeClass('active');
      const sel = $(link).parent();
      sel.siblings('pre').text(sel.data('deb-url-orig').replace(/VERSION/, version));
      return false;
    }

    $('.thirdpartyrepo-outer').each(function () {
      let versions = [],
          set_version_callback = function () {
          return set_version(this);
          },
          last_link;
      const classes = this.className.split(/\s+/);
      for (let i = 0; i < classes.length; i++) {
        if (classes[i].match(/^thirdpartyrepo-version-/)) {
          const version = classes[i].slice(23);
          versions.push(version);
        }
      }
      const sel = $('<div class="selector">').insertBefore($(this).find('.contents pre'));
      sel.prepend('<strong>Version: </strong>').data('deb-url-orig', $(this).find('.contents pre').text());
      for (let i = 0; i < versions.length; i++) {
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
  const result = /admin_menu\=([01])/.exec(document.cookie);
  let menu_status = (result != null) ? Number(result[1]) : 1;
  if (menu_status === 1) {
    $('.admin_link').removeClass('admin_link').addClass('admin_link_js').show();
    $('#admin_layer_button').addClass('highlight');
  } else {
    $('.admin_link').removeClass('admin_link').addClass('admin_link_js').hide();
  }
  $('.admin_link_hover').removeClass('admin_link_hover');
  $('#admin_layer_button').click(function () {
    $('.admin_link_js').each(function() {
      if ($(this).css('display') !== 'none') {
        $(this).fadeOut("fast", function () {$(this).hide();});
      } else {
        $(this).fadeIn("fast", function () {$(this).show();});
      }
    });
    menu_status = (menu_status === 0) ? 1 : 0;
    if (menu_status === 1) {
      $('#admin_layer_button').addClass('highlight');
    } else {
      $('#admin_layer_button').removeClass('highlight');
    }
    let admin_cookie = new Date();
    const admin_cookie_expires = admin_cookie.getTime() + (365 * 24 * 60 * 60 * 1000);
    admin_cookie.setTime(admin_cookie_expires);
    const exp = "expires=" + admin_cookie.toGMTString();
    let dom;
    if ($BASE_DOMAIN_NAME.indexOf(":") > 0) {
      dom = "domain=." + $BASE_DOMAIN_NAME.substring(0, $BASE_DOMAIN_NAME.indexOf(":"));
    } else {
      dom = "domain=." + $BASE_DOMAIN_NAME;
    }
    document.cookie = "admin_menu=" + menu_status + "; " + exp + "; " + dom + "; path=/";
  });

  // Quick Table Search
  // https://css-tricks.com/complete-guide-table-element/#article-header-id-25
  $('#table-search').keyup(function() {
    const regex = new RegExp($('#table-search').val(), "i");
    const rows = $('.edit-forum-permissions tbody tr:gt(1)');
    rows.each(function () {
      const title = $(this).children(":first-child").html()
      if (title.search(regex) !== -1) {
        $(this).show();
      } else {
        $(this).hide();
      }
    });
  });

  // column highlight inside table
  // https://css-tricks.com/row-and-column-highlighting/#article-header-id-2
  $(".edit-forum-permissions table").delegate('td','mouseover mouseleave', function(e) {
    if (e.type === 'mouseover') {
      $("colgroup").eq($(this).index()).addClass("hover");
      $(":first-child th").eq($(this).index()+1).addClass("hover");
    }
    else {
      $("colgroup").eq($(this).index()).removeClass("hover");
      $(":first-child th").eq($(this).index()+1).removeClass("hover");
    }
  });
});

String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
};
