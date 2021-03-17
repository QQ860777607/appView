from django.shortcuts import render, HttpResponse, redirect, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.clickjacking import xframe_options_exempt
from django.db.models import Count, Min, Max, Sum
from django_pandas.io import read_frame
from dataView import models
from dataView.other.findPath import FindPath
from pathlib import Path
from bs4 import BeautifulSoup
import json, arrow, pinyin, re
import pandas as pd

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent


# 用户登录函数
def login(request):
    if request.method == 'POST':
        username = request.POST.get("u", None)
        password = request.POST.get("p", None)
        try:
            item = models.UserInfo.objects.get(userName=username)
        except ObjectDoesNotExist:
            return HttpResponse('用户名错误')
        if check_password(password, item.password):
            # 存入session
            request.session['key'] = username
            return render(request, 'dataView/index.html', {'userName': username, 'realName': models.UserInfo.objects.filter(userName=username).values('realName')[0]['realName']})
        return HttpResponse('用户名密码错误')

    if request.method == 'GET':
        return render(request, 'dataView/api/login.html')


@xframe_options_exempt
def import_data(request):
    ret = {}
    if request.method == 'GET':
        v = pd.DataFrame(columns=['Ptitle', 'KWord', 'wordName', 'Introduce', 'SecName', 'IssuseTime', 'ID', 'c_id'])
        v['id'] = range(1, len(v) + 1)
        ret['get_name'] = json.loads(v.to_json(orient='records').encode('utf-8').decode('unicode_escape'))
    elif request.method == 'POST':
        do = request.POST.get('do', 0)
        if do == "1":
            dt = pd.read_excel(request.FILES.get('file'))
            post_list_to_insert = []
            for index, row in dt.iterrows():
                insert = models.UserPost(
                    alias=row['alias'],
                    creationType=row['creationType'],
                    status=row['status'],
                    lastOperationType=row['lastOperationType'],
                    name=row['name'],
                )
                if insert not in post_list_to_insert:
                    post_list_to_insert.append(insert)
            models.UserPost.objects.bulk_create(post_list_to_insert)
            return HttpResponse(json.dumps(ret))
        if do == "2":
            dt = pd.read_excel(request.FILES.get('file'))
            post_list_to_insert = []
            for index, row in dt.iterrows():
                insert = models.UserInfo(
                    alias=row['alias'],
                    userName=row['userName'],
                    realName=row['realName'],
                    userPhone=row['userPhone'],
                    password=make_password(row['password'], None, 'pbkdf2_sha256')
                )
                if insert not in post_list_to_insert:
                    post_list_to_insert.append(insert)
            models.UserInfo.objects.bulk_create(post_list_to_insert)
            return HttpResponse(json.dumps(ret))
    return render(request, 'dataView/api/import_data.html', ret)


@xframe_options_exempt
def menu_edit(request):
    """菜单管理"""
    ret = {'message': None}
    if request.method == 'GET':
        return render(request, 'dataView/api/menu.html', ret)
    if request.method == 'POST':
        # 获取 当前用户 在 用户表 中相应的角色ID，用户可以同时分配多个角色
        s = models.UserInfo.objects.filter(userName=request.session['key']).values('uRole__id')
        l1 = []
        for i in s:
            l1.append(i['uRole__id'])
        # 角色权限表：通过角色ID(role_id)获取角色已分配的目录
        qs2 = models.Author.objects.filter(role_id__in=l1).values('menu_id', 'checked')
        l1.clear()
        for i in qs2:
            if i['checked'] == 1:
                l1.append(i['menu_id'])
        qs = read_frame(
            qs=models.SystemMenu.objects.filter(id__in=set(l1)).values(
                'id', 'title', 'pid', 'icon', 'href', 'target', 'sort').order_by(
                'pid', 'sort'))
        menu_if = list_to_tree(qs.to_dict(orient='records'), 0, 'pid', 'id', )
        menu_dc = {"homeInfo": {
            "title": "首页",
            "href": "main_page"
        }, "logoInfo": {
            "title": "",
            "image": "/static/layuimini/images/logo.png",
            "href": "",
            "size": "11 px"
        }, 'menuInfo': menu_if}
        return HttpResponse(json.dumps(menu_dc), content_type='application/json')


