/*
    js.portal
    ~~~~~~~~~

    JavaScript for the portal.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
*/
$(function () { 
    (function () {
        function setFalse(element) {
            element.addClass('dv-no').removeClass('dv-yes');
        }

        function setTrue(element) {
            element.addClass('dv-yes').removeClass('dv-no');
        }

        var toggleBoolean = function (event) {
            if ($(this).hasClass('dv-yes')) {
                setFalse($(this));
            } else if ($(this).hasClass('dv-no')) {
                setTrue($(this));
            }
        }

        function getStatus(element) {
            if (element.hasClass('dv-yes')) {
                return 'true';
            } else if (element.hasClass('dv-no')) {
                return 'false';
            }
            return null;
        }

        var keys = ['number', 'name', 'lts', 'active', 'current', 'dev'];
        var number_re = /^\d\d?\.\d\d$/;
        var revert = {};
        var editing = {};

        var add_row = function (event) {
            event.preventDefault();
            var $row = $('<tr name="dv-new">' +
                '<td><input type="text" name="dv-number"/></td>' +
                '<td><input type="text" name="dv-name"/></td>' +
                '</tr>');
            for (var i = 2; i < keys.length; i++) {
                $('<td></td>').attr('name', keys[i]).addClass('dv-no').click(toggleBoolean).appendTo($row);
            }
            $('<td></td>').appendTo($row);
            var $e = $('<td></td>');
            var $a_del = $('<a href="#dv" name="dv-delete">Löschen</a>');
            $a_del.click(delete_row).appendTo($e);
            $e.appendTo($row);
            $row.appendTo('#dv > tbody');
        };

        var delete_row = function (event) {
            event.preventDefault();
            $(this).parent().parent().remove();
        };

        var revert_row = function (event) {
            event.preventDefault();
            var $row = $(this).parent().parent();
            var version = $row.attr('id').substring(3);
            // TODO: use keys to iterate over columns -> faster and more reliable
            $row.find("[name|=dv]").each(function () {
                var $p = $(this).parent();
                var key = $(this).attr('name').substr(3);
                if (key == 'number' || key == 'name') {
                    $p.attr('name', 'dv-' + key).empty();
                    $p.text(revert[version][key]);
                } else if (key == 'lts' || key == 'active' || key == 'current' || key == 'dev') {
                    if (revert[version][key] == 'true') {
                       setTrue($(this));
                    } else if (revert[version][key] == 'false') {
                        setFalse($(this));
                    }
                    $(this).unbind('click');
                } else if (key == 'revert') {
                    $p.empty();
                    var $a_edit = $('<a href="#dv" name="dv-edit">Ändern</a>');
                    $a_edit.click(edit_row).appendTo($p);
                }
            });
            delete revert[version];
            delete editing[version];
        };

        var edit_row = function (event) {
            event.preventDefault();
            var $row = $(this).parent().parent();
            var version = $row.attr('id').substring(3); //strip the dv- from the version
            var dataset = new Object();
            // TODO: use keys to iterate over columns -> faster and more reliable
            $row.find('[name^="dv"]').each(function () {
                // iterate over all <td> elements.
                var key = $(this).attr('name').substr(3);
                if (key == 'number' || key == 'name') {
                    var $e = $('<input type="text" name="dv-' + key + '"/>');
                    dataset[key] = $(this).text();
                    $e.val($(this).text());
                    $(this).removeAttr('name').empty();
                    $e.appendTo(this);
                } else if (key == 'lts' || key == 'active' || key == 'current' || key == 'dev') {
                    dataset[key] = getStatus($(this));
                    $(this).addClass('pointer').click(toggleBoolean);
                }
            });
            revert[version] = dataset;
            editing[version] = true;
            var $p = $(this).parent();
            $(this).remove();
            var $a_revert = $('<a href="#dv" name="dv-revert">Abbrechen</a>');
            $a_revert.click(revert_row).appendTo($p);
        };

        $('a[name="dv-add"]').click(add_row);

        $('a[name|="dv-edit"]').click(edit_row);

        $('a[name|="dv-delete"]').click(delete_row);

        $('input[type="submit"]').click(function (event) {
            var distri_versions = new Array();
            $('tr[id|="dv"],tr[name="dv-new"]').each(function () {
                var values = new Array(); //{number:'', name:'', lts:'', active:'', current:'', dev:''};
                for (i = 0; i < keys.length; i++) {
                    var k = keys[i];
                    var $e = $(this).find('[name="dv-' + k +'"]');
                    var val;
                    if ($e.is('INPUT')) {
                        val = $e.val();
                    } else {
                        val = getStatus($e);
                        val = (val == null) ? $e.text() : val;
                    }
                    if (k == 'number' && !number_re.test(val) || k == 'name' && jQuery.trim(val) == '') {
                        return true; // return true to skip this loop but continue in `each()`
                    }
                    values.push('"' + k + '":"' + val + '"');
                }
                distri_versions.push('{' + values.join(',') + '}');
            });
            $('#id_distri_versions').val('[' + distri_versions.toString() + ']');
        });
    })();
});
