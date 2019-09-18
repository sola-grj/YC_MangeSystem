from django import forms
from crm import models
import hashlib
from django.core.exceptions import ValidationError
from multiselectfield.forms.fields import MultiSelectFormField
from django.forms.fields import BooleanField


class BootStrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field, (MultiSelectFormField, BooleanField)):
                continue
            field.widget.attrs['class'] = 'form-control'


# 用户登录注册表
class Register_form(forms.ModelForm):
    # 当在此重新写表中有的字段，那将会覆盖原有的表中的字段
    password = forms.CharField(min_length=6,widget=forms.PasswordInput(attrs={'placeholder':'请输入您的密码','autocomplete': 'off'}))
    # 新增字段在Meta类上面写
    re_password = forms.CharField(min_length=6,widget=forms.PasswordInput(attrs={'placeholder':'请再次输入您的密码','autocomplete': 'off'}))

    class Meta:
        model = models.UserProfile
        exclude = ['is_active']
        fields = '__all__'
        widgets = {
            'username':forms.EmailInput(attrs={'placeholder':'请输入您的用户名','autocomplete':'off',}),
            'mobile':forms.TextInput(attrs={'placeholder':'请输入您的手机号码','autocomplete':'off',}),
            'name':forms.TextInput(attrs={'placeholder':'请输入您的真实姓名','autocomplete':'off',})
        }
        error_messages = {
            'username':{
                'required':'用户名是必填项！',
                'invalid':'邮箱格式不正确！'
            }
        }
    def clean(self):
        self._validate_unique = True
        password = self.cleaned_data.get('password','')
        re_password = self.cleaned_data.get('re_password','')
        # if not password  :
        #     self.add_error('password','输入密码不能为空')
        #     raise ValidationError('输入密码不能为空！！')
        if password == re_password:
            # 对密码进行校验
            md5 = hashlib.md5()
            md5.update(password.encode('utf-8'))
            self.cleaned_data['password'] = md5.hexdigest()
            return self.cleaned_data

        else:
            self.add_error('re_password','两次密码不一致')
            raise ValidationError('两次密码不一致')

# 客户信息表
class Customer_form(BootStrapModelForm):

    class Meta:
        model = models.Customer
        fields = '__all__'
        widgets = {
            'birthday':forms.TextInput(attrs={'type':'date'}),
            'next_date':forms.TextInput(attrs={'type':'date'}),

        }
    # def __init__(self,*args,**kwargs):
    #     super().__init__(*args,**kwargs)
    #     for field in self.fields.values():
    #         if isinstance(field,MultiSelectFormField):
    #             continue
    #         field.widget.attrs['class'] = 'form-control'

# 跟进记录表
class Consult_form(BootStrapModelForm):
    class Meta:
        model = models.ConsultRecord
        fields = '__all__'
        widgets = {

        }
    def __init__(self,request,customer_id,*args,**kwargs):
        super().__init__(*args,**kwargs)
        # 限制咨询客户为当前的销售私户
        if customer_id and customer_id !='0':
            self.fields['customer'].choices = [(i.pk,str(i)) for i in models.Customer.objects.filter(pk=customer_id)]
        else:

            self.fields['customer'].choices = [('','---------'),] + [(i.pk,str(i)) for i in request.user_obj.customers.all()]

        # 限制跟进人为当前销售
        self.fields['consultant'].choices = [(request.user_obj.pk,request.user_obj),]


# 报名记录表
class Enrollment_form(BootStrapModelForm):
    class Meta:
        model = models.Enrollment
        fields = '__all__'

    def __init__(self,request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['customer'].choices = [('','---------'),] + [(i.pk,str(i)) for i in request.user_obj.customers.all()]
        # self.fields['enrolment_class'].choices = [(i.pk,str(i)) for i in request.user_obj.]
        if self.instance.customer_id and self.instance.customer_id != '0':
            # print(request.user_obj.customers.all())
            # print(self.instance.customer_id)
            self.fields['customer'].choices = [(self.instance.customer.pk,self.instance.customer)]
            self.fields['enrolment_class'].choices = [(i.pk,str(i)) for i in self.instance.customer.class_list.all()]

        if self.instance.customer_id == '0':

            self.fields['customer'].choices =  [('','---------'),] + [(i.pk,str(i)) for i in request.user_obj.customers.all()]
        # print(self.instance.customer_id)

#缴费记录表
class PaymentRecord_form(BootStrapModelForm):
    class Meta:
        model = models.PaymentRecord
        fields = '__all__'
        widgets = {
            'date':forms.TextInput(attrs={'type':'date'})
        }
    def __init__(self,request,*args,**kwargs):

        super().__init__(*args,**kwargs)
        if self.instance.customer_id and self.instance.customer_id != '0':
            self.fields['customer'].choices = [(self.instance.customer.pk,self.instance.customer)]
            self.fields['consultant'].choices = [(self.instance.consultant.pk,self.instance.consultant)]
        if self.instance.customer_id == '0':

            self.fields['customer'].choices =  [('','---------'),] + [(i.pk,str(i)) for i in request.user_obj.customers.all()]



# 班级表
class Class_form(BootStrapModelForm):
    class Meta:
        model = models.ClassList
        fields = '__all__'
        widgets={
            'start_date':forms.TextInput(attrs={'type':'date'}),
            'graduate_date':forms.TextInput(attrs={'type':'date'}),
        }


# 课程记录表
class CourseRecord_form(BootStrapModelForm):
    class Meta:
        model = models.CourseRecord
        fields = '__all__'
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        # 限制班级为当前的班级
        self.fields['re_class'].choices = [(self.instance.re_class_id,self.instance.re_class)]
        print(self.fields['re_class'].choices)

        # 限制记录者为当前的用户
        self.fields['recorder'].choices = [(self.instance.recorder_id,self.instance.recorder)]

        # 限制讲师为当前的班级讲师
        self.fields['teacher'].choices = [(i.pk,str(i)) for i in self.instance.re_class.teachers.all()]

# 学习记录表
class StudentRecord_form(BootStrapModelForm):
    class Meta:
        model = models.StudyRecord
        fields = '__all__'