def list_to_tree(data, root, root_field, node_field, last_id=None):
    """
    解析list数据为树结构
    :param data:  被解析的数据data = [{'id': 1, 'title': 'GGG', 'parent_id': 0},{'id': 2, 'title': 'AAA', 'parent_id': 0},]
    :param root: 根节点值
    :param root_field: 根节点字段'parent_id'
    :param node_field: 节点字段'id'
    :return: list
    :调用：tree(data, 0, 'parent_id', 'id')
    """
    l = []
    for i in data:
        if i.get(root_field) == root:
            l.append(i)
    for i in data:
        node = i.get(node_field)
        children = []
        for j in data:
            parent = j.get(root_field)
            if node == parent:
                if last_id == parent:
                    i['isOpen'] = True
                children.append(j)
        i['child'] = children
        del i['pid']
        del i['id']
    return l


def list_to_tree_dp(data, root, root_field, node_field, last_id=None):
    """
    解析list数据为树结构
    :param data:  被解析的数据data = [{'id': 1, 'title': 'GGG', 'parent_id': 0},{'id': 2, 'title': 'AAA', 'parent_id': 0},]
    :param root: 根节点值
    :param root_field: 根节点字段'parent_id'
    :param node_field: 节点字段'id'
    :return: list
    :调用：tree(data, 0, 'parent_id', 'id')
    """
    l = []
    for i in data:
        if str(i.get(root_field)) == root:
            l.append(i)
    for i in data:
        node = i.get(node_field)
        children = []
        for j in data:
            parent = j.get(root_field)
            if str(node) == parent:
                if last_id == parent:
                    i['isOpen'] = True
                children.append(j)

        i['children'] = children
        del i['parentId']
    return l


@xframe_options_exempt
def main_page(request):
    ret = {'message': 1, 'data': {'id': 0}}
    return render(request, 'dataView/api/mainPage.html', ret)


@xframe_options_exempt
def structure(request):
    ret = {'message': None}
    if request.method == 'GET':
        ret['get_name'] = json.dumps(list(models.CompanyInfo.objects.all().values()), cls=DjangoJSONEncoder)
        return render(request, 'dataView/api/structure.html', ret)
    if request.method == 'POST':
        do = request.POST.get('do', "0")
        # 系统管理－组织构架－新增按钮
        if do == "0":
            v = request.POST.get('id')
            if len(v) < 4:
                ret['message'] = '不能少于4个字符'
                return HttpResponse(json.dumps(ret))
            if models.CompanyInfo.objects.filter(companyName=v).count() == 0:
                models.CompanyInfo.objects.create(companyName=v)
            else:
                ret['message'] = v + '已存在，请重新输入'
                return HttpResponse(json.dumps(ret))
            ret['data'] = json.dumps(list(models.CompanyInfo.objects.all().values()), cls=DjangoJSONEncoder)
            return HttpResponse(json.dumps(ret))
        # 系统管理－组织构架－删除按钮
        elif do == "1":
            d = eval(request.POST.get('id'))
            if len(d) > 0:
                for i in d:
                    models.CompanyInfo.objects.filter(id=i).delete()
            ret['message'] = 'done'
            return HttpResponse(json.dumps(ret))
        # 系统管理－组织构架－刷新按钮
        elif do == "2":
            data = json.loads(json.dumps(list(models.CompanyInfo.objects.all().values()), cls=DjangoJSONEncoder))
            ret['code'] = 0
            ret['msg'] = ""
            ret['count'] = len(data)
            ret['data'] = data
            return HttpResponse(json.dumps(ret))
        # 系统管理－组织构架－编辑按钮
        elif do == "3":
            d = eval(request.POST.get('id'))
            models.CompanyInfo.objects.filter(id=d[0]).update(companyName=d[1], uptime=arrow.utcnow().datetime)
            ret['data'] = json.dumps(list(models.CompanyInfo.objects.all().values()), cls=DjangoJSONEncoder)
            return HttpResponse(json.dumps(ret))


