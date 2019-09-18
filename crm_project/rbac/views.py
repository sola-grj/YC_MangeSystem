from django.shortcuts import render, redirect, reverse, HttpResponse
from rbac import models
from rbac.forms import RoleForm, MenuForm, PermissionForm, MultiPermissionForm
from rbac.service.routes import get_all_url_dict


def role_list(request):
    all_roles = models.Role.objects.all()
    return render(request, 'rbac/role_list.html', {'all_roles': all_roles})


def role_change(request, pk=None):
    obj = models.Role.objects.filter(pk=pk).first()
    form_obj = RoleForm(instance=obj)
    if request.method == 'POST':
        form_obj = RoleForm(request.POST, instance=obj)
        if form_obj.is_valid():
            form_obj.save()
            return redirect(reverse('role_list'))
    return render(request, 'form.html', {'form_obj': form_obj})


from django.db.models import Q


def menu_list(request):
    mid = request.GET.get('mid')

    all_menus = models.Menu.objects.all()
    if not mid:
        all_permissions = models.Permission.objects.all()
    else:
        all_permissions = models.Permission.objects.filter(Q(menu_id=mid) | Q(parent__menu_id=mid))

    """
    { id : {
                children： [ {}  {} ]
         } 
    }

    """
    permission_dict = {}

    for i in all_permissions.values('id', 'title', 'url', 'name', 'menu_id', 'menu__title', 'parent_id'):
        menu_id = i.get('menu_id')
        if menu_id:
            permission_dict[i['id']] = i
            i['children'] = []

    for i in all_permissions.values('id', 'title', 'url', 'name', 'menu_id', 'menu__title', 'parent_id'):
        pid = i.get('parent_id')
        if pid:
            permission_dict[pid]['children'].append(i)

    print(permission_dict)

    return render(request, 'rbac/menu_list.html', {
        'all_menus': all_menus,
        'all_permissions': permission_dict.values(),
        'mid': mid
    })


def menu_change(request, pk=None):
    obj = models.Menu.objects.filter(pk=pk).first()
    form_obj = MenuForm(instance=obj)
    if request.method == 'POST':
        form_obj = MenuForm(request.POST, instance=obj)
        if form_obj.is_valid():
            form_obj.save()
            return redirect(reverse('menu_list'))
    return render(request, 'form.html', {'form_obj': form_obj})


def permission_change(request, pk=None):
    obj = models.Permission.objects.filter(pk=pk).first()
    form_obj = PermissionForm(instance=obj)
    if request.method == 'POST':
        form_obj = PermissionForm(request.POST, instance=obj)
        if form_obj.is_valid():
            form_obj.save()
            return redirect(reverse('menu_list'))
    return render(request, 'form.html', {'form_obj': form_obj})


def delete(request, table, pk):
    table_class = getattr(models, table.capitalize())
    table_class.objects.filter(pk=pk).delete()
    if table == 'permission':
        return redirect(reverse('menu_list'))
    return redirect(reverse('{}_list'.format(table)))


# 批量操作权限
from django.forms import modelformset_factory, formset_factory


def multi_permissions(request):
    """
    批量操作权限
    :param request:
    :return:
    """
    post_type = request.GET.get('type')
    # 更新和删除
    FormSet = modelformset_factory(models.Permission, MultiPermissionForm, extra=0)
    # 新增
    AddFormSet = formset_factory(MultiPermissionForm, extra=0)

    # 数据库所有的权限
    permissions = models.Permission.objects.all()
    # 路由系统中所有的权限
    router_dict = get_all_url_dict(ignore_namespace_list=['admin', ])

    # 数据库权限的别名的集合
    permissions_name_set = set([i.name for i in permissions])
    # 路由系统中权限的别名的集合
    router_name_set = set(router_dict.keys())

    # 新增权限的别名的集合
    add_name_set = router_name_set - permissions_name_set
    add_formset = AddFormSet(initial=[row for name, row in router_dict.items() if name in add_name_set])

    if request.method == 'POST' and post_type == 'add':
        add_formset = AddFormSet(request.POST)
        if add_formset.is_valid():
            permission_obj_list = [models.Permission(**i) for i in add_formset.cleaned_data]
            query_list = models.Permission.objects.bulk_create(permission_obj_list)
            add_formset = AddFormSet()
            for i in query_list:
                permissions_name_set.add(i.name)

    # 删除的name的集合
    del_name_set = permissions_name_set - router_name_set
    del_formset = FormSet(queryset=models.Permission.objects.filter(name__in=del_name_set))
    # 更新的name的集合
    update_name_set = permissions_name_set & router_name_set
    update_formset = FormSet(queryset=models.Permission.objects.filter(name__in=update_name_set))

    if request.method == 'POST' and post_type == 'update':
        update_formset = FormSet(request.POST)
        if update_formset.is_valid():
            update_formset.save()
            update_formset = FormSet(queryset=models.Permission.objects.filter(name__in=update_name_set))

    return render(
        request,
        'rbac/multi_permissions.html',
        {
            'del_formset': del_formset,
            'update_formset': update_formset,
            'add_formset': add_formset,
        }
    )

