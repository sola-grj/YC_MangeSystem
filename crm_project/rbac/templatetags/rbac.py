from django import template
from django.conf import settings
import re

register = template.Library()
from collections import OrderedDict


@register.inclusion_tag('rbac/menu.html')
def menu(request):
    menu_dict = request.session.get(settings.MENU_SESSION_KEY)
    # url = request.path_info
    od = OrderedDict()
    keys_list = sorted(menu_dict, key=lambda x: menu_dict[x]['weight'], reverse=True)

    for key in keys_list:
        od[key] = menu_dict[key]

    for i in menu_dict.values():
        i['class'] = 'hide'
        for m in i['children']:
            if request.current_menu_id == m.get('id'):
                m['class'] = 'active'
                i['class'] = ''

    return {'menu_list': od.values()}


@register.inclusion_tag('rbac/breadcrumb.html')
def breadcrumb(request):
    breadcrumb_list = request.breadcrumb_list
    return {'breadcrumb_list': breadcrumb_list}


@register.filter
def has_permission(request, name):
    permission_dict = request.session.get(settings.PERMISSION_SESSION_KEY)
    if name in permission_dict:
        return True


@register.simple_tag
def gen_role_url(request, rid):
    params = request.GET.copy()
    params['rid'] = rid
    return params.urlencode()