@xframe_options_exempt
def account_management(request):
    ret = {'message': None}
    qs = read_frame(models.UserInfo.objects.all().values('id', 'userName', 'realName', 'uCollege', 'userPhone',
                                                         'uBDate', 'uDate', 'userMail', 'status', 'uptime', 'uRole__roleName'))
    # 指定dataFrame列中，取出重复的数据行
    sh = qs.loc[set(qs.index) - set(qs.drop_duplicates(subset=['id', 'userName'], keep=False).index), :]
    # pandas 按'id'列分组，将'uRole__roleName'列合并成字典
    plist = sh.groupby(['id']).uRole__roleName.apply(list).to_dict()
    print(plist)
    # 删除指定列中重复的数据行
    qs = qs.drop_duplicates(subset='id')
    if len(plist) > 0:
        for k, v in plist.items():
            print(k, v)
            qs.loc[qs.id == k, 'uRole__roleName'] = "，".join(v)

    for index, row in qs.iterrows():
        v_date = tp2("冻结", row['status'])
        qs.loc[index, 'status'] = v_date[1]
    qs = qs.sort_values(axis=0, by='uptime', ascending=False)
    ret['get_name'] = json.dumps(qs.to_dict(orient='records'), cls=DjangoJSONEncoder)
    if request.method == 'GET':
        return render(request, 'dataView/api/account_management.html', ret)
    if request.method == 'POST':
        return HttpResponse(json.dumps(ret))


@xframe_options_exempt
def role_select(request, req):
    data = [{
        'name': '角色分配',
        'id': 0,
        'pId': "",
        'childOuter': False,
        'open': True
    }]
    ret = {'message': None}
    if request.method == 'GET':
        qs = read_frame(qs=models.Role.objects.all())
        qs['checked'] = 'false'
        qs1 = read_frame(models.UserInfo.objects.filter(id=req).values('uRole__id'))
        for r, v in qs1.iterrows():
            qs.loc[qs.id == v['uRole__id'], 'checked'] = 'true'
        qs['pId'] = 0
        qs.rename(columns={'roleName': 'name'}, inplace=True)
        ret['data'] = json.dumps(json.loads(json.dumps(qs.sort_values(by=['sortIndex'], ascending=True).to_dict(
            orient='records'), cls=DjangoJSONEncoder))+data)
        return render(request, 'dataView/api/roleSelect.html', ret)
    if request.method == 'POST':
        v = json.loads(request.POST.get('v'))
        vid = request.POST.get('vid')
        if req == 'edit':
            lt1 = []
            for i in v:
                lt1.append(i['id'])
            obj = models.UserInfo.objects.get(id=vid)
            obj.uRole.set(lt1)
        ret['message'] = 'success'
        return HttpResponse(json.dumps(ret))


@xframe_options_exempt
def author(request):
    ret = {'message': False}
    if request.method == 'POST':
        v = json.loads(request.POST.get('v'))
        do = request.POST.get('do')
        if len(v) > 0:
            for i in v:
                if i['checked']:
                    i['checked'] = 1
                else:
                    i['checked'] = 0
                c = models.Author.objects.filter(menu__id=i['menu_id'], role__id=i['role_id']).count()
                if c != 0:
                    models.Author.objects.filter(menu__id=i['menu_id'], role__id=i['role_id']).update(checked=i['checked'])
                else:
                    models.Author.objects.create(menu_id=i['menu_id'], role_id=i['role_id'], checked=i['checked'])
            ret['message'] = True
        return HttpResponse(json.dumps(ret), content_type="application/json")   # 返回json数据