from crm.models import UserProfile
def distribute_permissions(request):
    """
    分配权限
    :param request:
    :return:
    """
    # 用户的id
    uid = request.GET.get('uid')
    rid = request.GET.get('rid')

    if request.method == 'POST' and request.POST.get('postType') == 'role':
        user = UserProfile.objects.filter(id=uid).first()
        if not user:
            return HttpResponse('用户不存在')
        user.roles.set(request.POST.getlist('roles'))

    if request.method == 'POST' and request.POST.get('postType') == 'permission' and rid:
        role = models.Role.objects.filter(id=rid).first()
        if not role:
            return HttpResponse('角色不存在')
        role.permissions.set(request.POST.getlist('permissions'))


    # 所有的用户
    user_list = UserProfile.objects.all()
    # 用户所拥有角色id
    user_has_roles = UserProfile.objects.filter(id=uid).values('id', 'roles')
    # 用户所拥有角色id的字典
    user_has_roles_dict = {item['roles']: None for item in user_has_roles}
    # 所有的角色
    role_list = models.Role.objects.all()

    if rid:
        role_has_permissions = models.Role.objects.filter(id=rid, permissions__id__isnull=False).values('id',
                                                                                                        'permissions')
    elif uid and not rid:
        # 用户的对象
        user = UserProfile.objects.filter(id=uid).first()
        if not user:
            return HttpResponse('用户不存在')
        # 当前用户所有的权限的 【{ role_id  permission_id  }】
        role_has_permissions = user.roles.filter(permissions__id__isnull=False).values('id', 'permissions')
    else:
        role_has_permissions = []
    # 用户所拥有的权限的字典
    role_has_permissions_dict = {item['permissions']: None for item in role_has_permissions}

    # 所有的菜单
    all_menu_list = []

    """
    all_menu_list = [ {   id   title children:[
            {  'id', 'title', 'menu_id'  children : [
                     { 'id', 'title', 'parent_id'  }
            ]  }
    ]   }
     
        {'id': None, 'title': '其他', 'children': [
              { 'id', 'title', 'parent_id'：None  }
        ]}
     ]
    """

    queryset = models.Menu.objects.values('id', 'title')
    menu_dict = {}
    """
    menu_dict = { 一级菜单的id: {   id   title children:[
                    {  'id', 'title', 'menu_id'  children : [
                             { 'id', 'title', 'parent_id'  }
                        ]  }
            ]   } ,
                None:{'id': None, 'title': '其他', 'children': [
                    
                     { 'id', 'title', 'parent_id'：None  }
                ]}
    }
    
    """

    for item in queryset:  #  item  {   id   title children:[]   }
        item['children'] = []
        menu_dict[item['id']] = item
        all_menu_list.append(item)

    other = {'id': None, 'title': '其他', 'children': []}
    all_menu_list.append(other)
    menu_dict[None] = other

    root_permission = models.Permission.objects.filter(menu__isnull=False).values('id', 'title', 'menu_id')
    root_permission_dict = {}
    """
    root_permission_dict = {
        二级菜单的id： {  'id', 'title', 'menu_id'  children : [
            { 'id', 'title', 'parent_id'  }
        ]  }  
    }
    """

    for per in root_permission:  #  per  {  'id', 'title', 'menu_id'  children : []  }
        per['children'] = []
        nid = per['id']
        menu_id = per['menu_id']
        root_permission_dict[nid] = per
        menu_dict[menu_id]['children'].append(per)

    node_permission = models.Permission.objects.filter(menu__isnull=True).values('id', 'title', 'parent_id')

    for per in node_permission:   # per   { 'id', 'title', 'parent_id'  }
        pid = per['parent_id']
        if not pid:
            menu_dict[None]['children'].append(per)
            continue
        root_permission_dict[pid]['children'].append(per)

    return render(
        request,
        'rbac/distribute_permissions.html',
        {
            'user_list': user_list,
            'role_list': role_list,
            'user_has_roles_dict': user_has_roles_dict,
            'role_has_permissions_dict': role_has_permissions_dict,
            'all_menu_list': all_menu_list,
            'uid': uid,
            'rid': rid
        }
    )
