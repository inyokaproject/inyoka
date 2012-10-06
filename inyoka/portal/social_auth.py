from django.http import HttpResponseRedirect
from django.utils.http import urlencode

# FIXME: user.status == 0...

def collect_registration_info(request, details, user=None, *args, **kwargs):
    if user is None and not request.session.get('social_auth_data'):
        d = {'username': details.get('username', ''),
             'email': details.get('email', '')}
        return HttpResponseRedirect('/register/external/?' + urlencode(d))

def get_username(request, user=None, *args, **kwargs):
    if user is not None:
        return {'username': user.username}
    data = request.session.pop('social_auth_data')
    return {'username': data['username']}