@xframe_options_exempt
def role_info(request):
    ret = {'message': None}
    data = [{
        'name': '角色管理',
        'id': 0,
        'pId': "",
        'childOuter': False,
        'open': True
    }]
    if request.method == 'GET':
        qs = read_frame(qs=models.Role.objects.all())
        qs['pId'] = 0
        qs.rename(columns={'roleName': 'name'}, inplace=True)
        ret['data'] = json.dumps(json.loads(json.dumps(qs.sort_values(by=['sortIndex'], ascending=True).to_dict(orient='records'), cls=DjangoJSONEncoder))+data)
        return render(request, 'dataView/api/roleInfo.html', ret)
    if request.method == 'POST':
        v = request.POST.get('value')
        do = request.POST.get('do')
        qs = models.Role.objects.all().aggregate(Max('sortIndex'))
        last_id = request.POST.get('lastID')  # 角色ID
        if do == 'add':
            if qs['sortIndex__max'] is None:
                smx = 0
            else:
                smx = qs['sortIndex__max'] + 1
            obj = models.Role(roleName=v, sortIndex=smx)
            obj.save()
            qs = read_frame(qs=models.Role.objects.all())
            qs['pId'] = 0
            qs.rename(columns={'roleName': 'name'}, inplace=True)
            ret['data'] = json.dumps(json.loads(json.dumps(qs.sort_values(by=['sortIndex'], ascending=False).to_dict(orient='records'), cls=DjangoJSONEncoder))+data)
        elif do == 'edit':
            obj = models.Role.objects.get(id=last_id)
            obj.roleName = v
            obj.save()
        elif do == 'del':
            obj = models.Role.objects.filter(id=last_id)
            if obj.count() == 1:
                obj.delete()
            else:
                ret['message'] = 2
        elif do == 'move':
            l1 = json.loads(v)
            if len(l1) > 0:
                for i in l1:
                    print(i['id'])
                    models.Role.objects.filter(id=i['id'], ).update(sortIndex=i['sortIndex'])
                ret['state'] = 'success'
        elif do == 'onclick':
            data1 = [{
                'name': '显示设置',
                'id': 0,
                'pId': "",
                'childOuter': False,
                'open': True
            }]
            qs1 = read_frame(qs=models.SystemMenu.objects.all().values('id', 'title', 'pid', 'sort'))
            qs1.rename(columns={'title': 'name', 'pid': 'pId', 'sort': 'sortIndex'}, inplace=True)
            qs = read_frame(qs=models.Author.objects.filter(role_id=last_id).values('menu__id', 'checked'))
            qs.rename(columns={'menu__id': 'id'}, inplace=True)
            if len(qs) == 0:
                qs1['checked'] = 'false'
                qs2 = qs1
            else:
                qs2 = pd.merge(qs1, qs, how='left', on=['id', ], sort=True)
                qs2['checked'] = qs2['checked'].apply(lambda x: x if x in ('false', 'true') else 'false')
            ret['data'] = json.dumps(
                qs2.sort_values(by=['pId', 'sortIndex'], ascending=True).to_dict(orient='records') + data1)
        return HttpResponse(json.dumps(ret))


@xframe_options_exempt
def user_reg_edit(request):
    ret = {'message': None}
    if request.method == 'GET':
        ret['arrayNation'] = (
            '汉族', '蒙古族', '彝族', '侗族', '哈萨克族', '畲族', '纳西族', '仫佬族', '仡佬族', '怒族', '保安族',
            '鄂伦春族', '回族', '壮族', '瑶族', '傣族', '高山族', '景颇族', '羌族', '锡伯族', '乌孜别克族', '裕固族', '赫哲族',
            '藏族', '布依族', '白族', '黎族', '拉祜族', '柯尔克孜族', '布朗族', '阿昌族', '俄罗斯族', '京族', '门巴族', '维吾尔族',
            '朝鲜族', '土家族', '傈僳族', '水族', '土族', '撒拉族', '普米族', '鄂温克族', '塔塔尔族', '珞巴族', '苗族', '满族',
            '哈尼族', '佤族', '东乡族', '达斡尔族', '毛南族', '塔吉克族', '德昂族', '独龙族', '基诺族')
        ret['arrayEducation'] = ('文盲', '小学', '初中', '高中', '职高', '中专', '大专', '本科', '硕士', '博士')
        return render(request, 'dataView/api/userRegEdit.html', ret)
    if request.method == 'POST':
        name = request.POST.get('name', 0)
        do = request.POST.get('do', 0)
        # 验证用户添加时，用户名是否存在数据库中
        if do == '1':
            # 验证手机号是否正确
            phone_pat = re.compile("^(13\\d|14[5|7]|15\\d|166|17[3|6|7]|18\\d)\\d{8}$")
            res = re.search(phone_pat, name)
            if res:
                ret['isPhone'] = True
            else:
                ret['isPhone'] = False
            try:
                item = models.UserInfo.objects.get(userName=name)
            except ObjectDoesNotExist:
                ret['isIn'] = False
                return HttpResponse(json.dumps(ret))
            ret['isIn'] = True
        if do == '2':            
            dt = json.loads(name)
            if len(dt['uBDate']) > 0:
                dt['uBDate'] = dt['uBDate']+" 00:00:00"
            else:
                dt['uBDate'] = None
            if len(dt['uDate']) > 0:
                dt['uDate'] = dt['uDate']+" 00:00:00"
            else:
                dt['uDate'] = None
            ps = make_password(dt['password'], None, 'pbkdf2_sha256')
            dt['alias'] = pinyin.get_initial(dt['realName'], delimiter="").lower()
            dt['status'] = {'on': 1, 'off': 0}[dt.get('status', 'off')]
            img = dt.get('image[0]', 0)
            if img == 0:
                dt['uPhotos'] = ''
            else:
                dt['uPhotos'] = img
                del dt['image[0]']
            del dt['password']
            models.UserInfo.objects.create(**dt)
            models.UserInfo.objects.filter(userName=dt['userName']).update(password=ps)
            ret['message'] = 'ok'
        if do == '3':
            models.UserInfo.objects.filter(id=name).delete()
            ret['message'] = 'ok'
        return HttpResponse(json.dumps(ret))


