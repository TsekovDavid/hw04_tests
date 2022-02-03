from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class YatubeViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="NoName")
        cls.auth_user = User.objects.create_user(username="testuser")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="testslug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.auth_user,
            text="Тестовый пост 1",
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_post_author = Client()
        self.authorized_client_post_author.force_login(self.auth_user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": "testslug"}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": "testuser"}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": self.post.id}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": self.post.id}
            ): "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html",
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client_post_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_template_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:index"))
        first_post = response.context.get("page_obj")[0]
        post_author_0 = first_post.author.username
        post_text_0 = first_post.text
        post_group_0 = first_post.group.title
        self.assertEqual(post_author_0, "testuser")
        self.assertEqual(post_text_0, "Тестовый пост 1")
        self.assertEqual(post_group_0, "Тестовая группа")

    def test_template_group_page_show_correct_context(self):
        """При создании поста с группой он появляется на всех страницах,
        шаблоны сформированы с правильным контекстом.
        """
        adresses = [
            reverse("posts:index"),
            reverse("posts:group_list", kwargs={"slug": self.post.group.slug}),
            reverse(
                "posts:profile", kwargs={"username": self.auth_user.username}
            ),
        ]
        for adress in adresses:
            response = self.authorized_client.get(adress)
            first_post = response.context["page_obj"][0]
            post_text = first_post.text
            post_group = first_post.group.title
            post_author = first_post.author.username
            values = {
                post_text: self.post.text,
                post_group: self.post.group.title,
                post_author: self.post.author.username,
            }
            for key, value in values.items():
                with self.subTest(key=key):
                    self.assertEqual(key, value)

    def test_post_notexists_group_page(self):
        """Пост без/с иной группой не отображается на странице сообщества."""
        self.post2 = Post.objects.create(
            author=self.user,
            text="Тестовый пост 2 с автором NoName",
        )
        response = self.authorized_client.get("/group/testslug/")
        self.assertNotIn(Post.objects.get(id=2), response.context["page_obj"])

    def test_template_post_detail_show_correct_context(self):
        """Страница о посте выводит 1 пост по id."""
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        self.assertEquals(Post.objects.get(id=1), response.context.get("post"))

    def test_form_post_create_and_post_edit(self):
        """Форма создания поста корректна."""
        response = self.authorized_client.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_form_post_edit(self):
        response = self.authorized_client_post_author.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="testauth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="testslug",
            description="Тестовое описание",
        )
        cls.batch_size = 13
        cls.obj_list = [
            Post(author=cls.user, text=f"Текст {i}", group=cls.group)
            for i in range(cls.batch_size)
        ]
        Post.objects.bulk_create(cls.obj_list)

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        """Паджинатор выводит по 10 постов на страницу."""
        set_pages = [
            self.guest_client.get(reverse("posts:index")),
            self.guest_client.get(
                reverse("posts:profile", kwargs={"username": "testauth"})
            ),
            self.guest_client.get(
                reverse("posts:group_list", kwargs={"slug": "testslug"})
            ),
        ]
        for page in set_pages:
            response = page
            self.assertEqual(len(response.context["page_obj"]), 10)

    def test_second_page_contains_three_records(self):
        """Вывод оставшихся 3х постов"""
        set_pages = [
            self.guest_client.get(reverse("posts:index") + "?page=2"),
            self.guest_client.get(
                reverse("posts:profile", kwargs={"username": "testauth"})
                + "?page=2"
            ),
            self.guest_client.get(
                reverse("posts:group_list", kwargs={"slug": "testslug"})
                + "?page=2"
            ),
        ]
        for page in set_pages:
            response = page
            self.assertEqual(len(response.context["page_obj"]), 3)
