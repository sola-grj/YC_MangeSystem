from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect,reverse
from crm import models
class AuthMiddleware(MiddlewareMixin):
    def process_request(self,request):
        # if request.path_info in [reverse('login'),reverse('register')]:
        #     return None
        # if request.path_info.startswith('/admin'):
        #     return None
        # if not request.session.get('is_login'):
        #     return redirect(reverse('login'))
        # 登录成功 保存登录的用户对象
        obj = models.UserProfile.objects.filter(pk=request.session.get('user_id')).first()
        if obj:
            request.user_obj = obj