from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post


def get_page(request, post_list):
    paginator = Paginator(post_list, settings.POSTS_ON_PAGE)
    return paginator.get_page(request.GET.get('page'))


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': get_page(request, group.posts.select_related(
            'author'),)
    })


@cache_page(20, key_prefix='index_page')
def index(request):
    context = {
        'page_obj': get_page(request, Post.objects.select_related(
            'author', 'group')),
        'title': 'Последние обновления на сайте',
    }
    return render(request, 'posts/index.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', request.user.username)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    title = 'Редактировать запись'
    context = {
        'form': form,
        'is_edit': True,
        'title': title,
        'post': post,
    }
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, 'posts/create_post.html', context)


def profile(request, username):
    """Профиль автора с возможность подписки на него."""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group')
    page_obj = get_page(request, post_list)
    following = request.user.is_authenticated and (
        author.following.filter(user=request.user).exists()
    )
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Детальные сведения поста и комментарии к нему."""
    post = get_object_or_404(Post.objects.select_related(
        'author', 'group'), pk=post_id)
    comments = post.comments.select_related('author')
    context = {
        'post': post,
        'form': CommentForm(),
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    context = {
        'page_obj': get_page(
            request,
            Post.objects.filter(author__following__user=request.user)),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user,
            author=author,
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username)
