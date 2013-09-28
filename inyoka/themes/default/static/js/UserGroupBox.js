/*
 *    js/UserGroupBox
 *    ~~~~~~~~~~~~~~~
 *
 *    A little box to add/remove the user to some groups.
 *
 *
 *    :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
 *    :license: BSD, see LICENSE for more details.
 */

(function () {

  GroupBox = Class.$extend({
    __init__: function (container, user_joined, user_not_joined) {
      var self = this;
      this.container = $(container);

      // Groups the user not joined
      this.user_not_joined = $('select[name="user_groups_not_joined"]');

      // Groups the user joined
      this.user_joined = $('select[name="user_groups_joined"]');

      // add items to the select boxes
      this.rebuildBoxes(user_joined, user_not_joined);

      // add needed submit event
      $($(container).find('input[type="submit"]')[0]).submit(function () {
        $.each([self.user_not_joined, self.user_joined], function () {
          this.find('option').each(function () {
            this.selected = true;
          });
        });
        return true;
      });

      // add add/remove events
      $('button.item_add').click(function () {
        self.move(self.user_not_joined, self.user_joined);
      });
      $('button.item_remove').click(function () {
        self.move(self.user_joined, self.user_not_joined);
      });
    },

    rebuildBoxes: function (joined, not_joined) {
      var self = this;
      $.each(joined, function (i, group) {
        $('<option />').text(group).appendTo(self.user_joined);
      });

      $.each(not_joined, function (i, group) {
        $('<option />').text(group).appendTo(self.user_not_joined);
      });
    },

    move: function (from, to) {
      from.find('option:selected').remove().appendTo(to);
    }
  });
})();
