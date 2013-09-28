/**
 * js.PrivilegeBox
 * ~~~~~~~~~~~~~~~
 *
 * :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
 * :license: BSD, see LICENSE for more details.
 *
 * TODO: i18n
 */
(function () {
  PrivilegeBox = function (container, forums, privileges) {
    this.mapping = {};
    var selected_forums = [],
        self = this,
        forum_container = $('<div class="col-sm-4" />'),
        list = $('<ul class="portal-privilege-list" role="tablist"/>'),
        content = $('<div class="col-sm-8"></div>'),
        selected_forums_info = $('<p class="text-info"/>'),
        priv_list = $('<div class="form-horizontal"/>');

    this.container = $(container);
    this.container.html('');
    this.container.append(forum_container);
    this.container.append(content);
    forum_container.append(list);
    forum_container.append('<p class="text-info">Auswahl:</p>');
    forum_container.append(selected_forums_info);
    content.append(priv_list);
    this.container.append(
      '<span class="help-block">'+
        'Halte die Steuerungs-Taste gedrückt, um mehrere Foren auszuwählen.'+
      '</span>'
    );

    $.each(forums, function (i, forum) {
      var id = forum[0];
      var name = forum[1];
      var positive = forum[2];
      var negative = forum[3];
      self.mapping[id] = positive.concat($.map(negative, function (o) {
        return o * -1;
      }));

      var li = $('<li />');
      li.text(name);
      li.attr('id', 'forum_' + id);
      li.addClass('portal-privilege-list-item');
      if (positive != '' || negative != '') {
        li.addClass('changed');
      }
      li.click(function (evt) {
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
          selected_forums_info.text($('#forum_' + forum).text());

          $.each(privileges, function (id, name) {
            id = parseInt(id, 10);
            var value;
            if ($.inArray(id, self.mapping[forum]) > -1){
              value = '1';
            } else if ($.inArray(id * -1, self.mapping[forum]) > -1) {
              value = '-1';
            } else {
              value = '0';
            }
            $('select.' + id).val(value);
          });

        } else {
          selected_forums_info.text(selected_forums.length + ' Foren');
          $('select.priv', self.container).val('0');
        }
      });
      list.append(li);
    });

    $.each(privileges, function (id, name) {
      var permission_select = function (values, options) {
        var select = $('<select class="form-control ' + id + ' priv" />');

        for (var i = 0; i < options.length; i++) {
          var option = $('<option />');
          option.attr({
            name: 'priv_' + id,
            value: values[i],
            id: 'priv_' + id + '_' + values[i]
          });
          option.text(options[i]);
          select.append(option);
        };
        select.change(function () {
          var priv_data = [];
          $('select.priv option:selected').each(function(i, field) {
            var priv_id = parseInt(field.getAttribute('name').substring(5), 10);
            var result = (parseInt(field.getAttribute('value'), 10) * priv_id);
            if (result) {
              priv_data[priv_data.length] = result;
            }
          });
          $.each(selected_forums, function (i, forum_id) {
            var name = 'forum_privileges_' + forum_id;
            var result = $('input[name=' + name + ']');
            if (result.length === 0) {
              result = $('<input type="hidden" />');
              result.attr('name', name);
              result.appendTo(self.container);
            }
            self.mapping[forum_id] = priv_data;
            result.val(priv_data.join(','));
          });
        });
        return select;
      };

      var entry =  $('<div class="form-group" />');
      var label = $('<label class="col-sm-6"/>');
      label.text(name);
      var selection = $('<div class="col-sm-6" />');
      selection.append(
        permission_select([1,0,-1], ['Ja','Nicht gesetzt', 'Nein'])
      );
      entry.append(label);
      entry.append(selection);

      priv_list.append(entry);
    });

   $(list.children()[0]).click();
  };
})();
