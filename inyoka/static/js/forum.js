/**
 * static.js.forum
 * ~~~~~~~~~~~~~~~
 *
 * JavaScript for the forum.
 *
 * :copyright: (c) 2007-2025 by the Inyoka Team, see AUTHORS for more details.
 * :license: BSD, see LICENSE for more details.
 */

$(function () {

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

  /* Display some more information about the ubuntu version */
  (function () {
    $('select[name="ubuntu_version"]').change(function () {
      const url = "/?__service__=forum.get_version_details";
      const version_str = $(this).find('option:selected').val();

      /* Only send a request if there's really a Version selected */
      if (!$.trim(version_str)) {
        return false;
      }

      $.getJSON(url, {
        version: version_str
      }, function (data) {
        if (data.dev) {
          const text_unstable = `<a href="${data.link}">Dies</a> ist die momentane <a href="https://wiki.${$BASE_DOMAIN_NAME}/Entwicklungsversion">Entwicklungsversion</a> von Ubuntu`;
          $('span#version_info').attr('class', 'unstable').html(text_unstable);
        } else if (data.lts) {
          const text_lts = `<a href="${data.link}">Dies</a> ist eine <a href="https://wiki.${$BASE_DOMAIN_NAME}/Long_Term_Support">LTS (Long Term Support)</a> Version`;
          $('span#version_info').attr('class', 'lts').html(text_lts);
        } else if (data.current) {
          const text_current = `<a href="${data.link}">Dies</a> ist die momentan <a href="https://wiki.${$BASE_DOMAIN_NAME}/Downloads">aktuelle Version</a> von Ubuntu`;
          $('span#version_info').attr('class', 'current').html(text_current);
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
    $('.splitinfo input').on('click', function() {
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

  /* Submit Post Form with Ctrl+Enter. */
  (function() {
    const carriageReturn = 13;
    const newLine = 10;

    $("#id_text").keypress(function (event) {
      const enterPressed = event.keyCode === newLine || event.keyCode === carriageReturn;
      if (enterPressed && event.ctrlKey &&
          confirm("Möchtest du den Beitrag absenden?")) {
        document.getElementById("submit_post").click()
      }
    });
  })();
});
