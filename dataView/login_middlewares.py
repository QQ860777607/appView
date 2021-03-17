from django.shortcuts import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin
import re


# 自定义中间件类
class Login(MiddlewareMixin):

    def process_request(self, request):
        # 获取session内用户的登录标识
        key = request.session.get('key', 0)
        # 判断用户是否登录，访问路径是不是登录页面
        print(key, request.path)
        # if request.META.get('HTTP_X_FORWARDED_FOR'):
        #     ip = request.META.get("HTTP_X_FORWARDED_FOR")
        # else:
        #     ip = request.META.get("REMOTE_ADDR")
        if re.search(r'/appEV/api/([^/]+)$', request.path) is not None:
            pass
        elif key == 0 and request.path != '/dataView/':
            return HttpResponseRedirect('/dataView/')