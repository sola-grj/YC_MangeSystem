from django.conf.urls import url
from crm.views import auth,consultant,teacher

urlpatterns = [
    url(r'^login/', auth.login,name='login'),
    url(r'^index/', auth.index,name='index'),
    url(r'^register/', auth.register,name='register'),

    # fbv
    # url(r'^customer_list/', views.customer_list,name='customer_list'),
    # url(r'^own_customer/', views.customer_list,name='own_customer'),

    # cbv
    url(r'^customer_list/', consultant.CustomerList.as_view(),name='customer_list'),
    url(r'^own_customer/', consultant.CustomerList.as_view(),name='own_customer'),

    # url(r'^pub_pri_change/(\d+)', views.pub_pri_change,name='pub_pri_change'),
    url(r'^add_customer/', consultant.customer_change,name='add_customer'),
    url(r'^edit_customer/(\d+)', consultant.customer_change,name='edit_customer'),
    # url(r'^user_list/', consultant.user_list,name='user_list'),

    # 跟进记录
    # CBV
    # 显示一个销售对应的所有的跟进记录表
    url(r'^consult_list/$', consultant.ConsultList.as_view(),name='consult_list'),
    # 在我的客户中显示某一个客户的所有的跟进记录表，因此需要当前的客户的id
    url(r'^consult_list/(\d+)/$', consultant.ConsultList.as_view(),name='show_consult'),
    #
    url(r'^add_consult/(?P<customer_id>\d+)/$', consultant.consult_change,name='add_consult'),
    url(r'^edit_consult/(\d+)', consultant.consult_change,name='edit_consult'),
    # FBV
    # url(r'^consult_list/', views.consult_list,name='consult_list'),
    # url(r'^add_consult/', views.consult_change,name='add_consult'),
    # url(r'^edit_consult/(\d+)', views.consult_change,name='edit_consult'),
    # url(r'^show_consult/(\d+)', views.show_consult,name='show_consult'),

    # 报名记录
    # 展示一个销售填写的报名记录
    url(r'^enrollment_list/$', consultant.EnrollmentList.as_view(),name='enrollment_list'),
    # 展示一个客户填写的报名记录
    url(r'^enrollment_list/(?P<customer_id>\d+)/$', consultant.EnrollmentList.as_view(),name='show_enrollment'),
    # 添加报名表
    url(r'^add_enrollment/(?P<customer_id>\d+)$', consultant.enrollment_change, name='add_enrollment'),
    # 编辑报名表
    url(r'^edit_enrollment/(\d+)/$', consultant.enrollment_change, name='edit_enrollment'),
    # FBV
    # url(r'^enrollment_list/', views.enrollment_list,name='enrollment_list'),
    # url(r'^add_enrollment/', views.enrollment_change,name='add_enrollment'),
    # url(r'^edit_enrollment/(\d+)', views.enrollment_change,name='edit_enrollment'),


    # 缴费记录表
    # 查看一个销售的所有缴费记录表
    url(r'^payment_record_list/$', consultant.PaymentRecordlist.as_view(), name='payment_record_list'),
    # 查看一个 客户填写的缴费记录表
    url(r'^payment_record_list/(?P<customer_id>\d+)/$', consultant.PaymentRecordlist.as_view(), name='show_payment'),
    # 添加缴费记录表
    url(r'^add_payment_record/(?P<customer_id>\d+)/$', consultant.payment_record_change, name='add_payment_record'),
    # 编辑缴费记录
    url(r'^edit_payment_record/(\d+)', consultant.payment_record_change, name='edit_payment_record'),




    # 班级表
    url(r'^class_list/', teacher.Classlist.as_view(), name='class_list'),
    url(r'^add_class/', teacher.class_change, name='add_class'),
    url(r'^edit_class/(\d+)', teacher.class_change, name='edit_class'),

    # 课程记录表
    url(r'^course_record_list/(?P<class_id>\d+)$', teacher.CourseRecordlist.as_view(), name='course_record_list'),
    url(r'^add_course_record/(?P<class_id>\d+)$', teacher.course_record_change, name='add_course_record'),
    url(r'^edit_course_record/(?P<pk>\d+)$', teacher.course_record_change, name='edit_course_record'),

    # 学习记录表
    url(r'^study_record/(?P<course_record_id>\d+)$', teacher.study_record_list, name='study_record'),

    # url(r'^study_record_list/', teacher.StudyRecordlist.as_view(), name='study_record_list'),
    # url(r'^add_study_record/', teacher.study_record_change, name='add_study_record'),
    # url(r'^edit_study_record/(\d+)', teacher.study_record_change, name='edit_study_record'),

]
