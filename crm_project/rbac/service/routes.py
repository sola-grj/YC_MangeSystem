from django.conf import settings
from django.utils.module_loading import import_string
from django.urls import RegexURLResolver, RegexURLPattern
from collections import OrderedDict


def recursion_urls(pre_namespace, pre_url, urlpatterns, url_ordered_dict):
    """
    None, "/", urlpatterns  url_ordered_dict
    [
            url(r'^', include('web.urls')),
            url(r'^rbac/', include('rbac.urls')),
    ]

    """

    """
     None   "/^"   [
    url(r'^role/list/$', views.role_list, name='role_list'),
    url(r'^role/add/$', views.role_change, name='role_add'), 
    ] 
    """

    for item in urlpatterns:
        if isinstance(item, RegexURLResolver):
            if pre_namespace:
                if item.namespace:
                    namespace = "%s:%s" % (pre_namespace, item.namespace,)
                else:
                    namespace = pre_namespace
            else:
                if item.namespace:
                    namespace = item.namespace
                else:
                    namespace = None
            # None   "/^"
            recursion_urls(namespace, pre_url + item.regex.pattern, item.url_patterns, url_ordered_dict)
        else:
            if pre_namespace:
                name = "%s:%s" % (pre_namespace, item.name,)
            else:
                name = item.name   #  role_list
            if not item.name:
                raise Exception('URL路由中必须设置name属性')
            #   name  role_list
            url = pre_url + item._regex  #   "/^^role/list/$"    '/role/list/'
            url_ordered_dict[name] = {'name': name, 'url': url.replace('^', '').replace('$', '')}


def get_all_url_dict(ignore_namespace_list=None):
    """
    获取路由中
    :return:
    """
    ignore_list = ignore_namespace_list or []
    url_ordered_dict = OrderedDict()

    md = import_string(settings.ROOT_URLCONF)
    urlpatterns = []

    for item in md.urlpatterns:
        """
        [
            url(r'^admin/', admin.site.urls),
            url(r'^', include('web.urls')),
            url(r'^rbac/', include('rbac.urls')),
           
            视图     RegexURLPattern
            include  RegexURLResolver
        ]  
        """
        if isinstance(item, RegexURLResolver) and item.namespace in ignore_list:
            continue
        urlpatterns.append(item)
    recursion_urls(None, "/", urlpatterns, url_ordered_dict)
    return url_ordered_dict
