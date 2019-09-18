from django import template
from django.urls import reverse
from django.http.request import QueryDict
register = template.Library()

@register.simple_tag
def reverse_url(request,name,*args,**kwargs):
    # 获取当前访问的路径
    next = request.get_full_path()

    url = reverse(name,args=args,kwargs=kwargs)
    qd = QueryDict(mutable=True)
    qd['next'] = next
    return_url = "{}?{}".format(url,qd.urlencode())
    return return_url