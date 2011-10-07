# -*- coding: utf-8 -*-
"""
    inyoka.pastebin.forms
    ~~~~~~~~~~~~~~~~~~~~~

    "Add new paste" formular.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django import forms
from django.utils.translation import ugettext_lazy as _

from inyoka.utils.forms import CaptchaField
from inyoka.pastebin.models import Entry


# languages for highlighting. We do not use the full list of pygments
# lexers because that is just insane ;-)
LANGUAGES = [
    ('text', _('Plain text')),
    ('apache', _('Apache Config (.htaccess)'))),
    ('bash', _('Bash')),
    ('bat', _('Batch (.bat)')),
    ('c', _('C')),
    ('csharp', _('C#')),
    ('cpp', _('C++')),
    ('css', _('CSS')),
    ('d', _('D')),
    ('html+django', _('Django / Jinja Templates')),
    ('rhtml', _('eRuby / rhtml')),
    ('html+genshi', _('Genshi Templates')),
    ('haskell', _('Haskell')),
    ('html', _('HTML')),
    ('irc', _('IRC Logs')),
    ('java', _('Java')),
    ('js', _('JavaScript')),
    ('jsp', _('JSP')),
    ('lua', _('Lua')),
    ('html+mako', _('Mako Templates')),
    ('minid', _('MiniD')),
    ('html+myghty', _('Myghty Templates')),
    ('ocaml', _('OCaml')),
    ('perl', _('Perl')),
    ('html+php', _('PHP')),
    ('python', _('Python')),
    ('pycon', _('Python Console Sessions')),
    ('pytb', _('Python Tracebacks')),
    ('rst', _('reStructuredText')),
    ('ruby', _('Ruby')),
    ('scheme', _('Scheme')),
    ('smarty', _('Smarty')),
    ('sourceslist', _('sources.list')),
    ('sql', _('SQL')),
    ('squidconf', _('SquidConf')),
    ('tex', _('TeX / LaTeX')),
    ('diff', _('Unified Diff')),
    ('vim', _('Vim Scripts')),
    ('xml', _('XML')
]


class AddPasteForm(forms.ModelForm):
    title = forms.CharField(max_length=40, required=False, label=_('Title'))
    lang = forms.ChoiceField(widget=forms.Select, label=_('Language'),
                             choices=LANGUAGES)
    captcha = CaptchaField(label=_(u'CAPTCHA'), only_anonymous=True)

    def save(self, user, commit=True):
        entry = super(AddPasteForm, self).save(commit=False)
        entry.author = user
        entry.title = entry.title or _('Untitled')
        if commit:
            entry.save()
        return entry

    class Meta:
        model = Entry
        fields = ('title', 'lang', 'code')
