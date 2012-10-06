from django.http import HttpResponseRedirect

# FIXME: user.status == 0...

def collect_registration_info(request, user=None, *args, **kwargs):
    if user is None and not request.session.get('social_auth_data'):
        return HttpResponseRedirect('/register/external/')

def get_username(request, user=None, *args, **kwargs):
    if user is not None:
        return {'username': user.username}
    data = request.session.pop('social_auth_data')
    return {'username': data['username']}
