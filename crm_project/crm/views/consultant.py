from django.shortcuts import render, redirect, reverse,HttpResponse
from crm import models
from crm.forms import Register_form, Customer_form,Consult_form,Enrollment_form,PaymentRecord_form
from django.db.models import Q
from django.views import View
from utils.pagination import Pagination
from django.db import transaction
from django.conf import global_settings,settings



# CBV实现公共客户、私有客户信息展示、公私客户转换、模糊匹配
class CustomerList(View):
    def get(self,request,*args,**kwargs):

        q = self.search(['qq','name','phone'])
        if request.path_info == reverse('customer_list'):
            all_customer = models.Customer.objects.filter(q,consultant__isnull=True)
            models.Customer.objects.filter()
        else:
            all_customer = models.Customer.objects.filter(q,consultant_id=request.session.get('user_id'))

        page = Pagination(request.GET.get('page',1),all_customer.count(),request.GET.copy(),4)
        return render(request, 'consultant/customer_list.html', {'all_customer': all_customer[page.start_num:page.end_num], 'page_html':page.page_html})

    def post(self,request,*args,**kwargs):
        action = request.POST.get('action')
        print(action)
        if not hasattr(self,action):
            return HttpResponse('非法操作')
        ret= getattr(self,action)()
        if ret:
            return ret
        return self.get(request,*args,**kwargs)

    # 公户转私户
    def multi_apply(self):
        # 获取要转为私户的pk列表
        pks = self.request.POST.getlist('pk')
        # 查看当前的客户的数量 + 要转为私户的列表长度 ，如果大于给出的私户上限数量，返回对应的页面
        if models.Customer.objects.filter(consultant=self.request.user_obj).count() + len(pks) > settings.MAX_CUSTOMER_NUM:
            return HttpResponse('做人不能太贪心')
        # 对公户转私户进行加事务
        try:
            with transaction.atomic():
                # 找到对应要转为私户的queryset（增强条件，无销售）进行加行级锁select_for_update
                queryset = models.Customer.objects.filter(pk__in=pks,consultant=None).select_for_update()
                # 如果要转为私户的pk列表的长度和pk__in=pks且无销售的queryset列表长度一致，才进行update到数据库
                if len(pks) == queryset.count():
                    queryset.update(consultant=self.request.user_obj)
                else:
                    return HttpResponse('手速太慢')
        except Exception  as e:
            print(e)
        # 方法一
        # models.Customer.objects.filter(pk__in=pks).update(consultant=self.request.user_obj)
        # models.Customer.objects.filter(pk__in=pks).update(consultant_id=self.request.session.get('user_id'))
        # 方法二(关系管理对象一对多)
        # self.request.user_obj.customers.add(*models.Customer.objects.filter(pk__in=pks))


    # 私户转公户
    def multi_pub(self):
        pks = self.request.POST.getlist('pk')
        # 方法一
        models.Customer.objects.filter(pk__in=pks).update(consultant=None)
        # 方法二
        # self.request.user_obj.customers.remove(*models.Customer.objects.filter(pk__in=pks))

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


# 二合一添加、编辑客户信息
def customer_change(request, pk=None):
    obj = models.Customer.objects.filter(pk=pk).first()
    consult_mes = models.ConsultRecord.objects.filter(pk=pk)
    print(consult_mes)
    form_obj = Customer_form(instance=obj)  # 实例  对象 拿到对应对象的原始数据，此时form_obj包含了原始数据
    if request.method == 'POST':
        form_obj = Customer_form(data=request.POST, instance=obj)
        if form_obj.is_valid():
            form_obj.save()
            next = request.GET.get('next')
            if next:
                return redirect(next)
            return redirect(reverse('own_customer'))
    title = '编辑客户' if pk else '添加客户'
    return render(request, 'form.html', {'form_obj': form_obj, 'title': title})






# 跟进记录表

class ConsultList(View):
    def get(self,request,customer_id=0,*args,**kwargs):
        if not customer_id:
            # 展示当前销售的所有的跟进记录
            all_consult = models.ConsultRecord.objects.filter(consultant=request.user_obj,delete_status=False)
        else:
            # 某一个客户的所有的跟进记录
            all_consult = models.ConsultRecord.objects.filter(customer_id=customer_id, delete_status=False)
        return render(request, 'consultant/consult_list.html', {'all_consult':all_consult.order_by('-date'), 'customer_id':customer_id})

# 增加的时候有两种情况，1.销售进行添加客户的跟进表，这时只可以展示该销售对应的客户，以及销售对应的也应该只能是他自己
                       #2.在我的私户中，进行查看某一个客户的对应所有的跟进情况，在这个条件下进行添加的时候，需要把对应的客户固定为不可变的
