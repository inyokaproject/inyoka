/*
    js.jstableform
    ~~~~~~~~~~~~~~
    JavaScript Table Form. This is an independent script to create fancy JS
    table forms. An example can be seen in the portal configuration.

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
*/
$(function () {
    (function () {
    JSTableForm = function ($table, $returnfield) {
        /**
         * To use the JavaScript Table Form call this function with two
         * parameters:
         *
         *  1. The jQuery object of the table to use
         *  2. The jQuery object where to resulting JSON string should be
         *     written into
         *
         * The definition takes place in the table cells of the thead. EVERY td
         * cell needs to get a class of the form `jstableform-key-NAME` where
         * `NAME` denotes the attribute for an object after conversion to JSON.
         * `NAME` might not be start with an underscore `_`, they are reserved
         * for internal use!
         *
         *  - If `NAME` is '_cmdedit' the column will contain the link to
         *    modify and revert the row.
         *  - If `NAME` is '_cmddel' the column will hold the link to remove
         *    the row.
         *
         * Additionally, EVERY cell in thead, except those starting with an '_'
         * has to contain a class of the form `jstableform-type-TYPE` where
         * `TYPE` can be on of 'string', 'int', 'float', 'text' and 'boolean'.
         * The JavaScript will guess the input element for this column from the
         * type. The first three will be represented as an <input type="text">,
         * the fourth as <textarea/> and the latter one will hold the amazing
         * clickable yes/no icons feature.
         *
         * Last but not least, each cell can optionally contain a class of the
         * form `jstableform-validate-VALIDATOR` where `VALIDATOR` has to be
         * given as a key in the variable `validators`. Currently there are
         * validators for 'int', 'float', 'versionnumber' and 'versionname'
         * that run a validation on the content of the input field when the
         * JavaScript event onblur is invoked on this element or when the
         * formula is send.
         *
         * Optionally a <td> element with the class 'jstableform-_jswarning'
         * can be added to the table with a warning message that the table
         * requires JavaScript. The parent HTML element of this cell, normally
         * an <tr> tag, will be removed if JavaScript is activated.
         */
        var int_re = /^\d+$/;
        var float_re = /^\d+|\d+\.\d+|\.\d+$/;
        var versionnumber_re = /^\d\d?\.\d\d$/;
        var versionname_re = /^[A-Z][a-z]+ [A-Z][a-z]+$/;
        var revert = {};
        var editing = {};
        var anchor = $table.attr('id') || '';

        function setFalse(element) {
            element.addClass('jstableform-status-no').removeClass('jstableform-status-yes');
        }

        function setTrue(element) {
            element.addClass('jstableform-status-yes').removeClass('jstableform-status-no');
        }

        function toggleBooleanStatus(event) {
            switch (getBooleanStatus($(this))) {
                case true:
                    setFalse($(this));
                    break;
                case false:
                    setTrue($(this));
                    break;
                default:
                    // do nothing. Just to catch 'undefined' and 'null'
            }
        }

        function getBooleanStatus(element) {
            if (element.hasClass('jstableform-status-yes')) {
                return true;
            } else if (element.hasClass('jstableform-status-no')) {
                return false;
            }
            return null;
        }

        function validateInt(value) {
            return int_re.test(value);
        }

        function validateFloat(value) {
            return float_re.test(value);
        }

        function validateVersionNumber(value) {
            return versionnumber_re.test(value);
        }

        function validateVersionName(value) {
            return versionname_re.test(value);
        }

        function onValidate(event) {
            var key = $(this).parent().attr('name').substring(16);
            var validator = columns[key].validator;
            if (validator != null) {
                if (validator($(this).val())) {
                    $(this).removeClass('invalid');
                } else {
                    $(this).addClass('invalid');
                }
            }
        }

        var validators = {
            'int': validateInt,
            'float': validateFloat,
            'versionnumber': validateVersionNumber,
            'versionname': validateVersionName
        };

        function add_row(event) {
            event.preventDefault();
            var $row = $('<tr name="jstableform-_new"></tr>'); // This is our new table row
            $.each(keys, function (i, k) { // let's iterator over the columns
                var obj = columns[k];
                // Since each column is forced to have an key,
                // we can generate the regarding cell for the row.
                var $td = $('<td name="jstableform-key-' + k + '"></td>');
                var $e;
                if (obj.type == 'string' || obj.type == 'int' || obj.type == 'float') {
                    // Internally, string, int and float are
                    // represented as intput html elements
                    $e = $('<input type="text"/>');
                    $e.blur(onValidate);
                    $e.appendTo($td);
                } else if (obj.type == 'text') {
                    $e = $('<textarea></textarea>');
                    $e.blur(onValidate);
                    $e.appendTo($td);
                } else if (obj.type == 'boolean') {
                    // For boolean values we have this fancy images showing yes
                    // and no / true and false
                    $td.addClass('jstableform-status-no');
                    $td.addClass('pointer');
                    $td.click(toggleBooleanStatus);
                } else if (obj.type == '_edit') {
                    // do nothing -- a new row is always in
                    // edit mode and cannot even be reverted
                } else if (obj.type == '_delete') {
                    // Since each row that we add can be deleted we add the
                    // regarding link here.
                    $e = $('<a href="#' + anchor + '">Löschen</a>');
                    $e.click(delete_row);
                    $e.appendTo($td);
                }
                // We now add the cell to to the table row
                $td.appendTo($row);
            });
            // And finally we add the row to the table body
            $('tbody', $table).append($row);
        }

        function delete_row(event) {
            event.preventDefault();
            $(this).parent().parent().remove();
        }

        function revert_row(event) {
            event.preventDefault();
            var $row = $(this).parent().parent(); // a -> td -> tr
            // To get the row identifier we strip the
            // 'jstableform-' from row attribute 'id'
            var row_id = $row.attr('name').substring(12);
            var dataset = {};

            $.each(keys, function (i, k) { // let's iterator over the columns
                var obj = columns[k];
                // This is the current cell we are operating on
                var $td = $row.find('[name="jstableform-key-' + k + '"]');
                if (obj.type == 'string' || obj.type == 'int' || obj.type == 'float' || obj.type == 'text') {
                    // string, int and float, text are the same, at
                    // least internally. They all contain plain text.
                    $td.empty();
                    $td.text(revert[row_id][k]);
                } else if (obj.type == 'boolean') {
                    if (revert[row_id][k]) {
                       setTrue($td);
                    } else {
                        setFalse($td);
                    }
                    $td.unbind('click');
                    $td.removeClass('pointer');
                } else if (obj.type == '_edit') {
                    var $e = $('<a href="#' + anchor + '">Ändern</a>');
                    $td.empty();
                    $e.click(edit_row).appendTo($td);
                } else if (obj.type == '_delete') {
                    // We don't have to change the delete cell.
                }
            });
            // Delete the data from the reverting storage
            delete revert[row_id];
            delete editing[row_id];
        }

        function edit_row(event) {
            event.preventDefault(); // We don't want the links to have any effect
            var $row = $(this).parent().parent(); // a -> td -> tr

            // To get the row identifier we strip the
            // 'jstableform-' from row attribute 'id'
            var row_id = $row.attr('name').substring(12);
            var dataset = {};

            $.each(keys, function (i, k) { // let's iterator over the columns
                var obj = columns[k];
                // This is the current cell we are operating on
                var $td = $row.find('[name="jstableform-key-' + k + '"]');
                if (obj.type == 'string' || obj.type == 'int' || obj.type == 'float') {
                    // string, int and float are the same, at least internally
                    var $e = $('<input type="text"/>');
                    $e.blur(onValidate);
                    dataset[k] = $td.text();
                    $e.val($td.text());
                    $td.empty();
                    $e.appendTo($td);
                } else if (obj.type == 'text') {
                    var $e = $('<textarea></textarea>');
                    $e.blur(onValidate);
                    dataset[k] = $td.text();
                    $e.val($td.text());
                    $td.empty();
                    $e.appendTo($td);
                } else if (obj.type == 'boolean') {
                    dataset[k] = getBooleanStatus($td);
                    $td.addClass('pointer');
                    $td.click(toggleBooleanStatus);
                } else if (obj.type == '_edit') {
                    var $e = $('<a href="#' + anchor + '">Abbrechen</a>');
                    $td.empty();
                    $e.click(revert_row);
                    $e.appendTo($td);
                } else if (obj.type == '_delete') {
                    // We don't have to change the delete cell.
                }
            });
            // Store the old data for reverting
            revert[row_id] = dataset;
            editing[row_id] = true;
        }

        function submit_config(event) {
            var distri_versions = new Array();
            var $row;
            var new_row;
            $('tr[name^="jstableform-"]').each(function () {
                $row = $(this); // just to make it a bit more handy
                var row_id = $row.attr('name').substring(12);
                new_row = (row_id == '_new');
                // values holds the content of the current row after the loop:
                // {key1: 'value1', key2: 'value2'}
                var values = {}; 
                if (new_row || editing[row_id]) {
                    // We will have to take the values
                    // from the input elements
                    $.each(keys, function (i, k) {
                        var obj = columns[k];
                        // This is the current cell we are operating on
                        var $td = $row.find('[name="jstableform-key-' + k + '"]');
                        if (obj.type == 'string' || obj.type == 'int' || obj.type == 'float' || obj.type == 'text') {
                            var $e = $('input', $td);
                            var val = $e.val();
                            var valid = true;
                            if (obj.validator !== null) {
                                valid = obj.validator(val);
                            }
                            if (!valid) {
                                event.preventDefault();
                            }
                            values[k] = val;
                        } else if (obj.type == 'boolean') {
                            values[k] = getBooleanStatus($td);
                        }
                    });
                } else {
                    // We can take the content from the cell
                    $.each(keys, function (i, k) {
                        var obj = columns[k];
                        // This is the current cell we are operating on
                        var $td = $row.find('[name="jstableform-key-' + k + '"]');
                        if (obj.type == 'string' || obj.type == 'int' || obj.type == 'float' || obj.type == 'text') {
                            values[k] = $td.text();
                        } else if (obj.type == 'boolean') {
                            values[k] = getBooleanStatus($td);
                        }
                    });
                }
                distri_versions.push(values);
            });
            $returnfield.val(window.JSON.stringify(distri_versions));
        }

        var columns = {};
        var keys = [];

        $('td[class="jstableform-_jswarning"]', $table).parent().remove();

        // Let's try to get the different columns of the table
        // with all their properties, such as type and validators
        $('thead tr td', $table).each(function () {
            classes = $(this).attr('class').split(' ');
            var key;
            var obj = {key: null, type: null, validator: null};
            // For each column we store a couple of information:
            //  - the name or key of the column
            //  - the type of content, whether string, text or boolean,
            //    int or float
            //  - the validator as defined in the variable `validators`
            $.each(classes, function (i, k) {
                if (k.indexOf('jstableform-') == 0) {
                    k = k.substring(12);
                    if (k.indexOf('key-') == 0) {
                        key = k.substring(4);
                        obj.key = key;
                        if (key == '_cmdedit') {
                            obj.type = '_edit';
                            return true; // continue with next element
                        } else if (key == '_cmddel') {
                            obj.type = '_delete';
                            return true; // continue with next element
                        }
                    } else if (k.indexOf('type-') == 0) {
                        obj.type = k.substring(5);
                        if (obj.type == 'int' && obj.validator == null) {
                            obj.validator = validators['int'];
                        } else if (obj.type == 'float' && obj.validator == null) {
                            obj.validator = validators['float'];
                        }
                    } else if (k.indexOf('validate-') == 0) {
                        obj.validator = validators[k.substring(9)];
                    }
                }
            });
            // Store the current object in the global lookup dictionary
            columns[key] = obj;
            // And push just the key to an array. This let us
            // keep track on the column order
            keys.push(key);
        });

        $('a[name="jstableform-add"]', $table).click(add_row);

        $('td[name|="jstableform-key-_cmdedit"] a', $table).click(edit_row);

        $('td[name|="jstableform-key-_cmddel"] a', $table).click(delete_row);

        $('input[type="submit"]').click(submit_config);
    }
    })();
});
