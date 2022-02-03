from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post, User


def pages_creator(request, post_list):
    return Paginator(post_list.order_by("-pub_date"), 10).get_page(
        request.GET.get("page")
    )


def index(request):
    return render(
        request,
        "posts/index.html",
        {
            "page_obj": pages_creator(request, Post.objects.all()),
        },
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(
        request,
        "posts/group_list.html",
        {
            "group": group,
            "page_obj": pages_creator(request, group.posts.all()),
        },
    )


def profile(request, username):
    user = get_object_or_404(User, username=username)
    return render(
        request,
        "posts/profile.html",
        {
            "author": user,
            "page_obj": pages_creator(request, user.posts.all()),
        },
    )


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return render(request, "posts/post_detail.html", {"post": post})


@login_required
def post_create(request):
    template = "posts/create_post.html"
    form = PostForm(request.POST or None)
    if not form.is_valid():
        return render(request, template, {"form": form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect("posts:profile", username=post.author)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect("posts:post_detail", post_id=post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id=post_id)
    context = {
        "form": form,
        "post_id": post_id,
        "is_edit": True,
    }
    return render(request, "posts/create_post.html", context)
