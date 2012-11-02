#-*- coding: utf-8 -*-
from django.conf import settings
from django.test import TestCase

from django.utils.translation import ugettext as _
from inyoka.portal.user import Group, User, PERMISSION_NAMES
from inyoka.utils.storage import storage
from inyoka.utils.test import InyokaClient
from inyoka.utils.urls import href


class TestViews(TestCase):

    client_class = InyokaClient
    permissions = sum(PERMISSION_NAMES.keys())

    def setUp(self):
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin._permissions = self.permissions
        self.admin.save()

        self.client.defaults['HTTP_HOST'] = settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_group(self):
        storage['team_icon_height'] = 80
        storage['team_icon_width'] = 80

        postdata = {u'name': u'Lorem'}
        response = self.client.post('/group/new/', postdata)
        self.assertEqual(response.status_code, 302)

        postdata = {u'name': u'LOr3m'}
        response = self.client.post('/group/Lorem/edit/', postdata)
        self.assertFalse('<ul class="errorlist"><li>%s</li></ul>' % _(
                u'The group name contains invalid chars') in \
                    response.content.decode('utf-8'))

        postdata = {u'name': u'£Ø®€m'}
        response = self.client.post('/group/LOr3m/edit/', postdata)
        self.assertTrue('<ul class="errorlist"><li>%s</li></ul>' % _(
                u'The group name contains invalid chars') in \
                    response.content.decode('utf-8'))

