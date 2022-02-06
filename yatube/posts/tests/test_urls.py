from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

SLUG = "testslug"
AUTHOR_USERNAME = "Abraham"
NOT_AUTHOR_USERNAME = "Isaak"
POST_TEXT = "Тестовый текст, длинее 15 символов"
GROUP_TITLE = "Тестовая группа"
GROUP_DESCRIPTION = "Тестовое описание"
INDEX_URL = reverse("posts:index")
GROUP_LIST_URL = reverse("posts:group_list", args=[SLUG])
LOGIN_URL = reverse("users:login")
POST_CREATE_URL = reverse("posts:post_create")
FOLLOW_REDIRECT_CREATE_TO_LOGIN = f"{LOGIN_URL}?next={POST_CREATE_URL}"


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_user = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.user = User.objects.create_user(username=NOT_AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.auth_user,
            text=POST_TEXT,
            group=cls.group,
        )
        cls.PROFFILE_URL = reverse("posts:profile", args=[AUTHOR_USERNAME])
        cls.POST_DETAIL_URL = reverse("posts:post_detail", args=[cls.post.id])
        cls.POST_EDIT_URL = reverse("posts:post_edit", args=[cls.post.id])
        cls.FOLLOW_REDIRECT_EDIT_TO_LOGIN = \
            f"{LOGIN_URL}?next={cls.POST_EDIT_URL}"
        cls.FOLLOW_REDIRECT_CREATE_TO_LOGIN = \
            f"{LOGIN_URL}?next={POST_CREATE_URL}"

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_post_author = Client()
        self.authorized_client_post_author.force_login(self.auth_user)

    def test_urls_exists_at_desired_locations(self):
        """Проверка доступности URL."""
        urls = [
            INDEX_URL,
            GROUP_LIST_URL,
            self.PROFFILE_URL,
            self.POST_DETAIL_URL,
            POST_CREATE_URL,
            self.POST_EDIT_URL,
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(
                    self.authorized_client_post_author.get(
                        url).status_code, 200)

    def test_post_create_or_edit_redirect_login(self):
        """Возвращает HTTP status code 302
        для неавторизированного пользователя.
        """
        urls = [POST_CREATE_URL, self.POST_EDIT_URL]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    302)

    def test_post_create_or_edit_redirect_login(self):
        """Перенаправляет анонимного пользователя и не автора поста"""
        urls = [
            [self.guest_client, POST_CREATE_URL,
                FOLLOW_REDIRECT_CREATE_TO_LOGIN],
            [self.guest_client, self.POST_EDIT_URL,
                self.FOLLOW_REDIRECT_EDIT_TO_LOGIN],
            [self.authorized_client, self.POST_EDIT_URL,
                self.POST_DETAIL_URL],
        ]
        for client, url, redirect_url in urls:
            with self.subTest(value=redirect_url):
                self.assertRedirects(
                    client.get(url, follow=True),
                    redirect_url)

    def test_urls_uses_correct_template(self):
        """URL-адреса используют соответствующие шаблоны."""
        template_url_names = {
            INDEX_URL: "posts/index.html",
            GROUP_LIST_URL: "posts/group_list.html",
            self.PROFFILE_URL: "posts/profile.html",
            self.POST_DETAIL_URL: "posts/post_detail.html",
            POST_CREATE_URL: "posts/create_post.html",
            self.POST_EDIT_URL: "posts/create_post.html",
        }
        for address, template in template_url_names.items():
            with self.subTest(address=address):
                self.assertTemplateUsed(
                    self.authorized_client_post_author.get(address), template
                )
