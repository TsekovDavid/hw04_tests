from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_user = User.objects.create_user(username="testauth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="testslug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.auth_user,
            text="Тестовый текст, длинее 15 символов",
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username="HasNoName")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_post_author = Client()
        self.authorized_client_post_author.force_login(self.auth_user)

    def test_urls_exists_at_desired_locations(self):
        """Проверка доступности URL."""
        urls = [
            "/",
            "/group/testslug/",
            f"/profile/{self.auth_user}/",
            f"/posts/{self.post.id}/",
            "/create/",
            f"/posts/{self.post.id}/edit/",
            "/about/tech/",
            "/about/author/",
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client_post_author.get(url)
                self.assertEqual(response.status_code, 200)

    def test_post_create_url_redirect_anonymous_on_admin_login(self):
        """Перенаправляет анонимного пользователя /create/"""
        response = self.guest_client.get("/create/", follow=True)
        self.assertRedirects(response, ("/auth/login/?next=/create/"))

    def test_post_edit_url_redirect_anonymous_on_admin_login(self):
        """Перенаправляет анонимного пользователя и не автора поста
        /posts/post.id/edit.
        """
        response = self.guest_client.get(
            f"/posts/{self.post.id}/edit/", follow=True
        )
        self.assertRedirects(
            response, (f"/auth/login/?next=/posts/{self.post.id}/edit/")
        )
        response = self.authorized_client.get(f"/posts/{self.post.id}/edit")
        self.assertEqual(response.status_code, 301)

    def test_urls_uses_correct_template(self):
        """URL-адреса используют соответствующие шаблоны."""
        templates_url_names = {
            "/": "posts/index.html",
            "/group/testslug/": "posts/group_list.html",
            f"/profile/{self.auth_user}/": "posts/profile.html",
            f"/posts/{self.post.id}/": "posts/post_detail.html",
            "/create/": "posts/create_post.html",
            f"/posts/{self.post.id}/edit/": "posts/create_post.html",
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_post_author.get(address)
                self.assertTemplateUsed(response, template)
