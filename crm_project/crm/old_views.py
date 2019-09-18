from django.shortcuts import render, redirect, reverse,HttpResponse
from crm import models
from crm.forms import Register_form, Customer_form,Consult_form,Enrollment_form,Class_form,CourseRecord_form,StudentRecord_form
from utils.pagination import Pagination
from django.db.models import Q, F
from django.views import View
from utils.pagination import Pagination
from django.db import transaction
from django.conf import global_settings,settings
from django.forms import modelformset_factory
import hashlib


def login_judge(func):
    def inner(requset, *args, **kwargs):
        is_login = requset.session.get('is_login')
        url = requset.path_info
        print(url)
        if not is_login:
            return redirect('/crm/login/?return_url={}'.format(url))
        ret = func(requset, *args, **kwargs)
        return ret

    return inner


# 首页

def index(request):
    return render(request, 'index.html')


# 登录
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        md5 = hashlib.md5()
        md5.update(password.encode('utf-8'))
        obj = models.UserProfile.objects.filter(username=username, password=md5.hexdigest(), is_active=True).first()
        if obj:
            request.session['is_login'] = True
            request.session['user_id'] = obj.pk
            return redirect(reverse('own_customer'))
        else:
            return render(request, 'login.html', {'error': '用户名密码错误！'})
    return render(request, 'login.html')


# 注册
def register(request):
    form_obj = Register_form()
    if request.method == 'POST':
        form_obj = Register_form(request.POST)
        # 对提交的数据进行校验
        if form_obj.is_valid():
            # 校验成功 把数据插入数据库中
            # models.UserProfile.objects.create(*form_obj.cleaned_data)
            form_obj.save()
            return redirect(reverse('login'))
        print(form_obj.errors)
    return render(request, 'register.html', {'form_obj': form_obj})


# CBV实现公共客户、私有客户信息展示、公私客户转换、模糊匹配
class CustomerList(View):
    def get(self,request,*args,**kwargs):
        # print(request.GET,type(request.GET))
        # print(request.GET.urlencode())
        # request.GET._mutable = True # 可编辑
        # request.GET['page'] = 1
        # print(request.GET.urlencode())

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
        pks = self.request.POST.getlist('pk')

        if models.Customer.objects.filter(consultant=self.request.user_obj).count() + len(pks) > settings.MAX_CUSTOMER_NUM:
            return HttpResponse('做人不能太贪心')
        try:
            with transaction.atomic():
                queryset = models.Customer.objects.filter(pk__in=pks,consultant=None).select_for_update()
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


def search(request,field_list):
    # 构建Q对象
    # q = Q(qq__contains=query)|Q(name__contains=query)|Q(phone__contains=query),

    query = request.GET.get('query','')
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
        q = search(self.request,['date'])
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
            print(111111)
            form_obj.save()
            print(22222)
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
    def get(self,request,*args,customer_id=None,**kwargs):
        # 展示一个销售的报名记录表
        if not customer_id:
            all_enrollment = models.Enrollment.objects.filter(customer__in=request.user_obj.customers.all(),delete_status=False)
        # 展示一个客户的报名记录表
        else:
            all_enrollment = models.Enrollment.objects.filter(customer_id=customer_id,delete_status=False)
        return render(request, 'consultant/enrollment_list.html', {'all_enrollment': all_enrollment.order_by('-enrolled_date'), })

def enrollment_change(reqeust,pk=None,customer_id=None):
    # obj = models.Enrollment.objects.filter(pk=pk).first()
    obj = models.Enrollment(customer_id=customer_id) if customer_id else models.Enrollment.objects.filter(pk=pk).first()
    form_obj = Enrollment_form(reqeust,instance=obj)
    if reqeust.method == 'POST':
        form_obj = Enrollment_form(reqeust,data=reqeust.POST,instance=obj)
        if form_obj.is_valid():
            form_obj.save()
            return redirect(reverse('enrollment_list'))
    title = '编辑客户' if pk else '添加客户'
    return render(reqeust, 'form.html', {'form_obj':form_obj, 'title':title})


# 班级表
class Classlist(View):
    def get(self,request,*args,**kwargs):
        all_class = models.ClassList.objects.all()
        return render(request, 'teacher/class_list.html', {'all_class':all_class})

def class_change(request,pk=None):
    obj = models.ClassList.objects.filter(pk=pk).first()
    form_obj = Class_form(instance=obj)
    if request.method == 'POST':
        form_obj = Class_form(data=request.POST,instance=obj)
        if form_obj.is_valid():
            form_obj.save()
            return redirect(reverse('class_list'))
    title = '编辑班级' if pk else '添加班级'
    return render(request,'form.html',{'form_obj':form_obj,'title':title})


