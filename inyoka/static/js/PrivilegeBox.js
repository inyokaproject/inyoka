/**
 * js.PrivilegeBox
 * ~~~~~~~~~~~~~~~
 *
 * :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
 * :license: BSD, see LICENSE for more details.
 */
(function () {
  PrivilegeBox = function (container, forums, privileges) {
    this.mapping = {};
    var id, name, positive, negative, result, selected_forums = [],
        self = this,
        list = $('<ul class="forums" />');
    this.container = $(container);
    $.each(forums, function (i, forum) {
      var id = forum[0];
      var name = forum[1];
      var positive = forum[2];
      var negative = forum[3];
      var result;
      self.mapping[id] = positive.concat($.map(negative, function (o) {
        return o * -1;
      }));
      var li = $('<li />').text(name).attr('id', 'forum_' + id);
      if (positive != '' || negative != '') {
        li.css('color', '#E00');
      }
      list.append(li.click(function (evt) {
        var id = $(this).attr('id').split('_')[1];
        if (evt.ctrlKey) {
          var pos = $.inArray(id, selected_forums);
          if (pos > -1 && selected_forums.length > 1) {
            selected_forums.splice(pos, 1);
          }
          if (pos == -1) {
            selected_forums.push(id);
          }
        } else {
          selected_forums = [id];
        }
        $(this).parent().children().removeClass('active');
        $.each(selected_forums, function (i, forum) {
          $('#forum_' + forum).addClass('active');
        });
        if (selected_forums.length == 1) {
          var forum = selected_forums[0];
          headline.text($('#forum_' + forum).text());
          $.each(privileges, function (id, name) {
            id = parseInt(id, 10);
            var s;
            if ($.inArray(id, self.mapping[forum]) > -1) s = '1';
            else if ($.inArray(id * -1, self.mapping[forum]) > -1) s = '-1';
            else s = '0';
            $('#priv_' + id + '_' + s).attr('checked', 'checked');
          });
        } else {
          headline.text(selected_forums.length + ' Foren');
          $('input[type=radio]', self.container).attr('checked', '');
        }
      }));
    });
    this.container.html('');
    this.container.append(list);
    var content = $('<div class="privileges"></div>').appendTo(this.container);
    var headline = $('<h5 />').appendTo(content);
    var priv_list = $('<dl />').appendTo(content);
    $.each(privileges, function (id, name) {
      var radio = function (val, text) {
        return $('<input type="radio" />').attr({
          name: 'priv_' + id,
          value: val,
          id: 'priv_' + id + '_' + val
        }).change(function () {
          var priv_data = [];
          self.container.find('input').each(function (i, field) {
            if (field.name.substring(0, 5) == 'priv_' && field.checked) {
              var priv_id = parseInt(field.name.substring(5), 10);
              result = (parseInt(field.value, 10) * priv_id);
              if (result) priv_data[priv_data.length] = result;
            }
          });
          $.each(selected_forums, function (i, forum_id) {
            var name = 'forum_privileges_' + forum_id;
            var result = $('input[name=' + name + ']');
            if (result.length === 0) result = $('<input type="hidden" />').attr('name', name).appendTo(self.container);
            self.mapping[forum_id] = priv_data;
            result.val(priv_data.join(','));
          });
        }).add(
        $('<label />').attr('for', 'priv_' + id + '_' + val).text(text));
      };
      priv_list.append($('<dt />').text(name), $('<dd />').append(
      radio(1, 'Ja'), radio(0, 'Nicht gesetzt'), radio(-1, 'Nein')));
    });
    $(list.children()[0]).click();
    content.append('<span class="note">Halte die Steuerungs-Taste gedrückt, um mehrere Foren auszuwählen.</span>');
  };
})();
