/**
 * js.admin
 * ~~~~~~~~
 *
 * Some scripts for the admin (requires jQuery).
 *
 * :copyright: (c) 2010-2015 by the Inyoka Team, see AUTHORS for more details.
 * :license: BSD, see LICENSE for more details.
 */

$(document).ready(function () {
  (function () {
    if (!$('textarea[name="signature"]').length == 0) {
      // create a WikiEditor instance for all signature fields
      var signature = new WikiEditor('textarea[name="signature"]');
    }

    // Small helper to define a users group title
    $('input[name="group_titles"]').change(function () {
      var value = "";
      $('input[name="group_titles"]:checked').each(function (i) {
        if (i > 0) value += " & ";
        value += $(this).val();
      });
      $('#id_member_title').val(value);
    });

    // Add auto completion to #user_query fields
    $('#user_query, #id_user, #id_author').autocomplete("/?__service__=admin.get_user_autocompletion", {
      delay: 40,
      maxItemsToShow: 10,
      limit: 10,
      minChars: 3
    });

    // various callbacks for user group editing
    $('select[name="user_groups_joined"]').change(function () {
      var field = $('select[name="user_groups_joined"]');
      $('input[name="primary_group"]').val(field.find('option:selected').val());
    });

    $('a.delete_primary_group').click(function () {
      $('input[name="primary_group"]').val("");
      return false;
    });

    $('input[name="primary_group"]').autocomplete("/?__service__=admin.get_group_autocompletion", {
      delay: 40,
      maxItemsToShow: 10,
      limit: 10,
      minChars: 1
    });
  })();
});
