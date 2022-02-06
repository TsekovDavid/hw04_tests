from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Group, Post, User


AUTHOR_USERNAME = "Abraham"
NOT_AUTHOR_USERNAME = "Isaak"
POST_TEXT = "Тестовый текст"
GROUP_TITLE = "Тестовая группа"
SLUG = "testslug"
GROUP_DESCRIPTION = "Тестовое описание"
SECOND_GROUP_TITLE = "Вторая тестовая группа"
SECOND_SLUG = "new_group"
SECOND_GROUP_DESCRIPTION = "Тестовое описание второй группы"
PROFFILE_URL = reverse("posts:profile", args=[AUTHOR_USERNAME])
POST_CREATE_URL = reverse("posts:post_create")


class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=NOT_AUTHOR_USERNAME)
        cls.auth_user = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.group2 = Group.objects.create(
            title=SECOND_GROUP_TITLE,
            slug=SECOND_SLUG,
            description=SECOND_GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.auth_user,
            text=POST_TEXT,
            group=cls.group,
        )
        cls.POST_DETAIL_URL = reverse("posts:post_detail", args=[cls.post.id])
        cls.POST_EDIT_URL = reverse("posts:post_edit", args=[cls.post.id])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.auth_user)
        self.not_author_authorized_client = Client()
        self.not_author_authorized_client.force_login(self.user)

    def test_post_edit(self):
        """Валидная форма обновляет выбранный пост."""
        REFRESHED_TEXT = "Новый текст для поста"
        post_count = Post.objects.count()
        form_data = {
            "text": REFRESHED_TEXT,
            "group": self.group2.id
        }
        self.authorized_client.post(
            self.POST_EDIT_URL, data=form_data, follow=True)
        # Обновляем post методом refresh_from_db()
        # post.refresh_from_db()
        extract_last_post = Post.objects.last()
        self.assertNotEqual(
            extract_last_post.text,
            self.post.text,
            "Пост не изменился")
        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"],
                group=form_data["group"],
                author=self.post.author
            ).exists(),
            "Пост с обновленными данными не найден"
        )
        self.assertRedirects(
            self.not_author_authorized_client.get(self.POST_EDIT_URL),
            self.POST_DETAIL_URL)
        self.assertEqual(
            post_count,
            Post.objects.count(),
            "Количество постов изменилось")

    def test_create_post_form(self):
        """Валидная форма создает новый пост."""
        NEW_POST_TEXT = "Тестовый текст 123"
        form_data = {
            "text": NEW_POST_TEXT,
            "group": self.group.id,
        }
        # Очищаем бд
        Post.objects.all().delete()
        # Создаем новый пост, он будет  1 единственный в бд
        response = self.authorized_client.post(POST_CREATE_URL, data=form_data)
        self.assertRedirects(response, PROFFILE_URL)
        self.assertTrue(Post.objects.filter(
            text=form_data["text"]).exists())
        self.assertTrue(Post.objects.filter(
            group=form_data["group"]).exists())
        self.assertTrue(Post.objects.filter(
            author=self.post.author).exists())
        self.assertEqual(
            Post.objects.count(), 1, "Количество новых постов не равно одному")

    def test_form_post_create_and_post_edit(self):
        """Формы создания и редкатирования поста корректны."""
        urls = (self.POST_EDIT_URL, POST_CREATE_URL)
        for url in urls:
            response = self.authorized_client.get(url)
            form_fields = {
                "text": forms.fields.CharField,
                "group": forms.fields.ChoiceField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get("form").fields.get(value)
                    self.assertIsInstance(form_field, expected)
