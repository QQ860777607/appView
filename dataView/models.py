from django.db import models
from django.contrib.auth.hashers import make_password
import uuid


# 系统菜单表
class SystemMenu(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    pid = models.IntegerField(verbose_name='父ID', default=0)
    title = models.CharField(max_length=100, verbose_name='名称', null=False)
    icon = models.CharField(max_length=100, verbose_name='菜单图标', default='')
    href = models.CharField(max_length=100, verbose_name='链接', default='')
    target = models.CharField(max_length=20, verbose_name='名称', default='_self')
    sort = models.IntegerField(verbose_name='菜单排序', default=0)
    status_choices = ((1, '启用'), (0, '禁用'))
    status = models.IntegerField(choices=status_choices, verbose_name='状态', default=1)
    remark = models.CharField(max_length=255, verbose_name='备注信息', null=True)
    is_sys_menu = models.IntegerField(verbose_name='缺省菜单', default=0)
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', null=True)
    update_at = models.DateTimeField(auto_now=True, verbose_name='更新时间', null=True)
    delete_at = models.DateTimeField(auto_now=True, verbose_name='删除时间', null=True)


# 公司表设计
class CompanyInfo(models.Model):
    id = models.UUIDField(primary_key=True, auto_created=True, default=uuid.uuid1, editable=False)
    companyName = models.CharField(max_length=60, help_text='输入公司名称')
    ctime = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', null=True)
    uptime = models.DateTimeField(auto_now=True, verbose_name='更新时间', null=True)


# 部门表设计
class Department(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='部门ID')
    department = models.CharField(max_length=20, verbose_name='部门名称', help_text='输入部门名称')
    companyInfo_id = models.ForeignKey("CompanyInfo", verbose_name='所属公司', to_field='id', null=True, blank=True, on_delete=models.CASCADE)
    description = models.CharField(max_length=200, verbose_name='备注')
    creationType_choices = ((1, '1'), (2, '2'), (0, '0'))
    creationType = models.IntegerField(choices=creationType_choices, verbose_name='创建类型', default=1)
    lastOperationType_choices = ((1, '1'), (2, '2'), (0, '0'))
    lastOperationType = models.IntegerField(choices=lastOperationType_choices, verbose_name='上次操作类型', default=1)
    enable = models.BooleanField(default=False)  # 部门是否可见
    fullPath = models.CharField(max_length=1000, verbose_name='目录起止汇总id')
    parentId = models.CharField(max_length=200, verbose_name='上一级目录id')
    sortIndex = models.IntegerField(verbose_name='目录排序', default=0)
    ctime = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', null=True)
    uptime = models.DateTimeField(auto_now=True, verbose_name='更新时间', null=True)


# 职务表设计
class UserPost(models.Model):
    id = models.UUIDField(primary_key=True, auto_created=True, default=uuid.uuid1, editable=False, verbose_name='职务ID')
    alias = models.CharField(max_length=255, verbose_name='别名')
    creationType_choices = ((1, '1'), (2, '2'), (0, '0'))
    creationType = models.IntegerField(choices=creationType_choices, verbose_name='创建类型', default=1)
    status = models.BooleanField(default=False)
    lastOperationType_choices = ((1, '1'), (2, '2'), (0, '0'))
    lastOperationType = models.IntegerField(choices=lastOperationType_choices, verbose_name='上次操作类型', default=1)
    description = models.CharField(max_length=200, verbose_name='备注')
    name = models.CharField(max_length=255, verbose_name='职务名称')


# 部门_职务_关联表
class DepartmentPost(models.Model):
    id = models.UUIDField(primary_key=True, auto_created=True, default=uuid.uuid1, editable=False)
    department = models.ForeignKey("Department", verbose_name='所属部门', to_field='id', null=True, blank=True,
                                   on_delete=models.CASCADE)
    post = models.ForeignKey("UserPost", verbose_name='职务名称', to_field='id', null=True, blank=True,
                             on_delete=models.CASCADE)
    creationType_choices = ((1, '1'), (2, '2'), (0, '0'))
    creationType = models.IntegerField(choices=creationType_choices, verbose_name='创建类型', default=1)
    lastOperationType_choices = ((1, '1'), (2, '2'), (0, '0'))
    lastOperationType = models.IntegerField(choices=lastOperationType_choices, verbose_name='上次操作类型', default=1)
    sortIndex = models.IntegerField(verbose_name='职务排序', default=0)
    ctime = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', null=True)
    uptime = models.DateTimeField(auto_now=True, verbose_name='更新时间', null=True)

    class Meta:
        indexes = [
            models.Index(fields=['department', 'post', 'ctime'], name='Dep_Post_idx', ),
        ]


# 角色表设计
class Role(models.Model):
    id = models.UUIDField(primary_key=True, auto_created=True, default=uuid.uuid1, editable=False)
    sortIndex = models.IntegerField(verbose_name='菜单排序', default=0)
    roleName = models.CharField(max_length=50, verbose_name='角色名称')
    remark = models.CharField(max_length=255, verbose_name='备注')


# 人员表设计
class UserInfo(models.Model):
    id = models.UUIDField(primary_key=True, auto_created=True, default=uuid.uuid1, editable=False)
    alias = models.CharField(max_length=255, verbose_name='别名')
    userName = models.CharField(max_length=32, verbose_name='账号')
    realName = models.CharField(max_length=32, verbose_name='用户名')
    uRole = models.ManyToManyField("Role")
    userPhone = models.CharField(max_length=32, verbose_name='用户手机')
    userMail = models.CharField(max_length=32, verbose_name='用户邮箱')
    password = models.CharField(max_length=120, verbose_name='用户密码', help_text='输入密码')
    user_status_choices = ((1, '正常'), (0, '冻结'))
    status = models.IntegerField(choices=user_status_choices, verbose_name='用户状态', default=1)
    user_type_choices = ((0, '超级管理员'), (1, '管理人员'), (2, '录入人员'), (3, '普通用户'))
    user_type = models.IntegerField(choices=user_type_choices, verbose_name='用户权限', default=3)
    creationType_choices = ((1, '后台添加'), (2, 'APP注册'))
    creationType = models.IntegerField(verbose_name='创建类型', default=1)
    lastOperationType_choices = ((1, '首建'), (2, '冻结'), (0, '修改'))
    lastOperationType = models.IntegerField(choices=lastOperationType_choices, verbose_name='上次操作类型', default=1)
    description = models.CharField(max_length=1000, verbose_name='备注')
    uBDate = models.DateTimeField(verbose_name='生日', null=True)
    uDate = models.DateTimeField(verbose_name='入职时间', null=True)
    uSex_choices = ((1, '男'), (2, '女'))
    uSex = models.IntegerField(choices=uSex_choices, verbose_name='性别', default=1)
    identity = models.CharField(max_length=20, verbose_name='身份证号')
    uCollege_choices = ((1, '文盲'), (2, '小学'), (3, '初中'), (4, '高中'), (5, '职高'), (6, '中专'), (7, '大专'), (8, '本科'),
                        (9, '硕士'), (10, '博士'))
    uCollege = models.IntegerField(choices=uCollege_choices, verbose_name='学历', default=7)
    uHobbies = models.CharField(max_length=100, verbose_name='个人爱好')
    uPhotos = models.TextField(verbose_name='用户照片', null=True)
    uProvince = models.CharField(max_length=100, verbose_name='省级')
    uCity = models.CharField(max_length=100, verbose_name='市级')
    uCounty = models.CharField(max_length=100, verbose_name='区县')
    uStreet = models.CharField(max_length=100, verbose_name='街道门牌')
    ctime = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', null=True)
    uptime = models.DateTimeField(auto_now=True, verbose_name='更新时间', null=True)

    def save(self, *args, **kwargs):
        self.password = make_password(self.password, None, 'pbkdf2_sha256')
        super(UserInfo, self).save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['userPhone', 'userName', 'userMail', 'ctime'], name='user_idx', ),
        ]


