from django.shortcuts import render, redirect, reverse,HttpResponse
from crm import models
from .base import BaseView
from crm.forms import Class_form,CourseRecord_form,StudentRecord_form
from utils.pagination import Pagination
from django.forms import modelformset_factory
from django.views import View


# 班级表
class Classlist(BaseView):
    def get(self,request,*args,**kwargs):
        q = self.search(['campuses__name','start_date'])
        all_class = models.ClassList.objects.filter(q)
        page = Pagination(request.GET.get('page',1),all_class.count(),request.GET.copy(),3)
        return render(request, 'teacher/class_list.html', {'all_class': all_class[page.start_num:page.end_num], 'page_html':page.page_html})

def class_change(request,pk=None):
    obj = models.ClassList.objects.filter(pk=pk).first()
    form_obj = Class_form(instance=obj)
    if request.method == 'POST':
        form_obj = Class_form(data=request.POST,instance=obj)
        if form_obj.is_valid():
            form_obj.save()
            next = request.GET.get('next')
            if next:
                return redirect(next)
            return redirect(reverse('class_list'))
    title = '编辑班级' if pk else '添加班级'
    return render(request,'form.html',{'form_obj':form_obj,'title':title})


# 课程记录表
class CourseRecordlist(BaseView):
    def get(self,request,*args,class_id,**kwargs):
        all_course_record = models.CourseRecord.objects.filter(re_class=class_id)
        page = Pagination(request.GET.get('page',1),all_course_record.count(),request.GET.copy(),3)
        return render(request, 'teacher/course_record_list.html', {'all_course_record':all_course_record[page.start_num:page.end_num],'page_html':page.page_html,'class_id':class_id})

    # 批量创建学习记录
    def multi_init(self):
        # 课程记录的id
        course_record_ids = self.request.POST.getlist('pk')
        print('course_record_ids',course_record_ids)
        # 找到对应的课程记录们
        course_records = models.CourseRecord.objects.filter(pk__in=course_record_ids)
        # 循环拿出每一个课程记录对象
        for course_record in course_records:
            # 查找学生：通过课程记录对象拿到班级对象，在通过班级对象反向查询找到所有的客户，在通过学习状态这个条件进行筛选，筛选出对应在学习中的学生
            students = course_record.re_class.customer_set.all().filter(status='studying')
            print('students',students)
            # 方式一：一条一条的插入数据，效率低
            # for student in students:
            #     models.StudyRecord.objects.create(course_record=course_record,student=student)

            # 方式二：将要生成的每个学生的学习记录放在一个列表中，添加完成之后，一起添加
            study_record_list = []
            for student in students:
                study_record_list.append(models.StudyRecord(course_record=course_record,student=student))
            print('study_record_list',study_record_list)
            models.StudyRecord.objects.bulk_create(study_record_list)

def course_record_change(request,pk=None,class_id=None):
    obj = models.CourseRecord(re_class_id=class_id,recorder=request.user_obj) if class_id else models.CourseRecord.objects.filter(pk=pk).first()
    form_obj = CourseRecord_form(instance=obj)
    if request.method == 'POST':
        form_obj = CourseRecord_form(data=request.POST,instance=obj)
        if form_obj.is_valid():
            form_obj.save()
            next = request.GET.get('next')
            if next:
                return redirect(next)
            return redirect(reverse('course_record_list',args=(class_id,)))
    title = '编辑课程记录' if pk else '添加课程记录'
    return render(request,'form.html',{'form_obj':form_obj,'title':title})

# 学习记录表
def study_record_list(request,course_record_id):
    # 把ModelFormSet看成一个类，第一个参数是数据库对应的类（表）：models.StudyRecord，第二个参数是modelform：StudentRecord_form，extra设置为0，就不会再数据为空的时候在生成一条额外的数据
    ModelFormSet = modelformset_factory(models.StudyRecord,StudentRecord_form,extra=0)
    # 通过课程记录的id来筛选出所有的学习记录的queryset列表，并把该列表传进ModelFormSet，得到form_set_obj对象
    form_set_obj = ModelFormSet(queryset=models.StudyRecord.objects.filter(course_record_id=course_record_id))
    if request.method == 'POST':
        # 除了将通过课程记录的id来筛选出所有的学习记录的queryset列表传进去，还需要将新编辑后的数据也要穿进去
        form_set_obj = ModelFormSet(queryset=models.StudyRecord.objects.filter(course_record_id=course_record_id),data=request.POST)
        if form_set_obj.is_valid():
            form_set_obj.save()
            next = request.GET.get('next')
            if next:
                return redirect(next)
            return redirect(reverse('study_record',args=(course_record_id,)))
    return render(request,'teacher/study_record_list.html',{'form_set_obj':form_set_obj})