@xframe_options_exempt
def user_edit(request, uid):
    ret = {'message': None}
    if request.method == 'GET':
        v = read_frame(models.UserInfo.objects.filter(id=uid))
        v['uBDate'] = v['uBDate'].apply(lambda x: x.strftime('%Y-%m-%d') if x else "")
        v['uDate'] = v['uDate'].apply(lambda x: x.strftime('%Y-%m-%d') if x else "")
        ret['data'] = json.loads(json.dumps(v.to_dict(orient='records'), cls=DjangoJSONEncoder))[0]
        ret['arrayEducation'] = ('文盲', '小学', '初中', '高中', '职高', '中专', '大专', '本科', '硕士', '博士')
        if ret['data']['uPhotos']:
            ret['data']['uPhotos'] = ret['data']['uPhotos'].split('base64,')[1]

        return render(request, 'dataView/api/userEdit.html', ret)
    if request.method == 'POST':
        name = request.POST.get('name', 0)
        data = json.loads(name)
        data['status'] = {'on': 1, 'off': 0}[data.get('status', 'off')]
        data['alias'] = pinyin.get_initial(data['realName'], delimiter="").lower()
        data['uCollege'] = int(data.get('uCollege', '0'))
        data['uSex'] = int(data.get('uSex', '1'))
        if data.get('image[0]', 0) != 0:
            data['uPhotos'] = data['image[0]']
            del data['image[0]']
        models.UserInfo.objects.filter(userName=data['userName']).update(**data)
        ret['message'] = 'ok'
        return HttpResponse(json.dumps(ret))


def tp2(d1, d2):
    KWord = str(d1).replace("'", "")
    # Introduce = re.sub(r'</?\w+[^>]*>', '', str(d2).replace('<br/','')).replace("'", "")
    Introduce = BeautifulSoup(BeautifulSoup(str(d2), 'html.parser').text, "html.parser").prettify()
    if KWord != "":
        x = str(KWord).split(',')
        for i in range(len(x)):
            Introduce = Introduce.replace(x[i], '<span style = "color: red">' + x[i] + '</span>')
            x[i] = '<span style = "color: red">' + x[i] + '</span>'
        return [x, Introduce]
    else:
        return [KWord, Introduce]