# 课程记录表
class CourseRecordlist(View):
    def get(self,request,*args,**kwargs):
        all_course_record = models.CourseRecord.objects.all()
        return render(request, 'teacher/course_record_list.html', {'all_course_record':all_course_record})
    # 批量创建学习记录
    def multi_init(self):
        # 课程记录的id
        course_record_ids = self.request.POST.getlist('pk')
        course_records = models.CourseRecord.objects.filter(pk__in=course_record_ids)
        for course_record in course_records:
            students = course_record.re_class.customer_set.all().filter(status='studying')
            # 一条一条数据的插入
            # for student in students:
            #     models.StudyRecord.objects.create(course_record=course_record,student=student)

            # 批量插入
            study_record_list = []
            for student in students:
                study_record_list.append(models.StudyRecord(course_record=course_record, student=student))
            models.StudyRecord.objects.bulk_create(study_record_list)

def course_record_change(request,pk=None):
    obj = models.CourseRecord.objects.filter(pk=pk).first()
    form_obj = CourseRecord_form(instance=obj)
    if request.method == 'POST':
        form_obj = CourseRecord_form(data=request.POST,instance=obj)
        if form_obj.is_valid():
            form_obj.save()
            return redirect(reverse('course_record_list'))
    title = '编辑课程记录' if pk else '添加课程记录'
    return render(request,'form.html',{'form_obj':form_obj,'title':title})



# 学习记录表

def study_record_list(request,course_record_id):
    ModelFormSet = modelformset_factory(models.StudyRecord,StudentRecord_form,extra=0)
    form_set_obj = ModelFormSet(queryset=models.StudyRecord.objects.filter(course_record_id=course_record_id))
    if request.method == 'POST':
        form_set_obj = ModelFormSet(queryset=models.StudyRecord.objects.filter(course_record_id=course_record_id),data=request.POST)
        if form_set_obj.is_valid():
            form_set_obj.save()
            next = request.GET.get('next')
            if next:
                return redirect(next)
            return redirect(reverse())
    return render(request,'')




class StudyRecordlist(View):
    def get(self,request,*args,**kwargs):
        all_study_record = models.StudyRecord.objects.all()
        return render(request, 'teacher/study_record_list.html', {'all_study_record':all_study_record})

def study_record_change(request,pk=None):
    obj = models.StudyRecord.objects.filter(pk=pk).first()
    form_obj = StudentRecord_form(instance=obj)
    if request.method == 'POST':
        form_obj = StudentRecord_form(data=request.POST,instance=obj)
        if form_obj.is_valid():
            form_obj.save()
            return redirect(reverse('study_record_list'))
    title = '编辑学习记录' if pk else '添加学习记录'
    return render(request,'form.html',{'form_obj':form_obj,'title':title})














# 用户表分页
user = [{'user': 'alex-{}'.format(i, ), 'pwd': '123'} for i in range(1, 921)]


def user_list(request):
    page = Pagination(request.GET.get('page', 1), len(user))
    return render(request, 'user_list.html', {'user': user[page.start_num:page.end_num], 'page_html': page.page_html})





# 自己实现的功能

# FBV实现
def customer_list(request):
    # get请求
    if request.path_info == reverse('customer_list'):
        all_customer = models.Customer.objects.filter(consultant__isnull=True)
        models.Customer.objects.filter()
        title = '添加到我的客户'

    else:
        all_customer = models.Customer.objects.filter(consultant_id=request.session.get('user_id'))
        title = '变为公共用户'
    # post请求
    if request.method == "POST":
        options = request.POST.get('options')
        obj_pk = request.POST.getlist('obj')
        search = request.POST.get('search')
        # 模糊匹配查询
        if request.path_info == reverse('own_customer'):
            all_customer = models.Customer.objects.filter(Q(consultant_id=request.session.get('user_id'))&Q(Q(qq__contains=search) | Q(name__contains=search) | Q(phone__contains=search)))
        else:
            all_customer = models.Customer.objects.filter(Q(consultant=None)&Q(Q(qq__contains=search) | Q(name__contains=search) | Q(phone__contains=search)))
        page = Pagination(request.GET.get('page',1),all_customer.count(),2)
        # 公户转私户、私户转公户
        if obj_pk:
            for i in obj_pk:
                obj = models.Customer.objects.filter(pk=i).first()

                if options == '添加到我的客户':
                    obj.consultant_id = request.session.get('user_id')
                    obj.save()
                    ret = reverse('customer_list')

                else:
                    obj.consultant_id = None
                    obj.save()
                    ret = reverse('own_customer')
            else:
                return redirect(ret)

    return render(request, 'consultant/customer_list.html', {'all_customer': all_customer, 'title': title})


