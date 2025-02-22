"""
    inyoka.filters
    ~~~~~~~~~~~~~~

    `QuerySet` filter based on `django-filters <https://github.com/alex/django-filter>`_

    :copyright: (c) 2011-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from itertools import chain

from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy
from django_filters import ChoiceFilter, FilterSet
from django_filters.widgets import LinkWidget as BaseLinkWidget

from inyoka.portal.models import Subscription
from inyoka.utils.urls import urlencode

SUPPORTED_SUBSCRIPTION_TYPES = {
    'topic': gettext_lazy('Topic'),
    'forum': gettext_lazy('Forum'),
    'article': gettext_lazy('Ikhaya article'),
    'page': gettext_lazy('Wiki page')
}


class LinkWidget(BaseLinkWidget):

    def render_options(self, choices, selected_choices, name):
        selected_choices = {force_str(v) for v in selected_choices}
        output = []
        for option_value, option_label in chain(self.choices, choices):
            if option_label:
                output.append(self.render_option(name, selected_choices, option_value, option_label))
        return '\n'.join(output)

    def render_option(self, name, selected_choices, option_value, option_label):
        option_value = force_str(option_value)
        if option_label == '':
            option_label = gettext_lazy('All types')
        data = self.data.copy()
        data[name] = option_value
        selected = data == self.data or option_value in selected_choices
        try:
            url = data.urlencode()
        except AttributeError:
            url = urlencode(data)
        return self.option_string() % {
            'attrs': selected and ' class="selected"' or '',
            'query_string': url,
            'label': force_str(option_label)
        }

    def option_string(self):
        return '<li><a%(attrs)s href="?%(query_string)s">%(label)s</a></li>'


class SubscriptionFilter(FilterSet):
    content_type = ChoiceFilter(field_name='content_type__model', label='',
        choices=tuple(SUPPORTED_SUBSCRIPTION_TYPES.items()),
        widget=LinkWidget, empty_label=gettext_lazy('All types'))

    class Meta:
        model = Subscription
        fields = []