@xframe_options_exempt
def department(request, dpe):
    ret = {'message': 1, 'data': {'id': dpe}}
    data = [{
        'name': '所有部门',
        'id': dpe,
        'pId': "",
        'childOuter': False,
        'open': True
    }]
    if request.method == 'GET':
        qs = models.Department.objects.filter(companyInfo_id_id=dpe).values('id', 'department', 'parentId', 'sortIndex')
        qs1 = read_frame(qs=qs)
        qs1.rename(columns={'department': 'name', 'parentId': 'pId'}, inplace=True)
        ret['data'] = json.dumps(
            qs1.sort_values(by=['pId', 'sortIndex'], ascending=True).to_dict(orient='records') + data)
    if request.method == 'POST':
        v = request.POST.get('value')  # 获取提交的部门名称
        do = request.POST.get('do')  # do: add update del部门结构的增减删除操作类型
        last_id = request.POST.get('lastID')  # 部门ID
        if do == 'add':
            if dpe == last_id:
                qs = models.Department.objects.filter(parentId=dpe).aggregate(Max('sortIndex'))
                if qs['sortIndex__max'] is None:
                    smx = 0
                else:
                    smx = qs['sortIndex__max'] + 1
                obj = models.Department(department=v, companyInfo_id_id=dpe, parentId=last_id, fullPath=dpe,
                                        sortIndex=smx)
                obj.save()
            else:
                v1 = models.Department.objects.filter(id=last_id).values('fullPath').first()['fullPath'] + ',' + last_id
                qs = models.Department.objects.filter(parentId=last_id).aggregate(Max('sortIndex'))
                if qs['sortIndex__max'] is None:
                    smx = 0
                else:
                    smx = qs['sortIndex__max'] + 1
                obj = models.Department(department=v, companyInfo_id_id=dpe, parentId=last_id, fullPath=v1,
                                        sortIndex=smx)
                obj.save()
            qs = models.Department.objects.filter(parentId=last_id, department=v).values('id', 'department', 'parentId')
            qs1 = read_frame(qs=qs)
            qs1.rename(columns={'department': 'name', 'parentId': 'pId'}, inplace=True)

            ret['data'] = json.dumps(qs1.to_dict(orient='records'))
        elif do == 'del':
            v1 = models.Department.objects.filter(id=last_id).values('fullPath').first()['fullPath']
            if models.Department.objects.filter(parentId=last_id).count() == 0:
                models.Department.objects.filter(id=last_id).delete()
            else:
                ret['message'] = 2
                return HttpResponse(json.dumps(ret))
        elif do == 'edit':
            obj = models.Department.objects.get(id=last_id)
            obj.department = v
            obj.save()
            v1 = models.Department.objects.filter(id=last_id).values('fullPath').first()['fullPath']
            qs = models.Department.objects.filter(companyInfo_id_id=dpe).values('id', 'department', 'parentId')
            qs1 = read_frame(qs=qs)
            qs1.rename(columns={'department': 'label'}, inplace=True)
            xx = list_to_tree_dp(qs1.to_dict(orient='records'), dpe, 'parentId', 'id', last_id)
            data[0]['children'] = xx
            for i in v1.split(','):
                f1 = "data" + FindPath(data).the_value_path(str(i))[0].replace("['id']", "") + "['isOpen']= True"
                exec(f1)
        elif do == 'move':
            l1 = json.loads(v)
            try:
                for i in l1:
                    if i['parentId'] == dpe:
                        full_path = dpe
                        models.Department.objects.filter(id=i['id'], ).update(parentId=i['parentId'],
                                                                              sortIndex=i['sortIndex'],
                                                                              fullPath=full_path)
                    else:
                        ph = models.Department.objects.filter(id=i['parentId']).values('id', 'fullPath').first()
                        full_path = ph['fullPath'] + ',' + str(ph['id'])
                        models.Department.objects.filter(id=i['id'], ).update(parentId=i['parentId'], sortIndex=i['sortIndex'], fullPath=full_path)
                ret['state'] = 'success'
            except:
                ret['state'] = 'error'
        elif do == 'movePost':
            l1 = json.loads(v)
            for i in l1:
                print(dpe.split('|')[0],i['id'],i['sortIndex'])
                models.DepartmentPost.objects.filter(department_id=dpe.split('|')[0], post_id=i['id']).update(sortIndex=i['sortIndex'])
            ret['state'] = 'success'
        elif do == 'onclick':
            qs = models.DepartmentPost.objects.filter(department_id=last_id).values('id', 'post__id', 'post__name', 'sortIndex')
            qs1 = read_frame(qs=qs)
            qs1.rename(columns={'id': 'sId'}, inplace=True)
            qs1.rename(columns={'post__name': 'name', 'post__id': 'id'}, inplace=True)
            ret['data'] = json.dumps(qs1.sort_values(by=['sortIndex'], ascending=True).to_dict(orient='records'), cls=DjangoJSONEncoder)
            qs = read_frame(models.UserDepPostMiddle.objects.filter(depPost__department=last_id).values('depPost__post__name', 'user__id', 'user__realName', 'user__uPhotos', 'depPost__sortIndex'))
            ret['userData'] = json.dumps(qs.sort_values(by=['depPost__sortIndex'], ascending=True).to_dict(orient='records'), cls=DjangoJSONEncoder)

        return HttpResponse(json.dumps(ret))
    return render(request, 'dataView/api/department.html', ret)


