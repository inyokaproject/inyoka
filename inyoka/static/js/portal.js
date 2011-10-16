/*
    js.portal
    ~~~~~~~~~

    JavaScript for the portal.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
*/

$(function () { 
    (function () {
        var table = $('#dv');
        $('a[name="dv-add"]').click(function (event) {
            event.preventDefault();
            var $row = $('<tr>' +
                '<td><input type="text" name="dv-name"/></td>' +
                '<td><input type="text" name="dv-number"/></td>' +
                '<td><input type="checkbox" name="dv-lts"/></td>' +
                '<td><input type="checkbox" name="dv-active"/></td>' +
                '<td><input type="checkbox" name="dv-current"/></td>' +
                '<td><input type="checkbox" name="dv-dev"/></td>' +
                '<td></td>' +
                '</tr>');
            var $td_del = $('<td></td>');
            var $a_del = $('<a href="#dv" name="dv-delete-new">Löschen</a>');
            $a_del.click(function (event) {
                event.preventDefault();
                $(this).parent().parent().remove();
            });
            $a_del.appendTo($td_del);
            $td_del.appendTo($row);
            $row.appendTo('#dv > tbody');
        });
        $('a[id|="dv-edit"]').click(function (event) {
            event.preventDefault();
            var $row = $(this).parent().parent();
            var version = $row.attr('id').substring(3); //strip the dv- from the version
            $row.children().each(function () {
                // iterate over all <td> elements.
                var key = $(this).attr('id').substr(3);
                var key = key.substr(0, key.length - 6);
                if (key == 'number' || key == 'name') {
                    var $e = $('<input type="text" name="dv-' + key + '" value="' + $(this).text() + '"/>');
                    $(this).empty();
                    $e.appendTo(this);
                } else if (key == 'lts' || key == 'active' || key == 'current' || key == 'dev') {
                    var $e = $('<input type="checkbox" name="dv-' + key + '"/>');
                    if ($(this).hasClass('dv-yes')) {
                        $e.attr('checked', 'checked');
                    }
                    $(this).empty();
                    $e.appendTo(this);
                }
            });
            $(this).remove();
        });
        $('a[id|="dv-delete"]').click(function (event) {
            event.preventDefault();
            $(this).parent().parent().remove();
        });
    })();
});
