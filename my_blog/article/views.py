from django.shortcuts import render,redirect
from django.http import HttpResponse
import markdown
from .models import *
from .forms import ArticlePostForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from comment.models import Comment
from comment.forms import CommentForm
from django.views.generic import View


def article_list(request):
    # 从 url 中提取查询参数
    search = request.GET.get('search')
    order = request.GET.get('order')
    column = request.GET.get('column')
    tag = request.GET.get('tag')

    # 初始化查询集
    article_list = ArticlePost.objects.all()

    # 搜索查询集
    if search:
        article_list = article_list.filter(
            Q(title__icontains=search) |
            Q(body__icontains=search)
        )
    else:
        search = ''

    # 栏目查询集
    if column is not None and column.isdigit():
        article_list = article_list.filter(column=column)

    # 标签查询集
    if tag and tag != 'None':
        article_list = article_list.filter(tags__name__in=[tag])

    # 查询集排序
    if order == 'total_views':
        article_list = article_list.order_by('-total_views')

    paginator = Paginator(article_list, 3)
    page = request.GET.get('page')
    articles = paginator.get_page(page)

    # 需要传递给模板（templates）的对象
    context = {
        'articles': articles,
        'order': order,
        'search': search,
        'column': column,
        'tag': tag,
    }

    return render(request, 'article/list.html', context)

def article_detail(request, id):
    article = ArticlePost.objects.get(id=id)
    # 取出文章评论
    comments = Comment.objects.filter(article=id)

    # 浏览量 +1
    article.total_views +=1
    article.save(update_fields=['total_views'])
    # 将markdown语法渲染成html样式
    md = markdown.Markdown(
        extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
        ]
    )
    article.body = md.convert(article.body)
    comment_form = CommentForm()
    context = { 'article': article, 'toc': md.toc, 'comments': comments, 'comment_form':comment_form}
    return render(request, 'article/detail.html', context)
@login_required(login_url='/userprofile/login/')
def article_create(request):

    # 判断用户是否提交数据
    if request.method == "POST":
        # 将提交的数据赋值到表单实例上去
        # 增加request.FILES
        article_post_form = ArticlePostForm(request.POST,request.FILES)
        # 判断提交提交数据是否满足模型需求
        if article_post_form.is_valid():
            new_article = article_post_form.save(commit=False)
            # 指定数据库中 id=1 的用户作者
            # 如果你进行过删除数据表的操作，可能会找不到id=1的用户
            # 此时请重新创建用户，并传入此用户的id
            new_article.author = User.objects.get(id=request.user.id)
            if request.POST['column'] !='none':
                new_article.column = ArticleColumn.objects.get(id=request.POST['column'])
            # 将新的文章保存到数据库中
            new_article.save()
            # 新增代码，保存 tags 的多对多关系
            article_post_form.save_m2m()
            # 完成返回到章节列表
            return redirect('article:article_list')
        else:
            return HttpResponse('表单有误，请重新填写')
    else:
        # 创建表单类实例
        article_post_form = ArticlePostForm()
        # 赋值上下文
        columns = ArticleColumn.objects.all()
        context = {'article_post_form':article_post_form,'columns':columns}
        return render(request,'article/create.html',context)

def article_delete(request,id):
    # 根据ID获取需要删除的章节
    article = ArticlePost.objects.get(id=id)
    # 调用delete()方法删除章节
    article.delete()
    # 完成删除后返回文章列表
    return redirect('article:article_list')
# 安全删除文章
def article_safe_delete(request,id):
    if request.method=='POST':
        article = ArticlePost.objects.get(id=id)
        article.delete()
        return redirect('article:article_list')
    else:
        return HttpResponse('仅允许post请求')


def article_update(request,id):
    """
        更新文章的视图函数
        通过POST方法提交表单，更新titile、body字段
        GET方法进入初始表单页面
        id： 文章的 id
        """
    # 获取需要修改的文章对象
    article = ArticlePost.objects.get(id=id)
    # 过滤非作者的用户
    if request.user !=article.author:
        return HttpResponse('抱歉，你无权修改这篇文章')
    # 判断是否为POST请求
    if request.method=='POST':
        # 将提交的数据赋值到表单实例中
        article_post_form = ArticlePostForm(data=request.POST)
        # 判断提交的数据是否符合模型的要求
        if article_post_form.is_valid():
            # 保存写入的title,body 的数据保存
            article.title = request.POST['title']
            article.body = request.POST['body']
            if request.FILES.get('avatar'):
                article.avatar = request.FILES.get('avatar')
            article.tags.set(*request.POST.get('tags').split('.'), clear=True)
            article.save()
            # 完成后返回到修改后的文章中。需传入文章的 id 值
            return redirect('article:article_detail',id=id)
        # 如果数据不合法，返回错误信息
        else:
            return HttpResponse('表单内容错误，请重新填写')
        # 如果用户 GET 请求获取数据
    else:
        # 创建表单类实例
        article_post_form = ArticlePostForm()
        # 赋值上下文，将 article 文章对象也传递进去，以便提取旧的内容
        context = {'article':article, 'article_post_form':article_post_form,'tags': ','.join([x for x in article.tags.names()]),}
        return render(request,'article/update.html', context)

class IncreaseLikesView(View):
    def post(self, request, *args, **kwargs):
        article = ArticlePost.objects.get(id=kwargs.get('id'))
        article.likes += 1
        article.save()
        return HttpResponse('success')
