# -*- coding: utf-8 -*-
"""
    inyoka.pastebin.forms
    ~~~~~~~~~~~~~~~~~~~~~

    "Add new paste" formular.

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django import forms
from django.utils.translation import gettext, gettext_lazy

from inyoka.pastebin.models import Entry

# languages for highlighting. We do not use the full list of pygments
# lexers because that is just insane ;-)
LANGUAGES = [
    ('text', gettext_lazy('Plain text')),
    ('apache', gettext_lazy('Apache Config (.htaccess)')),
    ('bash', gettext_lazy('Bash')),
    ('bat', gettext_lazy('Batch (.bat)')),
    ('c', gettext_lazy('C')),
    ('csharp', gettext_lazy('C#')),
    ('cpp', gettext_lazy('C++')),
    ('css', gettext_lazy('CSS')),
    ('d', gettext_lazy('D')),
    ('html+django', gettext_lazy('Django / Jinja Templates')),
    ('rhtml', gettext_lazy('eRuby / rhtml')),
    ('html+genshi', gettext_lazy('Genshi Templates')),
    ('haskell', gettext_lazy('Haskell')),
    ('html', gettext_lazy('HTML')),
    ('irc', gettext_lazy('IRC Logs')),
    ('java', gettext_lazy('Java')),
    ('js', gettext_lazy('JavaScript')),
    ('jsp', gettext_lazy('JSP')),
    ('lua', gettext_lazy('Lua')),
    ('html+mako', gettext_lazy('Mako Templates')),
    ('minid', gettext_lazy('MiniD')),
    ('html+myghty', gettext_lazy('Myghty Templates')),
    ('ocaml', gettext_lazy('OCaml')),
    ('perl', gettext_lazy('Perl')),
    ('html+php', gettext_lazy('PHP')),
    ('python', gettext_lazy('Python')),
    ('pycon', gettext_lazy('Python Console Sessions')),
    ('pytb', gettext_lazy('Python Tracebacks')),
    ('rst', gettext_lazy('reStructuredText')),
    ('ruby', gettext_lazy('Ruby')),
    ('scheme', gettext_lazy('Scheme')),
    ('smarty', gettext_lazy('Smarty')),
    ('sourceslist', gettext_lazy('sources.list')),
    ('sql', gettext_lazy('SQL')),
    ('squidconf', gettext_lazy('SquidConf')),
    ('tex', gettext_lazy('TeX / LaTeX')),
    ('diff', gettext_lazy('Unified Diff')),
    ('vim', gettext_lazy('Vim Scripts')),
    ('xml', gettext_lazy('XML')),
]


class AddPasteForm(forms.ModelForm):
    title = forms.CharField(max_length=40, required=False, label=gettext_lazy('Title'))
    lang = forms.ChoiceField(widget=forms.Select, label=gettext_lazy('Language'),
                             choices=LANGUAGES)

    def save(self, user, commit=True):
        entry = super(AddPasteForm, self).save(commit=False)
        entry.author = user
        entry.title = entry.title or gettext('Untitled')
        if commit:
            entry.save()
        return entry

    class Meta:
        model = Entry
        fields = ('title', 'lang', 'code')
