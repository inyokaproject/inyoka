/**
 * jquery.plugin.wiki_editor
 * ~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 * Implements a jQuery plugin to advance textareas so that they give
 * a better text control for wiki markup.
 * 
 * Usage as follows::
 *
 *    $('#my_editor').wikiEditor();
 *
 * The toolbar is added dynamically to the editor so that users without
 * JavaScript don't get a useless UI.
 *
 * :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
 * :license: GNU GPL, see LICENSE for more details.
 */


(function( $ ) {

  var defaults = {
    indentation: 2,
    profile: 'small',
    codes: {
      'text': 'Code ohne Highlighting',
      'bash': 'Bash',
      'c': 'C',
      'csharp': 'C#',
      'cpp': 'C++',
      'css': 'CSS',
      'd': 'D',
      'html+django': 'Django / Jinja Templates',
      'html': 'HTML',
      'irc': 'IRC Logs',
      'java': 'Java',
      'js': 'JavaScript',
      'perl': 'Perl',
      'html+php': 'PHP',
      'python': 'Python',
      'pycon': 'Python Console Sessions',
      'pytb': 'Python Tracebacks',
      'ruby': 'Ruby',
      'sourceslist': 'sources.list',
      'sql': 'SQL',
      'xml': 'XML'
    }
  };

  /**
   * Helper function that creates a button object.
   */
  var button = function (id, title, callback, profiles, helper) {
    return function(editor) {
      if (!profiles || $.inArray(editor.options.profile, profiles) > -1)
        return $('<a href="#" class="button" />')
          .attr('id', 'button-' + id)
          .attr('title', title)
          .mouseover(function(evt) {
            evt.preventDefault();
            helper(editor, evt);
          })
          .mouseout(function(evt) {
            evt.preventDefault();
            helper(editor, evt);
          })
          .append($('<span />').text(title))
          .click(function(evt) {
            evt.preventDefault();
            return callback.call(editor, evt);
          });
    };
  };

  /**
   * helper function that creates a dropdown object.
   */
  var dropdown = function(id, title, items, callback, profiles, helper) {
    return function(editor) {
      if (profiles && $.inArray(editor.options.profile, profiles))
        return;
      var dropdown = $('<select />')
        .attr('id', 'dropdown-' + id)
        .attr('title', title)
        .append($('<option class="title" value="" />').text(title))
        .mouseover(function(evt) {
          helper(editor, evt);
        })
        .mouseout(function(evt) {
          helper(editor, evt);
        })
        .change(function(evt) {
          callback(editor, evt);
        });
      $.each(items, function() {
        dropdown.append(this);
      });
      dropdown[0].selectedIndex = 0;
      return dropdown;
    };
  };

  /**
   * one item in a dropdown
   */
  var item = function(value, title) {
    return $('<option />').val(value).text(title || value);
  };

  /**
   * factory function for combined usage with "button".
   */
  var insert = function(format, def) {
    return function(evt) {
      return this.insertTag(format,
        (typeof def == 'undefined') ? 'Formatierter Text' : def
      );
    };
  };

  /**
   * factory duncrion for combined usage with "button".
   * It's an easy way to insert help commands.
   *
   */
  var help = function(message) {
    return function(editor, evt) {
      if (evt.type == 'mouseover') {
        $('.toolbar_help').text(message);
      } else {
        $('.toolbar_help').text('...');
      }
    };
  };

  /**
   * Helper function that formats a `Date` object into a iso8601
   * format string.
   *
   */
  var formatISO8601 = function(orig) {
    var year = orig.getUTCFullYear(),
        month = orig.getUTCMonth(),
        date = orig.getUTCDate(),
        hours = orig.getUTCHours(),
        minutes = orig.getUTCHours(),
        seconds = orig.getUTCSeconds();
    return (year + '-' + (month < 9 ? '0' : '') + (month + 1) + '-' +
                         (date < 10 ? '0' : '') + date + 'T' +
                         (hours < 10 ? '0' : '') + hours + ':' +
                         (minutes < 10 ? '0' : '') + minutes + ':' +
                         (seconds < 10 ? '0' : '') + seconds + 'Z');
  };

  /**
   * The toolbar
   */
  var toolbar = function() {
    return [
    button('bold', 'Fetter Text', insert("'''%s'''"),
           ['wiki', 'forum', 'small'], help("'''Text'''")),
    button('italic', 'Kursiver Text', insert("''%s''"),
           ['wiki', 'forum', 'small'], help("''Text''")),
    button('underlined', 'Unterstrichener Text', insert('__%s__'),
           ['forum', 'small'], help("__Text__")),
    button('stroke', 'Durchgestrichener Text', insert('--(%s)--'),
           ['forum'], help("--(Text)--")),
    button('monospace', 'Monotype', insert('`%s`'),
           ['wiki'], help("`Text`")),
    button('mark', 'Hervorgehobener Text', insert('[mark]%s[/mark]'),
           ['forum'], help("[mark]Text[/mark]")),
    button('wiki-link', 'Wiki-Link', insert('[:%s:]', 'Seitenname'),
           ['wiki', 'forum'], help("[:Seitenname:(Linktext)]")),
    button('external-link', 'Externer Link', insert('[%s]',
           'http://www.example.org/'), ['wiki', 'forum', 'small'], help("[www.example.com]")),
    button('user-link', 'Benutzerlink', insert('[user:%s:]', 'Benutzername'),
           ['forum'], help("[user:Beispiel:]")),
    button('quote', 'Auswahl zitieren', function(evt) {
      var selection = this.getSelection();
      if (selection.length)
        this.setSelection(this.quoteText(selection));
    }, ['forum'], help("Auswahl zitieren")),
    button('picture', 'Bild', insert('[[Bild(%s)]]', 'Bildname'),
           ['wiki', 'forum'], help("[[Bild(Bildname)]]")),
    (function(editor) {
      if (editor.options.profile == 'small') {
        return;
      }
      var result = $('<div />');
      button('pre', 'Codeblock', function(evt) {
        codebox.slideToggle('fast');
        return false;
      }, ['wiki', 'forum'], help("Code einfügen"))(editor).appendTo(result);
      var codebox = $('<table class="codebox" />').appendTo(result).hide();
      codebox[0].style.display = 'none'; //hide box in safari
      var tds = [$('<td>Rohtext</td>').click(function() {
        editor.insertTag('{{{\n%s\n}}}', 'Code');
      })];
      $.each(editor.options.codes, function(k, v) {
        tds.push($('<td>' + v + '</td>')
          .click(function() {
            editor.insertTag('{{{#!code ' + k + '\n%s\n}}}', 'Code');
          }));
      });
      for (var i = 0; i < tds.length / 2; i++) {
        $('<tr />')
          .appendTo(codebox)
          .append(tds[i], tds[i + tds.length / 2]);
      }
      $(document).click(function() {
        if (codebox.is(':visible'))
          codebox.slideUp('fast');
      });
      return result;
    }),
    (function(editor) {
      if (editor.options.profile != 'forum')
        return;
      var result = $('<div />');
      button('smilies', 'Smilies', function(evt) {
        smileybox.slideToggle('fast');
        return false;
      }, ['forum'], help("Smiley einfügen"))(editor).appendTo(result);
      var smileybox = $('<ul class="smileybox" />').appendTo(result).hide();
      smileybox[0].style.display = 'none'; //hide box in safari
      $.getJSON('/?__service__=wiki.get_smilies', function(smilies) {
        $.each(smilies, function() {
          var code = this[0], src = this[1];
          $('<li />')
            .append($('<img />')
              .attr('src', src)
              .attr('alt', code)
              .click(function() {
                editor.insertText(' ' + code + ' ');
              }))
            .appendTo(smileybox);
        });
      });
      $(document).click(function() {
        if (smileybox.is(':visible'))
          smileybox.slideUp('fast');
      });
      return result;
    }),
    dropdown('headline', 'Überschrift', [
        item('=', 'Überschrift: Stufe 1'),
        item('==', 'Überschrift: Stufe 2'),
        item('===', 'Überschrift: Stufe 3'),
        item('====', 'Überschrift: Stufe 4'),
        item('=====', 'Überschrift: Stufe 5')
      ],
      function(evt) {
        var delim = evt.target.value;
        if (delim.length > 0)
          this.insertTag(delim + ' %s ' + delim + '\n', 'Überschrift');
        evt.target.selectedIndex = 0;
    }, ['wiki'], help("= Überschrift =")),
    dropdown('macro', 'Textbausteine', [
        item('[[Vorlage(InArbeit, %s)]]', 'in Arbeit'),
        item('[[Inhaltsverzeichnis(%s)]]', 'Inhaltsverzeichnis'),
        item('[[Vorlage(Getestet, %s)]]', 'Getestet'),
        item('{{{#!vorlage Paketinstallation\n{S/Paket, info}\n}}}', 'Paketinstallation'),
        item('{{{#!vorlage Befehl\n%s\n}}}', 'Befehl'),
        item('[[Vorlage(PPA, %s)]]', 'PPA-Vorlage'),
        item('{{{#!vorlage Hinweis\n%s\n}}}', 'Hinweis'),
        item('[[Vorlage(Fremd, Quelle, "%s")]]', 'Fremdquelle-Warnung'),
        item('{{{#!vorlage Warnung\n%s\n}}}', 'Warnung'),
        item('{{{#!vorlage Experten\n%s\n}}}', 'Experten-Info'),
        item('[[Vorlage(Tasten, %s)]]', 'Taste'),
        item('{{{#!vorlage Tabelle\n{S/[:Wiki/Syntax/Tabellen:]}\n}}}', 'Tabelle')
      ],
      function(evt) {
        if (evt.target.value.length > 0)
          this.insertTag(evt.target.value, '');
        evt.target.selectedIndex = 0;
    }, ['wiki'], help("Textbaustein einfügen")),
    dropdown('textformat', 'Textformat', [
      item("'''{S/Verzeichnisse}'''", 'Verzeichnisse'),
      item("''\"{S/Menü -> Untermenü -> Menübefehl}\"''", 'Menüs'),
      item("'''{S/Dateien}'''", 'Dateien'),
      item('`{S/Befehl}`', 'Befehl')
    ],
    function(evt) {
        if (evt.target.value.length > 0)
          this.insertTag(evt.target.value, '');
        evt.target.selectedIndex = 0;
    }, ['wiki'], help("Textformat einfügen")),
    button('shrink', 'Eingabefeld verkleinern', function(evt) {
      var height = this.$el.height() - 50;
      this.$el.height((height >= 100) ? height : 100).focus();
    }, ['forum', 'wiki'], help("Eingabefeld verkleinern")),
    button('enlarge', 'Eingabefeld vergrößern', function(evt) {
      this.$el.height(this.$el.height() + 50).focus();
    }, ['forum', 'wiki'], help("Eingabefeld vergrößern"))];
  };

  var WikiEditor = function (editor, options) {
    this.$el = $(editor);
    this.options = options;

    this.init();
  };

  WikiEditor.prototype.init = function (options) {
    var self = this;
    this.options = $.extend(defaults, options);
    this.username = Inyoka.CURRENT_USER;
    this.smilies = null;
    this.$el[0].inyokaWikiEditor = this;

    /* create toolbar based on button layout */
    t = $('<ul class="toolbar" />').prependTo(this.$el.parent());
    var bar = toolbar();
    for (var i = 0, n = bar.length, x; i != n; ++i)
      if (x = bar[i](self))
        x.appendTo($('<li />').appendTo(t));

    if (this.options.profile == 'wiki') {
      link = 'http://wiki.ubuntuusers.de/Wiki/Syntax';
    } else {
      link = 'http://wiki.ubuntuusers.de/Forum/Syntax';
    }
    $('<span class="syntax_help note"><a href="' + link + '">Hilfe zur Syntax</a></span>')
      .appendTo($('<li />').appendTo(t));
  };


  /**
   * Insert a tag around a selection.  (Or if no value is selected then it
   * inserts a default text and marks it).  This does not use the
   * `getSelection` and `setSelection` for performance reasons.
   */
  WikiEditor.prototype.insertTag = function (format, def) {
    var
      t = this.$el[0],
      args = [];
    if (format instanceof Array) {
      args = format;
    } else if (format.indexOf('%s') != -1) {
      args = format.split('%s', 2);
    } else {
      def = format.match(/{S\/(.+?)}/)[1];
      args = format.split('{S/'+def+'}', 2);
    }

    var
      before = args[0] || '',
      after = args[1] || '';

    scroll = t.scrollTop;

    if (typeof t.selectionStart != 'undefined') {
      var
        start = t.selectionStart,
        end = t.selectionEnd;
      var
        s1 = t.value.substring(0, start),
        s2 = t.value.substring(start, end),
        s3 = t.value.substring(end);

      s2 = (end != start) ? before + s2 + after : before + def + after;
      t.value = s1 + s2 + s3;
      t.focus();
      t.selectionStart = start + before.length;
      t.selectionEnd = start + (s2.length - after.length);
    }
    else if (typeof document.selection != 'undefined') {
      t.focus();
      var range = document.selection.createRange();
      var text = range.text;
      range.text = before + (text.length > 0 ? text : def) + after;
    }
    t.scrollTop = scroll;
  };

  /**
   * Get the currently selected text.
   */
  WikiEditor.prototype.getSelection = function () {
    var t = this.$el[0];
    if (typeof t.selectionStart != 'undefined') {
      var
        start = t.selectionStart,
        end = t.selectionEnd;
      return (start == end) ? '' : t.value.substring(start, end);
    }
    else if (typeof document.selection != 'undefined') {
      var range = document.selection.createRange();
      return range.text;
    }
  };

  /**
   * Replace the current selection with a new text.
   */
  WikiEditor.prototype.setSelection = function (text, reselect) {
    var t = this.$el[0];
    if (typeof t.selectionStart != 'undefined') {
      var
        start = t.selectionStart,
        end = t.selectionEnd;
      var
        s1 = t.value.substring(0, start),
        s2 = t.value.substring(end);

      t.value = s1 + text + s2;
      t.focus();
      if (reselect) {
        t.selectionStart = start;
        t.selectionEnd = start + text.length;
      }
      else
        t.selectionEnd = t.selectionStart = start + text.length;
    }
    else if (typeof document.selection != 'undefined') {
      t.focus();
      var range = document.selection.createRange();
      range.text = text;
      /* BUG: reselect? */
    }
  },

  /**
   * Insert text at the cursor position.  This works pretty much like
   * `setSelection` just that it deselects first.
   */
  WikiEditor.prototype.insertText = function (text) {
    var t = this.$el[0];
    if (typeof t.selectionStart != 'undefined') {
      t.selectionStart = t.selectionEnd;
    }
    this.setSelection(text);
  };

  /**
   * Get the current line as string.
   */
  WikiEditor.prototype.getCurrentLine = function () {
    var t = this.$el[0], i, c;
    if (typeof t.selectionStart != 'undefined') {
      var buffer = [];
      for (i = t.selectionEnd - 1; (c = t.value.charAt(i)) != '\n' && c; i--)
        buffer.push(c);
      buffer.reverse();
      for (i = t.selectionEnd; (c = t.value.charAt(i)) != '\n' && c; i++)
        buffer.push(c);
      return buffer.join('');
    }
    return '';
  };

  /**
   * Set the current line to a new value.
   */
  WikiEditor.prototype.setCurrentLine = function (text) {
    var t = this.$el[0];
    if (typeof t.selectionStart != 'undefined') {
      var start, end, c;
      for (start = t.selectionEnd - 1;
           (c = t.value.charAt(start)) != '\n' && c;
           start--)
      for (end = t.selectionEnd;
           (c = t.value.charAt(end)) != '\n' && c;
           end++)
      t.value = t.value.substring(0, start) + text + t.value.substring(end);
      t.selectionStart = t.selectionEnd = start + text.length;
    }
  },

  /**
   * Quote a given text.
   */
  WikiEditor.prototype.quoteText = function (text) {
    if (!text)
      return '';
    var lines = [];
    $.each(text.split(/\r\n|\r|\n/), function() {
      lines.push('>' + (this.charAt(0) != '>' ? ' ' : '') + this);
    });
    return lines.join('\n') + '\n';
  };

  $.fn.wikiEditor = function (options) {
    return this.each(function() {
      new WikiEditor(this, options);
    });
  };

  /*
   * Automatically detect form fields and transform them to a editor
   * field.
   *
   */

  $(document).ready(function () {
    $('textarea[data-enable-editor="true"]').each(function () {
      new WikiEditor($(this));
    });
  });


})(jQuery, document, window);