@xframe_options_exempt
def dep_add_post(request, dpe):
    ret = {'message': 1, 'data': None}
    if request.method == 'GET':
        qs2 = read_frame(
            qs=models.DepartmentPost.objects.filter(department_id=int(dpe)).values('post__id', 'post__name'))
        qs2.rename(columns={'post__name': 'name', 'post__id': 'id'}, inplace=True)
        qs = models.UserPost.objects.values('id', 'name')
        qs1 = read_frame(qs=qs)
        ret['data'] = json.dumps(qs1.sort_values(by=['name'], ascending=True).to_dict(orient='records'),
                                 cls=DjangoJSONEncoder)
        ret['dataCheck'] = json.dumps(qs2.sort_values(by=['name'], ascending=True).to_dict(orient='records'),
                                      cls=DjangoJSONEncoder)
        ret['dpe'] = dpe
        return render(request, 'dataView/api/dep_add_post.html', ret)
    if request.method == 'POST':
        v = request.POST.get('value')
        do = request.POST.get('do')
        if do == 'dpePost':
            tp_list = []
            v = json.loads(v)
            for i in v:
                tp_list.append(i['id'])
            obj = models.DepartmentPost.objects.filter(department_id=int(dpe)).values('post_id')
            if len(obj) > 0:
                for i in obj:
                    if str(i['post_id']) not in tp_list:
                        models.DepartmentPost.objects.filter(department_id=int(dpe), post_id=i['post_id']).delete()
            for i in v:
                models.DepartmentPost.objects.update_or_create(department_id=int(dpe), post_id=i['id'])
            qs = read_frame(
                qs=models.DepartmentPost.objects.filter(department_id=int(dpe)).values('id', 'post__id', 'post__name'))
            qs.rename(columns={'id': 'sId'}, inplace=True)
            qs.rename(columns={'post__name': 'name', 'post__id': 'id'}, inplace=True)
            ret['data'] = json.dumps(qs.to_dict(orient='records'), cls=DjangoJSONEncoder)
        elif do == 'addPost':
            alias = pinyin.get_initial(dpe, delimiter="").lower()
            models.UserPost.objects.create(alias=alias, name=dpe)
            qs = read_frame(qs=models.UserPost.objects.filter(name=dpe).values('id', 'name'))
            ret['data'] = json.dumps(qs.to_dict(orient='records'), cls=DjangoJSONEncoder)
        elif do == 'isTrue':
            ret['data'] = models.DepartmentPost.objects.filter(post_id=v).count()
        elif do == 'refresh':
            qs2 = read_frame(
                qs=models.DepartmentPost.objects.filter(department_id=int(dpe)).values('post__id', 'post__name'))
            qs2.rename(columns={'post__name': 'name', 'post__id': 'id'}, inplace=True)
            qs = models.UserPost.objects.values('id', 'name')
            qs1 = read_frame(qs=qs)
            qs1['checked'] = 'false'
            for r, v in qs2.iterrows():
                qs1.loc[qs1.id == v['id'], 'checked'] = 'true'
            ret['data'] = json.dumps(qs1.sort_values(by=['checked', 'name'], ascending=False).to_dict(orient='records'),
                                     cls=DjangoJSONEncoder)
            ret['dpe'] = dpe
    return HttpResponse(json.dumps(ret))


@xframe_options_exempt
def dep_add_user(request, dpe):
    ret = {'message': 1, 'data': None, 'dataCheck': []}
    if request.method == 'GET':
        qs = read_frame(
            models.UserInfo.objects.filter(status=1).values('id', 'userName', 'realName'))
        qs['title'] = qs['realName'] + "(" + qs['userName'] + ")"
        qs.drop(['userName', 'realName'], axis=1, inplace=True)
        ret['data'] = json.dumps(qs.to_dict(orient='records'), cls=DjangoJSONEncoder)
        qs1 = models.UserDepPostMiddle.objects.filter(depPost_id=dpe).values('user_id')
        for i in qs1:
            ret['dataCheck'].append(str(i['user_id']))
        return render(request, 'dataView/api/dep_add_user.html', ret)
    if request.method == 'POST':
        do = request.POST.get('do', 0)
        if do == 'addUser':
            v = json.loads(request.POST.get('value'))
            tp_list = []
            for i in v:
                tp_list.append(i['value'])
            obj = models.UserDepPostMiddle.objects.filter(depPost_id=dpe).values('user_id')
            if len(obj) > 0:
                for i in obj:
                    if str(i['user_id']) not in tp_list:
                        models.UserDepPostMiddle.objects.filter(depPost_id=dpe, user_id=i['user_id']).delete()
            for i in v:
                models.UserDepPostMiddle.objects.update_or_create(user_id=i['value'], depPost_id=dpe)
            qs = read_frame(
                models.UserDepPostMiddle.objects.filter(depPost_id=dpe).values('user__id', 'user__realName', 'user__uPhotos'))
            ret['data'] = json.dumps(qs.to_dict(orient='records'), cls=DjangoJSONEncoder)
        if do == 'findPostUser':
            qs = read_frame(
                models.UserDepPostMiddle.objects.filter(depPost_id=dpe).values('depPost__post__name', 'user__id', 'user__realName', 'user__uPhotos'))
            ret['data'] = json.dumps(qs.to_dict(orient='records'), cls=DjangoJSONEncoder)
    return HttpResponse(json.dumps(ret))


