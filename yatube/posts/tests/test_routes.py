from django.test import TestCase
from django.urls import reverse

from ..models import User, Post


SLUG = "testslug"
USERNAME = "Abraham"
POST_TEXT = "Тестовый текст, длинее 15 символов"
GROUP_TITLE = "Тестовая группа"
GROUP_DESCRIPTION = "Тестовое описание"
INDEX_URL = reverse("posts:index")
GROUP_LIST_URL = reverse("posts:group_list", args=[SLUG])
LOGIN_URL = reverse("users:login")
POST_CREATE_URL = reverse("posts:post_create")
FOLLOW_REDIRECT_CREATE_TO_LOGIN = f"{LOGIN_URL}?next={POST_CREATE_URL}"
PROFILE_URL = reverse("posts:profile", args=[USERNAME])


class RoutesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
        )
        cls.POST_DETAIL_URL = reverse("posts:post_detail", args=[cls.post.id])
        cls.POST_EDIT_URL = reverse("posts:post_edit", args=[cls.post.id])
        cls.FOLLOW_REDIRECT_EDIT_TO_LOGIN = (
            f"{LOGIN_URL}?next={cls.POST_EDIT_URL}")

    def test_routes(self):
        set = [
            [INDEX_URL, "/"],
            [GROUP_LIST_URL, f"/group/{SLUG}/"],
            [LOGIN_URL, "/auth/login/"],
            [POST_CREATE_URL, "/create/"],
            [FOLLOW_REDIRECT_CREATE_TO_LOGIN, "/auth/login/?next=/create/"],
            [PROFILE_URL, f"/profile/{USERNAME}/"],
            [self.POST_DETAIL_URL, f"/posts/{self.post.id}/"],
            [self.POST_EDIT_URL, f"/posts/{self.post.id}/edit/"],
            [self.FOLLOW_REDIRECT_EDIT_TO_LOGIN,
                f"/auth/login/?next=/posts/{self.post.id}/edit/"]
        ]
        for route, url in set:
            self.assertEqual(route, url, "неправильный расчет маршрута")