# 角色权限表设计
class Author(models.Model):
    id = models.UUIDField(primary_key=True, auto_created=True, default=uuid.uuid1, editable=False)
    role = models.ForeignKey("Role", verbose_name='角色信息', to_field='id', null=True, blank=True,
                             on_delete=models.CASCADE)
    menu = models.ForeignKey("SystemMenu", verbose_name='系统目录', to_field='id', null=True, blank=True,
                             on_delete=models.CASCADE)
    is_query = models.IntegerField(verbose_name='查询', default=0)
    is_edit = models.IntegerField(verbose_name='编辑', default=0)
    is_delete = models.IntegerField(verbose_name='删除', default=0)
    checked_choices = ((1, 'true'), (0, 'false'))
    checked = models.IntegerField(choices=checked_choices, verbose_name='显示菜单', default=0)

    class Meta:
        indexes = [
            models.Index(fields=['role'], name='role_idx', ),
        ]


# 人员与（部门_职务_关联表）的关联表
class UserDepPostMiddle(models.Model):
    id = models.UUIDField(primary_key=True, auto_created=True, default=uuid.uuid1, editable=False)
    user = models.ForeignKey("UserInfo", verbose_name='人员信息', to_field='id', null=True, blank=True,
                             on_delete=models.CASCADE)
    depPost = models.ForeignKey("DepartmentPost", verbose_name='部门职务关联信息', to_field='id', null=True, blank=True,
                                on_delete=models.CASCADE)