@xframe_options_exempt
def e_flowchart(request):
    ret = {'message': 1, 'data': {'id': 0}}
    return render(request, 'dataView/api/e_flowchart.html', ret)


@xframe_options_exempt
def scrollbar(request):
    ret = {'message': 1, 'data': {'id': 0}}
    return render(request, 'dataView/api/scrollBar.html', ret)


@xframe_options_exempt
def icon_list(request):
    return render(request, 'dataView/api/icon.html')


@xframe_options_exempt
def menu_info(request):
    ret = {'message': None, 'data': {'id': 0}}
    data = [{
        'name': '目录管理',
        'id': 0,
        'pId': "",
        'childOuter': False,
        'open': True
    }]
    if request.method == 'GET':
        qs = models.SystemMenu.objects.all().values('id', 'title', 'pid', 'sort')
        qs1 = read_frame(qs=qs)
        qs1.rename(columns={'title': 'name', 'pid': 'pId', 'sort': 'sortIndex'}, inplace=True)
        ret['data'] = json.dumps(
            qs1.sort_values(by=['pId', 'sortIndex'], ascending=True).to_dict(orient='records') + data)
        return render(request, 'dataView/api/edit_menu.html', ret)
    if request.method == 'POST':
        title = request.POST.get('title')
        do = request.POST.get('do')
        pid = request.POST.get('ID')
        if do == 'add':
            qs = models.SystemMenu.objects.filter(pid=pid).aggregate(Max('sort'))
            if qs['sort__max'] is None:
                smx = 0
            else:
                smx = qs['sort__max'] + 1
            if pid == 0:
                obj = models.SystemMenu(title=title, sort=smx)
            else:
                obj = models.SystemMenu(pid=pid, title=title, sort=smx)
            obj.save()
            qs = models.SystemMenu.objects.filter(title=title, pid=pid).values('id', 'title', 'pid', 'sort')
            qs1 = read_frame(qs=qs)
            qs1.rename(columns={'title': 'name', 'pid': 'pId', 'sort': 'sortIndex'}, inplace=True)
            ret['data'] = json.dumps(
                qs1.sort_values(by=['pId', 'sortIndex'], ascending=True).to_dict(orient='records') + data)
        if do == 'del':
            if models.SystemMenu.objects.filter(pid=pid).count() == 0:
                if models.SystemMenu.objects.filter(id=pid).values('is_sys_menu')[0]['is_sys_menu'] == 0:
                    models.SystemMenu.objects.filter(id=pid).delete()
                    ret['message'] = 0
                else:
                    ret['message'] = 1
            else:
                ret['message'] = 2
        if do == 'onclick':
            qs = read_frame(qs=models.SystemMenu.objects.filter(id=pid))
            ret['data'] = json.dumps(qs.to_dict(orient='records'), cls=DjangoJSONEncoder)
        if do == 'edit':
            if models.SystemMenu.objects.filter(id=pid).values('is_sys_menu')[0]['is_sys_menu'] == 0:
                obj = models.SystemMenu.objects.get(id=pid)
                obj.title = title
                obj.save()
                ret['message'] = 1
            else:
                ret['message'] = 0
        if do == 'move':
            l1 = json.loads(title)
            try:
                for i in l1:
                    models.SystemMenu.objects.filter(id=i['id'], ).update(pid=i['parentId'], sort=i['sortIndex'])
                ret['state'] = 'success'
            except:
                ret['state'] = 'error'
        if do == 'save':
            try:
                v = json.loads(title)
                if v.get('icon', 0) != 0:
                    v['icon'] = 'fa ' + v['icon']
                if v.get('status', 0) == 0:
                    v['status'] = 0
                else:
                    v['status'] = 1
                models.SystemMenu.objects.filter(id=pid, ).update(**v)
                ret['state'] = 'success'
            except:
                ret['state'] = 'error'
        return HttpResponse(json.dumps(ret))
