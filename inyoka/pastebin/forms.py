# -*- coding: utf-8 -*-
"""
    inyoka.pastebin.forms
    ~~~~~~~~~~~~~~~~~~~~~

    "Add new paste" formular.

    :copyright: (c) 2007-2021 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django import forms
from django.utils.translation import ugettext, ugettext_lazy

from inyoka.pastebin.models import Entry

# languages for highlighting. We do not use the full list of pygments
# lexers because that is just insane ;-)
LANGUAGES = [
    ('text', ugettext_lazy('Plain text')),
    ('apache', ugettext_lazy('Apache Config (.htaccess)')),
    ('bash', ugettext_lazy('Bash')),
    ('bat', ugettext_lazy('Batch (.bat)')),
    ('c', ugettext_lazy('C')),
    ('csharp', ugettext_lazy('C#')),
    ('cpp', ugettext_lazy('C++')),
    ('css', ugettext_lazy('CSS')),
    ('d', ugettext_lazy('D')),
    ('html+django', ugettext_lazy('Django / Jinja Templates')),
    ('rhtml', ugettext_lazy('eRuby / rhtml')),
    ('html+genshi', ugettext_lazy('Genshi Templates')),
    ('haskell', ugettext_lazy('Haskell')),
    ('html', ugettext_lazy('HTML')),
    ('irc', ugettext_lazy('IRC Logs')),
    ('java', ugettext_lazy('Java')),
    ('js', ugettext_lazy('JavaScript')),
    ('jsp', ugettext_lazy('JSP')),
    ('lua', ugettext_lazy('Lua')),
    ('html+mako', ugettext_lazy('Mako Templates')),
    ('minid', ugettext_lazy('MiniD')),
    ('html+myghty', ugettext_lazy('Myghty Templates')),
    ('ocaml', ugettext_lazy('OCaml')),
    ('perl', ugettext_lazy('Perl')),
    ('html+php', ugettext_lazy('PHP')),
    ('python', ugettext_lazy('Python')),
    ('pycon', ugettext_lazy('Python Console Sessions')),
    ('pytb', ugettext_lazy('Python Tracebacks')),
    ('rst', ugettext_lazy('reStructuredText')),
    ('ruby', ugettext_lazy('Ruby')),
    ('scheme', ugettext_lazy('Scheme')),
    ('smarty', ugettext_lazy('Smarty')),
    ('sourceslist', ugettext_lazy('sources.list')),
    ('sql', ugettext_lazy('SQL')),
    ('squidconf', ugettext_lazy('SquidConf')),
    ('tex', ugettext_lazy('TeX / LaTeX')),
    ('diff', ugettext_lazy('Unified Diff')),
    ('vim', ugettext_lazy('Vim Scripts')),
    ('xml', ugettext_lazy('XML')),
]


class AddPasteForm(forms.ModelForm):
    title = forms.CharField(max_length=40, required=False, label=ugettext_lazy('Title'))
    lang = forms.ChoiceField(widget=forms.Select, label=ugettext_lazy('Language'),
                             choices=LANGUAGES)

    def save(self, user, commit=True):
        entry = super(AddPasteForm, self).save(commit=False)
        entry.author = user
        entry.title = entry.title or ugettext('Untitled')
        if commit:
            entry.save()
        return entry

    class Meta:
        model = Entry
        fields = ('title', 'lang', 'code')
