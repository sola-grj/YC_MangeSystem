from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse
from django.shortcuts import redirect, HttpResponse
from django.conf import settings
import re


class AuthMiddleWare(MiddlewareMixin):
    def process_request(self, request):
        # 获取当前访问的URL
        path = request.path_info

        request.current_menu_id = None

        request.breadcrumb_list = [
            {'title': '首页', 'url': '/index/'}
        ]
        # 白名单
        for url in settings.WHITE_LIST:
            if re.match(url, path):
                return
        # 登录状态的校验
        is_login = request.session.get('is_login')
        if not is_login:
            return redirect(reverse('login'))
            # 免认证的校验
        for url in settings.NO_PERMISSION_LIST:
            if re.match(url, path):
                return
        # 获取权限信息
        permissions_dict = request.session.get(settings.PERMISSION_SESSION_KEY)

        # 权限的校验
        for i in permissions_dict.values():
            if re.match(r"{}$".format(i['url']), path):
                # 记录二级菜单的id（父权限的id）
                id = i['id']
                pid = i['pid']
                if pid:
                    # 当前访问的是一个子权限
                    request.current_menu_id = pid
                    # p_permission = permissions_dict[str(pid)]
                    p_permission = permissions_dict[i['pname']]

                    request.breadcrumb_list.append({'url': p_permission['url'], 'title': p_permission['title']})
                    request.breadcrumb_list.append({'url': i['url'], 'title': i['title']})
                else:
                    # 当前访问的是一个父权限（二级菜单）
                    request.current_menu_id = id
                    request.breadcrumb_list.append({'url': i['url'], 'title': i['title']})
                return
        return HttpResponse('没有访问权限,请联系管理员')