def consult_change(request,pk=None,customer_id=None):
    obj = models.ConsultRecord.objects.filter(pk=pk).first()
    form_obj = Consult_form(request,customer_id,instance=obj)
    if request.method == 'POST':
        form_obj = Consult_form(request,customer_id,data=request.POST,instance=obj)
        if form_obj.is_valid():
            form_obj.save()
            return redirect(reverse('consult_list'))
    title = '编辑客户' if pk else '添加客户'
    return render(request, 'form.html', {'form_obj':form_obj, 'title':title})

# FBV
# def consult_list(request):
#     # obj = models.Customer.objects.filter(pk=pk).first()
#     # all_customer = obj.consultrecord_set.all()
#     consult_customers = models.ConsultRecord.objects.filter(consultant=request.user_obj)
#     return render(request,'consult_list.html',{'consult_customers':consult_customers})
#
# # 添加、编辑二合一跟进记录
# def consult_change(request,pk=None):
#     obj = models.ConsultRecord.objects.filter(pk=pk).first()
#     form_obj = Consult_form(request,instance=obj)
#     if request.method == 'POST':
#         form_obj = Consult_form(request,data=request.POST,instance=obj)
#         if form_obj.is_valid():
#             print(111111)
#             form_obj.save()
#             print(22222)
#             return redirect(reverse('consult_list'))
#     button = '编辑' if pk else '添加'
#     return render(request,'consult_form.html',{'form_obj':form_obj,'button':button})
#
# # 显示每个客户的跟进信息
# def show_consult(reqeust,pk=None):
#     obj = models.Customer.objects.filter(pk=pk).first()
#     consult_customers = obj.consultrecord_set.all()
#     return render(reqeust,'consult_list.html',{'consult_customers':consult_customers})



# 报名表的管理
class EnrollmentList(View):
    def get(self,request,*args,customer_id=0,**kwargs):
        # 展示一个销售的报名记录表
        if not customer_id:
            all_enrollment = models.Enrollment.objects.filter(customer__in=request.user_obj.customers.all(),delete_status=False)
            print(all_enrollment)
        # 展示一个客户的报名记录表
        else:
            all_enrollment = models.Enrollment.objects.filter(customer_id=customer_id,delete_status=False)
        return render(request, 'consultant/enrollment_list.html', {'all_enrollment': all_enrollment.order_by('-enrolled_date'),'customer_id':customer_id })

def enrollment_change(reqeust,pk=None,customer_id=None):
    # obj = models.Enrollment.objects.filter(pk=pk).first()
    obj = models.Enrollment(customer_id=customer_id,) if customer_id else models.Enrollment.objects.filter(pk=pk).first()
    form_obj = Enrollment_form(reqeust,instance=obj)
    if reqeust.method == 'POST':
        form_obj = Enrollment_form(reqeust,data=reqeust.POST,instance=obj)
        if form_obj.is_valid():
            form_obj.save()
            return redirect(reverse('enrollment_list'))
    title = '编辑客户' if pk else '添加客户'
    return render(reqeust, 'form.html', {'form_obj':form_obj, 'title':title})


# 缴费记录表
class PaymentRecordlist(View):
    def get(self,request,*args,customer_id=None,**kwargs):
        # 查看销售填写的缴费记录表
        if not customer_id:
            all_payment_records = models.PaymentRecord.objects.filter(consultant=request.user_obj,delete_status=False)
        else:
            all_payment_records = models.PaymentRecord.objects.filter(customer_id=customer_id,delete_status=False)

        page = Pagination(request.GET.get('page'),all_payment_records.count(),request.GET.copy(),3)
        return render(request,'consultant/payment_record_list.html',{'all_payment_records':all_payment_records[page.start_num:page.end_num],'page_html':page.page_html,'customer_id':customer_id})

def payment_record_change(request,pk=None,customer_id=0):
    obj =models.PaymentRecord(customer_id=customer_id,consultant=request.user_obj) if customer_id else models.PaymentRecord.objects.filter(pk=pk).first()
    form_obj = PaymentRecord_form(request,instance=obj)
    if request.method == 'POST':
        form_obj = PaymentRecord_form(request,data=request.POST,instance=obj)
        if form_obj.is_valid():
            form_obj.save()
            next = request.GET.get('next')
            if next:
                return redirect(next)
            return redirect(reverse('payment_record_list'))
    title = '编辑缴费记录' if pk else '添加缴费记录'
    return render(request,'form.html',{'form_obj':form_obj,'title':title})
















# 用户表分页
user = [{'user': 'alex-{}'.format(i, ), 'pwd': '123'} for i in range(1, 921)]


def user_list(request):
    page = Pagination(request.GET.get('page', 1), len(user))
    return render(request, 'user_list.html', {'user': user[page.start_num:page.end_num], 'page_html': page.page_html})

