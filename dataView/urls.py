from django.urls import path, re_path
from . import views
from rest_framework.routers import DefaultRouter


urlpatterns = [
    path('', views.login, name='login'),
    path('menuEdit/', views.menu_edit),                         # 菜单管理
    path('eFlowChart/', views.e_flowchart),                     # 流程图
    path('scrollBar/', views.scrollbar),                        # 流动条
    path('ImportData/', views.import_data),                     # 数据导入
    re_path(r'menu_info/', views.menu_info),
    re_path(r'iconList/', views.icon_list),
    path('main_page/', views.main_page),
    re_path(r'dep_add_post/([^/]+)$', views.dep_add_post),      # 部门添加角色
    re_path(r'dep_add_user/([^/]+)$', views.dep_add_user),      # 部门添加用户
    path('structure/', views.structure),                        # 组织构架
    re_path(r'accountManagement/', views.account_management),   # 用户管理
    re_path(r'roleInfo/', views.role_info),                     # 角色管理
    path('userRegEdit/', views.user_reg_edit),                  # 用户注册
    re_path(r'userEdit/([^/]+)$', views.user_edit),             # 用户编辑
    re_path(r'department/([^/]+)$', views.department),          # 二级部门
    re_path(r'author/', views.author),                          # 二级部门
    re_path(r'roleSelect/([^/]+)$', views.role_select),                 # 人员角色：用户管理->



]

