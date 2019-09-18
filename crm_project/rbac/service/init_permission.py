from django.conf import settings


def init_permission(request, obj):
    # 获取权限
    permissions = obj.roles.filter(permissions__url__isnull=False).values(
        'permissions__url',
        'permissions__title',
        'permissions__menu__title',
        'permissions__menu__icon',
        'permissions__menu__weight',
        'permissions__menu_id',
        'permissions__id',
        'permissions__name',
        'permissions__parent__name',
        'permissions__parent_id',
    ).distinct()

    # 权限信息的字典
    permission_dict = {}
    # 菜单信息的字典
    menu_dict = {}

    for i in permissions:  # {  'permissions__url', }
        permission_dict[i['permissions__name']] = {
            'url': i['permissions__url'],
            'id': i['permissions__id'],
            'pid': i['permissions__parent_id'],
            'pname': i['permissions__parent__name'],
            'title': i['permissions__title']
        }

        menu_id = i.get('permissions__menu_id')
        if not menu_id:
            continue

        if menu_id not in menu_dict:
            menu_dict[menu_id] = {
                'title': i.get('permissions__menu__title'),
                'icon': i.get('permissions__menu__icon'),
                'weight': i.get('permissions__menu__weight'),
                'children': [
                    {'title': i.get('permissions__title'), 'url': i.get('permissions__url'),
                     'id': i.get('permissions__id')}
                ]
            }
        else:
            menu_dict[menu_id]['children'].append(
                {'title': i.get('permissions__title'), 'url': i.get('permissions__url'),
                 'id': i.get('permissions__id')})



    # 保存到session中
    request.session[settings.PERMISSION_SESSION_KEY] = permission_dict  # json序列化
    request.session[settings.MENU_SESSION_KEY] = menu_dict  # json序列化
    request.session['is_login'] = True
