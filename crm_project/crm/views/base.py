from django.views import View
from django.shortcuts import render, redirect, reverse,HttpResponse
from django.db.models import Q
class BaseView(View):

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        print(action)
        if not hasattr(self, action):
            return HttpResponse('非法操作')
        ret = getattr(self, action)()
        if ret:
            return ret
        return self.get(request, *args, **kwargs)


    # 搜索
    def search(self,field_list):
        # 构建Q对象
        # q = Q(qq__contains=query)|Q(name__contains=query)|Q(phone__contains=query),

        query = self.request.GET.get('query','')
        q = Q()
        q.connector = 'OR'  # 表示为or的关系
        # q.children.append(Q(('qq__contains',query))) # 变成元组等价Q(qq__contains=query)
        for field in field_list:
            q.children.append(Q(('{}__contains'.format(field), query)))
        return q
