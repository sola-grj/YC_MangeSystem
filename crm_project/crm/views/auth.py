from django.shortcuts import render, redirect, reverse,HttpResponse
from crm import models
from crm.forms import Register_form, Customer_form,Consult_form,Enrollment_form,Class_form,CourseRecord_form,StudentRecord_form
import hashlib
from rbac.service.init_permission import init_permission

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
            init_permission(request,obj)
            request.session['is_login'] = True
            request.session['user_id'] = obj.pk
            return redirect(reverse('index'))
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