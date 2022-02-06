from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Group, Post, User

CONST_SLUG = "testslug"
AUTHOR_USERNAME = "Abraham"
NOT_AUTHOR_USERNAME = "Isaak"
POST_TEXT = "Тестовый текст"
GROUP_TITLE = "Тестовая группа"
GROUP_DESCRIPTION = "Тестовое описание"
URL_POST_EDIT = "posts:post_edit"
URL_POST_DETAIL = "posts:post_detail"
URL_PROFFILE = reverse("posts:profile", args=[AUTHOR_USERNAME])
URL_POST_CREATE = reverse("posts:post_create")


class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=NOT_AUTHOR_USERNAME)
        cls.auth_user = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=CONST_SLUG,
            description=GROUP_DESCRIPTION,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.auth_user)
        self.not_author_authorized_client = Client()
        self.not_author_authorized_client.force_login(self.user)
        # Пост в сетапе, что бы после очистки бд, он вновь создался
        self.post = Post.objects.create(
            author=self.auth_user,
            text=POST_TEXT,
            group=self.group,
        )

    def test_post_edit(self):
        """Валидная форма обновляет выбранный пост."""
        REFRESHED_TEXT = "Новый текст для поста"

        post = self.post
        form_data = {
            "text": REFRESHED_TEXT,
            "group": self.group.id,
        }
        response = self.authorized_client.post(
            reverse(URL_POST_EDIT, args=[post.id]),
            data=form_data,
        )
        # Обновляем post методом refresh_from_db()
        post.refresh_from_db()
        self.assertRedirects(
            response, reverse(URL_POST_DETAIL, args=[post.id])
        )
        self.assertTrue(
            Post.objects.filter(
                text=REFRESHED_TEXT,
                group=self.group.id,
                author=self.auth_user
            ).exists()
        )
        # Проверяем редактирование поста не автором
        response = self.not_author_authorized_client.get(
            reverse(URL_POST_EDIT, args=[post.id])
        )
        self.assertRedirects(
            response, reverse(URL_POST_DETAIL, args=[post.id]))

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
        response = self.authorized_client.post(URL_POST_CREATE, data=form_data)
        self.assertRedirects(response, URL_PROFFILE)
        self.assertTrue(
            Post.objects.filter(
                text=NEW_POST_TEXT,
                group=self.group.id,
                author=self.auth_user
            ).exists()
        )

    def test_form_post_create_and_post_edit(self):
        """Форма создания поста корректна."""
        response = self.authorized_client.get(URL_POST_CREATE)
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_form_post_edit(self):
        """Форма редактирования поста корректна"""
        response = self.authorized_client.get(
            reverse(URL_POST_EDIT, args=[self.post.id])
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)