# 公私户转换
def pub_pri_change(request, pk):
    obj = models.Customer.objects.filter(pk=pk).first()
    if obj.consultant_id:
        obj.consultant_id = None
        obj.save()
        ret = reverse('own_customer')
    else:

        obj.consultant_id = request.session.get('user_id')
        obj.save()
        ret = reverse('customer_list')
    return redirect(ret)


# 登陆成功展示自己的客户
def own_customer(request):
    user_id = request.session.get('user_id')
    print(user_id)
    customers = models.Customer.objects.filter(consultant_id=user_id)
    return render(request, 'consultant/own_customer_list.html', {'customers': customers})


# 添加客户信息
def add_customer(requsest):
    form_obj = Customer_form()
    if requsest.method == 'POST':
        form_obj = Customer_form(requsest.POST)
        if form_obj.is_valid():
            form_obj.save()
            return redirect(reverse('customer_list'))
        print(form_obj.errors)
    return render(requsest, 'consultant/add_customer.html', {'form_obj': form_obj})


# 编辑客户信息
def edit_customer(request, pk):
    obj = models.Customer.objects.filter(pk=pk).first()
    form_obj = Customer_form(instance=obj)  # 实例  对象 拿到对应对象的原始数据，此时form_obj包含了原始数据
    if request.method == 'POST':
        form_obj = Customer_form(data=request.POST, instance=obj)
        if form_obj.is_valid():
            form_obj.save()
            return redirect(reverse('own_customer'))
    return render(request, 'customer_form.html', {'form_obj': form_obj})
# 分页展示用户信息
# FBV分页展示用户表
def user_list(request):
    user = [{'user':'alex-{}'.format(i,),'pwd':'123'}for i in range(1,921)]
    # 进行异常处理，如果在地址上输入page=0或<0,让page赋值为0，或者当获取不到page，
    # 或者page中有字符串或其他内容而无法执行的时候进行抛出异常，并将page赋值为1
    try:
        page = int(request.GET.get('page'))
        if page <= 0:
            page = 1
    except Exception:
        page = 1
    # 总数据数all_count
    all_count = len(user)
    # 每页显示的数据量
    per_page = 15
    # 总的页码数total_num
    total_num,rest = divmod(all_count,per_page)
    if rest:
        total_num += 1
    # 每页要显示的页码数max_show
    max_show = 15
    half_show = max_show//2
    # 如果总的页码数比每一页显示的页码数还要小，那么给page最小值为1，最大值为总的页码数
    if total_num <= max_show:
        page_start = 1
        page_end = total_num
    # 或者总的页码数比每一页显示的页码数要大，这时需要分为三种情况来考虑
    else:
        # 第一种情况为页码的左侧，即用户选择的页码数比每一页的页码数的一半还小，那么
        # 就不能继续做page - half_show，这时就需要给page_start赋最小值1
        if page - half_show <= 0:
            page_start = 1
            page_end = max_show
        # 第二种情况为页码的右侧，即用户选择的页码数加上每一页页码数的一半还大，那么
        # 就不能继续做page + half_show，这时需要给page_end赋最大值，即总页码数，page_start
        # 就可以用总页码数减去每页要显示的页码数+1来实现
        elif page + half_show > total_num:
            page_end = total_num
            page_start = total_num - max_show + 1
        # 第三种情况为正常，没有出现在范围之外的情况
        else:
            # 页码的起始值
            page_start = page - half_show
            # 页码的终止值
            page_end = page + half_show
    # 将分页展示做在后端
    # 对生成的li标签做一个空的列表
    li_list = []
    # 完成上一页，如果到了第一页，那么对上一页的按钮设置禁用class="disabled"
    if page == 1:
        li_list.append(
            '<li class="disabled"><a href="?page={}" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a></li>'.format(
                page - 1, ))
    else:
        li_list.append('<li><a href="?page={}" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a></li>'.format(page-1,))
    # 完成中间的页码显示，并设置客户选择哪一个就设置激活状态class="active"
    for i in range(page_start,page_end + 1):
        if i == page:
            li_list.append('<li class="active"><a href="?page={}">{}</a></li>'.format(i, i))
        else:
            li_list.append( '<li><a href="?page={}">{}</a></li>'.format(i,i))
    # 完成下一页，如果到了最后一页，那么对下一页的按钮设置禁用class="disabled"
    if page == total_num:
        li_list.append(
            '<li class="disabled"><a href="?page={}" aria-label="Next"><span aria-hidden="true">&raquo;</span></a></li>'.format(
                page + 1, ))
    else:
        li_list.append('<li><a href="?page={}" aria-label="Next"><span aria-hidden="true">&raquo;</span></a></li>'.format(page+1,))
    page_html = ''.join(li_list)
    start_num = (page-1)*per_page
    end_num = page*per_page
    return render(request, 'user_list.html', {'user': user[start_num:end_num], 'page_html':page_html})
