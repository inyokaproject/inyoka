/**
 * static.js.forum
 * ~~~~~~~~~~~~~~~
 *
 * JavaScript for the forum.
 *
 * :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
 * :license: BSD, see LICENSE for more details.
 */

$(function () { /* collapsable elements for the input forms */
  $('dt.collapse').each(function () {
    $(this).nextWhile('dd').addClass('collapse_enabled').toggle($(this).hasClass('has_errors'));
    $(this).click(function () {
      $(this).toggleClass('collapsed').nextWhile('dd').toggle();
    }).addClass('collapse_enabled collapsed');
  });

  /* poll helpers */
  (function () {
    $('#id_add_option').click(function addReply() {
      count = $('.newtopic_polls_replies').length;
      $($('.newtopic_polls_replies')[count - 1]).after('<dd class="newtopic_polls_replies collapse_enabled">Antwort ' + (count + 1) + ': <input type="text" name="options" value="" /></dd>');
      $('#id_add_option').remove();
      $($('.newtopic_polls_replies')[count]).append(' <input type="submit" name="add_option" value="Weitere Antwort" ' + 'id="id_add_option" />');
      $('#id_add_option').click(addReply);
      return false;
    });
  })();

  /* expand and collapse button for categories */
  (function () {
    var toggleState = {};
    $('<a href="#" class="collapse" />').click(function () {
      var head = $(this).parent().parent();
      head.nextUntil('tr.head').toggle();
      $(this).toggleClass('collapsed');
      $('table.category_box tr.head').each(function () {
        toggleState[this.id.substr(9)] = $('a.collapsed', this).length > 0;
      });
      var hidden = [];
      for (var state in toggleState) {
        if (toggleState[state]) hidden.push(state);
      }
      $.get('/', {
        __service__: 'forum.toggle_categories',
        hidden: hidden
      });
      return false;
    }).prependTo('table.category_box tr.head th');

    /* this function is used by the index template */
    hideForumCategories = function (hidden_categories) {
      $('table.category_box tr.head').each(function () {
        if ($.inArray(parseInt(this.id.substr(9), 10), hidden_categories) >= 0) {
          $(this).nextUntil('tr.head').hide();
          $('a.collapse', this).addClass('collapsed');
        }
      });
    };
  })();

  function doAction(type, slug, tags, callback) {
    // Get the matching string for replacement. Since the two buttons (top and bottom)
    // are in the same macro we just need to check for one buttons text at all.
    var action = "";
    var new_text = "";

    var text = $(tags[0]).text();

    switch (text) {
    case 'abbestellen':
      action = 'unsubscribe';
      new_text = 'abonnieren';
      break;
    case 'abonnieren':
      action = 'subscribe';
      new_text = 'abbestellen';
      break;
    case 'als ungelöst markieren':
      action = 'mark_unsolved';
      new_text = 'als gelöst markieren';
      break;
    case 'als gelöst markieren':
      action = 'mark_solved';
      new_text = 'als ungelöst markieren';
      break;
    }

    var url = "/?__service__=forum." + action;

    $.post(url, {
      type: type,
      slug: slug
    }, function (data, status, xhr) {
      // Bind new events and change button's text.
      if (xhr.status == 200) {
        $(tags).fadeOut('fast');
        $(tags).text(new_text);
        $(tags).fadeIn('fast');
        if (typeof callback == 'function') callback();
      }
    });
  }

//  (function () {
//    $('a.action_subscribe.subscribe_topic').each(function () {
//      $(this).click(function () {
//        doAction('topic', $(this).attr('id'), $('a.action_subscribe.subscribe_topic'));
//        return false;
//      });
//    });
//
//    $('a.action_subscribe.subscribe_forum').each(function () {
//      $(this).click(function () {
//        doAction('forum', $(this).attr('id'), $('a.action_subscribe.subscribe_forum'));
//        return false;
//      });
//    });
//
//    $('a.solve_topic').each(function () {
//      $(this).click(function () {
//        doAction('topic', $(this).attr('id'), $('a.solve_topic'), function () {
//          // switch classes
//          if ($('a.solve_topic').hasClass('action_solve')) {
//            $('a.solve_topic').removeClass('action_solve');
//            $('a.solve_topic').addClass('action_unsolve');
//            var span = $('span.status_unsolved');
//            span.fadeOut('fast');
//            span.removeClass('status_unsolved');
//            span.addClass('status_solved');
//            span.text('gelöst');
//            span.fadeIn('fast');
//          } else {
//            $('a.solve_topic').removeClass('action_unsolve');
//            $('a.solve_topic').addClass('action_solve');
//            var span = $('span.status_solved');
//            span.fadeOut('fast');
//            span.removeClass('status_solved');
//            span.addClass('status_unsolved');
//            span.text('ungelöst');
//            span.fadeIn('fast');
//          }
//        });
//        return false;
//      });
//    });
//  })();

  /* Display some more informations about the ubuntu version */
  (function () {
    $('select[name="ubuntu_version"]').change(function () {
      var text_unstable = '<a href="{LL}">Dies</a> ist die momentane <a href="http://wiki.ubuntuusers.de/Entwicklungsversion">Entwicklungsversion</a> von Ubuntu';
      var text_lts = '<a href="{LL}">Dies</a> ist eine <a href="http://wiki.ubuntuusers.de/Long_Term_Support">LTS (Long Term Support)</a> Version';
      var text_current = '<a href="{LL}">Dies</a> ist die momentan <a href="http://wiki.ubuntuusers.de/Downloads">aktuelle Version</a> von Ubuntu';
      var url = "/?__service__=forum.get_version_details";
      var version_str = $(this).find('option:selected').val();

      /* Only send an request if there's really a Version selected */
      if (!$.trim(version_str)) {
        return false;
      }

      var with_link = function (text, data) {
        return text.replace(/\{LL\}/, data.link);
      };

      $.getJSON(url, {
        version: version_str
      }, function (data) {
        if (data.dev) {
          $('span#version_info').attr('class', 'unstable').html(with_link(text_unstable, data));
        } else if (data.lts) {
          $('span#version_info').attr('class', 'lts').html(with_link(text_lts, data));
        } else if (data.current) {
          $('span#version_info').attr('class', 'current').html(with_link(text_current, data));
        } else {
          $('span#version_info').attr('class', '').text('');
        }
      });

      return false;
    });
  })();


  /* Special Topic Split functions that ease the moderation pain. */
  (function() {
    // Bind events so that we can update the user session
    // properly on interaction.
    $('.splitinfo input').live('click', function() {
      var self = $(this);
      var topic = location.href.slice(location.href.indexOf('/topic/') + 7);
      topic = topic.substring(0, topic.indexOf('/'));

      post = self.attr('value');
      type = self.attr('type');
      other = $('.splitinfo input[name="' + (type == 'radio' ? 'select' : 'start') + '"]');

      if (self.is(':checked')) {
        other.removeAttr('checked');
      }

      if (other.is(':checked')) {
        self.removeAttr('checked');
      }

      var url = '/?__service__=forum.mark_topic_split_point';
      if (self.attr('type') == 'radio') {
        $.getJSON(url, {
          post: self.attr('value'),
          from_here: true,
          topic: topic
        });
      } else if (self.attr('type') == 'checkbox') {
        $.getJSON(url, {
          post: self.attr('value'),
          topic: topic
        })
      }

      return true;
    });
  })();
});