class WorkJob(models.Model):
    wid = models.UUIDField(primary_key=True, auto_created=True, default=uuid.uuid1, editable=False)
    # on_delete=models.SET_NULL表示外键关联到用户表,当用户表删除了该条数据,任务表中不删除,仅仅是把外键置空
    w_greatId = models.ForeignKey("UserInfo", to_field='id', null=True, blank=True, on_delete=models.SET_NULL)
    w_title = models.CharField(max_length=40, verbose_name='标题')
    w_project = models.ForeignKey("ProjectInfo", to_field='pid', verbose_name='所属项目', related_name='w_project', null=True, blank=True, on_delete=models.SET_NULL)
    w_info = models.CharField(max_length=999, verbose_name='发布内容')
    w_fileSave = models.CharField(max_length=99)
    w_priority_choices = ((0, '紧急'), (1, '加急'), (2, '一般'),)
    w_priority = models.IntegerField(choices=w_priority_choices, default=0)
    w_online_choices = ((0, '未完成'), (1, '已完成'),)
    w_online = models.IntegerField(choices=w_online_choices, default=0)
    w_chargeId = models.ForeignKey("UserInfo", to_field='id', verbose_name='负责人', related_name='w_chargeId', null=True, blank=True, on_delete=models.SET_NULL)
    w_charge_choices = ((0, '未开始'), (1, '处理中'), (2, '已完成'),)
    w_chargeType = models.IntegerField(choices=w_charge_choices, default=0)
    w_chargeTime = models.DateTimeField(blank=True, verbose_name='处理时间', null=True)
    w_chargeInfo = models.CharField(max_length=440, verbose_name='处理意见')
    w_reviewerId = models.ForeignKey("UserInfo", to_field='id', verbose_name='审核人', related_name='w_reviewerId', null=True, blank=True, on_delete=models.SET_NULL)
    w_reviewer_choices = ((0, '未开始'), (1, '处理中'), (2, '已完成'),)
    w_reviewerType = models.IntegerField(choices=w_reviewer_choices, default=0)
    w_reviewerTime = models.DateTimeField(blank=True, verbose_name='处理时间', null=True)
    w_reviewerInfo = models.CharField(max_length=440, verbose_name='处理意见')
    w_cc = models.CharField(max_length=40, verbose_name='抄送人')
    ctime = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', null=True)
    uptime = models.DateTimeField(auto_now=True, verbose_name='更新时间', null=True)

    class Meta:
        indexes = [
            models.Index(fields=['w_greatId', 'w_chargeId', 'w_reviewerId', 'ctime', 'uptime', ], name='workJob_idx', ),
        ]


class ProjectInfo(models.Model):
    pid = models.UUIDField(primary_key=True, auto_created=True, default=uuid.uuid1, editable=False)
    p_title = models.CharField(max_length=40, verbose_name='标题请控制在20个字符内')
    p_info = models.CharField(max_length=999, blank=True, verbose_name='项目内容')
    ctime = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', null=True)
    uptime = models.DateTimeField(auto_now=True, verbose_name='更新时间', null=True)
    p_greatId = models.ForeignKey("UserInfo", to_field='id', verbose_name='创建人', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        indexes = [
            models.Index(fields=['ctime', 'uptime', ], name='project_idx', ),
        ]
