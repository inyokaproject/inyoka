/**
 * js.DateTime
 * ~~~~~~~~~~~
 *
 * This replaces a DateTime text field with a nice user-friendly gui including
 * a calendar and a table to select the clock.
 * It's based on django code that implements a similar widget for the admin
 * panel.
 *
 * :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
 * :license: BSD, see LICENSE for more details.
 */


/* create a closure for all of our stuff so that we don't export the
   helper functions and variables.  The only thing that is defined as
   a global is the `DateTimeField`. */

(function () {
  var months = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'];
  var days_of_week = ['S', 'M', 'D', 'M', 'D', 'F', 'S'];

  function isLeapYear(year) {
    return (((year % 4) === 0) && ((year % 100) !== 0) || ((year % 400) === 0));
  }

  function getDaysInMonth(month, year) {
    var days;
    if ($.inArray(month, [1, 3, 5, 7, 8, 10, 12]) != -1) days = 31;
    else if ($.inArray(month, [4, 6, 9, 11]) != -1) days = 30;
    else if (month == 2 && isLeapYear(year)) days = 29;
    else days = 28;
    return days;
  }


  DateTimeField = Class.$extend({
    __init__: function (editor, auto_show, only_date, only_time) {
      var self = this;
      this.input = $(editor).click(function () {
        $('table.datetime').each(function () {
          if (self.container[0] !== this) $(this).hide();
          else self.show();
        });
        return false;
      });
      this.auto_show = auto_show || false;
      this.only_date = only_date || false;
      this.only_time = only_time || false;
      this.readDateTime();
      this.container = $('<table class="datetime"></table>').click(function () {
        return false;
      });
      auto_show ? this.container.hide().addClass('auto_show') : this.input.hide();
      var row = $('<tr></tr>').appendTo(this.container);
      this.calendar = $('<td></td>').appendTo(row);
      this.timetable = $('<td></td>').appendTo(row);
      this.drawDate(this.currentYear, this.currentMonth);
      this.drawTimetable();
      if (only_date) {
        this.timetable.hide();
        this.currentTime = '00:00:00';
      }
      if (only_time) {
        this.calendar.hide();
      }
      this.input.after(this.container);
    },

    show: function () {
      this.readDateTime();
      this.container.css({
        position: 'absolute',
        left: this.input.offset().left
      }).show();
      if (this.only_date) {
        this.timetable.hide();
        this.currentTime = '00:00:00';
      }
      if (this.only_time) {
        this.calendar.hide();
      }
    },

    readDateTime: function () {
      var self = this;
      var set_vars = function (year, month, day, time) {
        self.currentYear = parseInt(year, 10);
        self.currentMonth = parseInt(month, 10);
        self.currentDay = parseInt(day, 10);
        self.currentTime = time;
      };
      var dateTimeRegex = /(\d{4})-(\d{1,2})-(\d{1,2}) (\d{2}):(\d{2}):(\d{2})/;
      var input_value = this.input.val();
      var found = dateTimeRegex.exec(input_value);
      if (input_value == '' || !found) {
        var today = new Date();
        set_vars(today.getFullYear(), today.getMonth() + 1, today.getDate(), [today.getHours(), today.getMinutes(), today.getSeconds()].join(':'));
      } else {
        set_vars(RegExp.$1, RegExp.$2, RegExp.$3, [RegExp.$4, RegExp.$5, RegExp.$6].join(':'));
      }
    },

    writeDateTime: function () {
      this.input.val(this.currentYear + '-' + this.currentMonth + '-' + this.currentDay);
      if (!this.only_date) this.input.val(this.input.val() + ' ' + this.currentTime);
      if (this.only_time) this.input.val(this.currentTime);
    },

    drawTimetable: function () {
      var self = this;
      var timetable = $('<table class="timetable"></table>').append(
      $('<tr><th class="caption">Uhrzeit</th></tr>'));
      this.timetable.append(timetable);
      var now = new Date();
      var times = [
        ['Jetzt', [now.getHours(), now.getMinutes(), now.getSeconds()].join(':'), (function (s) { s.container.hide(); })],
        ['Mitternacht', '00:00:00'],
        ['6 Uhr', '06:00:00'],
        ['Mittag', '12:00:00'],
        ['18 Uhr', '18:00:00']
      ];
      $.each(times, function (i, time) {
        timetable.append($('<tr></tr>').append($('<td></td>').append(
        $('<a/>').text(time[0]).click(function () {
          self.currentTime = time[1];
          self.writeDateTime();
          if (time.length > 2)
            time[2](self);
          return false;
        }))));
      });
      var col = $('<td></td>').appendTo($('<tr></tr>').appendTo(timetable));
      if (this.auto_show) {
        $('<a class="close">Schließen</a>').click(function () {
          self.container.hide();
          return false;
        }).appendTo(col);
      }
    },

    drawCalendar: function () {
      var self = this;
      var month = parseInt(this.calendarMonth, 10);
      var year = parseInt(this.calendarYear, 10);
      this.calendar.children().remove();
      var calendar = $('<table class="calendar"></table>').append(
      $('<tr></tr>').append(
      $('<th colspan="7" class="caption"></th>').append(
      $('<a class="calendarnav-next"></a>').text('>').click(function () {
        self.drawNextMonth();
        return false;
      }), $('<a class="calendarnav-previous"></a>').text('<').click(function () {
        self.drawPreviousMonth();
        return false;
      }), $('<span>' + months[month - 1] + ' ' + year + '</span>').click(function () {
        $(this).hide().after(
        $('<input type="text" />').val(month + '-' + year).change(function () {
          var dayRegex = /(\d{1,2})-(\d{1,2})-(\d+)/;
          dayRegex.exec($(this).val());
          if (RegExp.$1) self.drawDate(RegExp.$3, RegExp.$2, RegExp.$1);
          else {
            var monthRegex = /(\d{1,2})-(\d+)/;
            monthRegex.exec($(this).val());
            if (RegExp.$1) {
              self.drawDate(RegExp.$2, RegExp.$1);
            }
          }
        }).keypress(function (evt) {
          if (evt.keyCode == 13) {
            $(this).change();
            return false;
          }
        }).blur(function (evt) {
          $(this).change();
        }));
        $(this).next().focus();
      }).attr('title', 'Klicke hier, um schnell einen anderen Monat auszuwählen'))));
      var tbody = $('<tbody></tbody>').appendTo(calendar);
      var row = $('<tr></tr>').appendTo(tbody);

      // draw days-of-week header
      $.each(days_of_week, function (i, d) {
        row.append($('<th class="weekday"></th>').text(d));
      });

      var starting_pos = new Date(year, month - 1, 1).getDay();
      var days = getDaysInMonth(month, year);

      // Draw blanks before first of month
      var row = $('<tr></tr>').appendTo(tbody);
      for (var i = 0; i < starting_pos; i++)
      $('<td style="background-color: #f3f3f3;"></td>').appendTo(row);

      // Draw days of month
      var currentDay = 1;
      var day_click_callback = function () {
        $('.selected', $(this).parent().parent().parent()).removeClass('selected');
        $(this).parent().addClass('selected');
        self.currentDay = $(this).text();
        self.currentMonth = month;
        self.currentYear = year;
        self.writeDateTime();
        return false;
      };
      for (var i = starting_pos; currentDay <= days; i++) {
        if (i % 7 === 0 && currentDay != 1) row = $('<tr></tr>').appendTo(tbody);
        var td = $('<td></td>').append(
        $('<a></a>').text(currentDay).click(day_click_callback)).appendTo(row);
        if (year == this.currentYear && month == this.currentMonth && currentDay == this.currentDay) td.addClass('selected');
        currentDay++;
      }

      // Draw blanks after end of month (optional, but makes code valid)
      while (row.children().length < 7)
      row.append($('<td class="nonday"></td>'));

      this.calendar.append(calendar);
    },

    drawDate: function (year, month, day) {
      day = parseInt(day, 10);
      month = parseInt(month, 10);
      year = parseInt(year, 10);
      if (month > 0 && month < 13) {
        this.calendarMonth = month;
        this.calendarYear = year;
        if (day) {
          this.currentDay = day;
          this.currentMonth = month;
          this.currentYear = year;
        }
        this.drawCalendar();
      }
    },

    drawPreviousMonth: function () {
      if (this.calendarMonth == 1) {
        this.calendarMonth = 12;
        this.calendarYear--;
      } else {
        this.calendarMonth--;
      }
      this.drawCalendar();
    },

    drawNextMonth: function () {
      if (this.calendarMonth == 12) {
        this.calendarMonth = 1;
        this.calendarYear++;
      } else {
        this.calendarMonth++;
      }
      this.drawCalendar();
    },

    drawPreviousYear: function () {
      this.calendarYear--;
      this.drawCalendar();
    },

    drawNextYear: function () {
      this.calendarYear++;
      this.drawCalendar();
    },

    destroy: function () {
      this.writeDateTime();
      this.container.remove();
      this.input.show();
    }
  });

  /* Get all inputs with type date or datetime and create a DateTimeField for
   * them. */

  $(document).ready(function () {
    $('input').each(function () {
      var type = this.getAttribute('valuetype');
      if (type == 'datetime') {
        DateTimeField(this, true);
      } else if (type == 'date') {
        DateTimeField(this, true, true);
      } else if (type == 'time') {
        DateTimeField(this, true, false, true);
      }
    });
  });

  $(document).click(function () {
    $('table.datetime.auto_show').hide();
  });

})();
