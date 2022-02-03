from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_user = User.objects.create_user(username="testuser")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="testslug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.auth_user,
            text="Тестовый текст",
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.auth_user)

    def test_post_edit(self):
        """Валидная форма обновляет выбранный пост."""
        post = self.post
        form_data = {
            "text": "Новый текст для поста",
        }
        response = self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": post.id}),
            data=form_data,
        )
        # Обновляем post методом refresh_from_db()
        post.refresh_from_db()
        expected_object_text = post.text
        print(reverse("posts:post_detail", kwargs={"post_id": post.id}))
        self.assertRedirects(
            response, reverse("posts:post_detail", kwargs={"post_id": post.id})
        )
        self.assertEqual(expected_object_text, "Новый текст для поста")

    def test_create_post_form(self):
        """Валидная форма создает новый пост."""
        posts_count = Post.objects.count()
        form_data = {
            "text": "Тестовый текст 123",
            "group": self.group.id,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"),
            data=form_data,
        )
        self.assertRedirects(
            response,
            reverse(
                "posts:profile", kwargs={"username": self.auth_user.username}
            ),
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text="Тестовый текст 123",
            ).exists()
        )
