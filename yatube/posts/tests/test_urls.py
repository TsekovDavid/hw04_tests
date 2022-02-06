from django.test import Client, TestCase

from posts.models import Group, Post, User

SLUG = "testslug"
AUTHOR_USERNAME = "Abraham"
NOT_AUTHOR_USERNAME = "Isaak"
POST_TEXT = "Тестовый текст, длинее 15 символов"
GROUP_TITLE = "Тестовая группа"
GROUP_DESCRIPTION = "Тестовое описание"
URL_POST_DETAIL = "posts:post_detail"
URL_POST_CREATE = "/create/"
URL_INDEX = "/"
URL_GROUP_LIST = f"/group/{SLUG}/"
URL_PROFFILE = "posts:profile"
URL_LOGIN = "/auth/login/"
FOLLOW_REDIRECT_CREATE_TO_LOGIN = f"{URL_LOGIN}?next={URL_POST_CREATE}"


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
        cls.URL_PROFFILE = f"/profile/{cls.auth_user}/"
        cls.URL_POST_DETAIL = f"/posts/{cls.post.id}/"
        cls.URL_POST_EDIT = f"/posts/{cls.post.id}/edit/"
        cls.FOLLOW_REDIRECT_EDIT_TO_LOGIN = f"{URL_LOGIN}?next={cls.URL_POST_EDIT}"

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_post_author = Client()
        self.authorized_client_post_author.force_login(self.auth_user)

    def test_urls_exists_at_desired_locations(self):
        """Проверка доступности URL."""
        urls = [
            URL_INDEX,
            URL_GROUP_LIST,
            self.URL_PROFFILE,
            self.URL_POST_DETAIL,
            URL_POST_CREATE,
            self.URL_POST_EDIT,
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(
                    self.authorized_client_post_author.get(
                        url).status_code, 200)

    def test_post_create_or_edit_redirect_login(self):
        """Перенаправляет анонимного пользователя и не автора поста"""
        urls = [URL_POST_CREATE, self.URL_POST_EDIT]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    302)
        urls = [
            [self.guest_client, URL_POST_CREATE, FOLLOW_REDIRECT_CREATE_TO_LOGIN],
            [self.guest_client, self.URL_POST_EDIT, self.FOLLOW_REDIRECT_EDIT_TO_LOGIN],
            [self.authorized_client, self.URL_POST_EDIT, self.URL_POST_DETAIL]
        ]
        for client, url, redurl in urls:
            with self.subTest(value=url):
                self.assertRedirects(client.get(url, follow=True), redurl)

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
                self.assertTemplateUsed(
                    self.authorized_client_post_author.get(address), template
                )
