# -*- coding: utf-8 -*-
"""
    inyoka.utils.sortable
    ~~~~~~~~~~~~~~~~~~~~~

    This file helps creating a sortable Table.

    You can create a new instance of `Sortable` this way::

        >>> from inyoka.portal.user import User
        >>> table = Sortable(User.objects.all(), {}, 'id')

    :Parameters:
        objects
            This has to be a django database query set that should be sorted.
            Use the `get_queryset()` to get it back in the right order.
        args
            The GET arguments (request.args).
        default
            Defines the default sorting mode.

    Every instance of `Sortable` has these methods:

        - get_html:
            Returns a HTML link for sorting the table.
            This function is usually called inside the template.

            :Parameters:
                key
                    The name of the database column that should be used for
                    sorting.
                value
                    The name that is displayed for the link.

        - get_queryset:
            Returns an ordered database query set.

    A working example of a box would look like this:
    Inside Python File::

        from inyoka.utils.sortable import Sortable
        from inyoka.portal.user import User

        @templated('portal/memberlist.html')
        def memberlist(req):
            table = Sortable(User.objects.all(), req.GET, 'id')
            return {
                'users': list(table.get_queryset()),
                'table': table
            }

    Inside the template file::

        <tr>
          <th>
            {{ table.get_html('id', '#') }}
          </th>
          <th>
            {{ table.get_html('username', 'Benutzername') }}
          </th>
        </tr>
        {% for user in users %}
          (...)
        {% endfor %}

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.contrib import messages
from django.utils.html import escape

from inyoka.utils.local import current_request
from django.utils.translation import ugettext as _
from inyoka.utils.urls import href


class Sortable(object):

    def __init__(self, objects, args, default, columns=None):
        self.objects = objects
        self.order = args.get('order') or default
        self.order_column = self.order.startswith('-') and self.order[1:] or \
                            self.order
        self.default = default
        self.columns = columns or []

    def get_html(self, key, value):
        if key == self.order_column:
            args = (not self.order.startswith('-') and '-' or '',
                    self.order_column)
            new_order = '%s%s' % args
            img = '<img src="%s" alt="" />' % href('static', 'img',
                '%s.png' % (self.order.startswith('-') and 'down' or 'up'))
        else:
            new_order = key
            img = ''
        return '<a href="?order=%s">%s</a>%s' % (
            new_order, value, img)

    def get_queryset(self):
        order = self.order
        ocol = escape(order.lstrip('-'))
        if self.columns and not ocol in self.columns:
            # safes us for some bad usage that raises an exception
            messages.info(current_request,
                _(u'The chosen sort value (“%(value)s”) is not available')
                % {'value': ocol})
            return self.objects

        q = self.objects.order_by(order)
        return q
