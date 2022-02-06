from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User
from yatube.settings import POSTS_ON_PAGE

SLUG = "testslug"
SECOND_SLUG = "slugslug"
AUTHOR_USERNAME = "Abraham"
NOT_AUTHOR_USERNAME = "Isaak"
POST_TEXT = "Тестовый текст, длинее 15 символов"
SECOND_TEXT = "Текст второго поста"
GROUP_TITLE = "Тестовая группа"
SECOND_GROUP_TITLE = "Вторая тестовая группа"
GROUP_DESCRIPTION = "Тестовое описание"
SECOND_GGROUP_DESCRIPTION = "Тестовое описание второй группы"
URL_POST_CREATE = "/create/"

URL_LOGIN = "/auth/login/"
FOLLOW_REDIRECT_CREATE_TO_LOGIN = f"{URL_LOGIN}?next={URL_POST_CREATE}"
URL_SECOND_GROUP_LIST = f"/group/{SECOND_SLUG}/"
URL_GROUP_LIST = reverse("posts:group_list", args=[SLUG])
URL_INDEX = reverse("posts:index")
URL_PROFFILE = reverse("posts:profile", args=[AUTHOR_USERNAME])


class YatubeViewsTest(TestCase):
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
            description=SECOND_GGROUP_DESCRIPTION
        )
        cls.post = Post.objects.create(
            author=cls.auth_user,
            text=POST_TEXT,
            group=cls.group,
        )
        cls.URL_POST_DETAIL = reverse("posts:post_detail", args=[cls.post.id])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_post_author = Client()
        self.authorized_client_post_author.force_login(self.auth_user)

    def test_group_page_show_correct_context(self):
        """При создании поста с группой он появляется на страницах: автора,
        главной, сообщества.
        Шаблоны сформированы с правильным контекстом.
        """
        adresses = [
            URL_INDEX,
            URL_GROUP_LIST,
            URL_PROFFILE,
            self.URL_POST_DETAIL
        ]
        for adress in adresses:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                if adress == self.URL_POST_DETAIL:
                    post = response.context["post"]
                    self.assertEquals(
                        Post.objects.get(id=1), response.context.get("post"))
                else:
                    post = response.context["page_obj"][0]
                    self.assertEqual(len(response.context["page_obj"]), 1)
                self.assertEqual(post.text, POST_TEXT)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.author, self.post.author)

    def test_post_is_not_displayed_in_someone_elses_group(self):
        """Пост неотображается в чужом сообществе."""
        response = self.authorized_client.get(URL_SECOND_GROUP_LIST)
        self.assertNotIn(Post.objects.get(id=1), response.context["page_obj"])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.BATCH_SIZE = 13
        cls.obj_list = [
            Post(author=cls.user, text=f"Текст {i}", group=cls.group)
            for i in range(cls.BATCH_SIZE)
        ]
        Post.objects.bulk_create(cls.obj_list)

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        """Паджинатор выводит по 10 постов на страницу."""
        POSTS_ON_PAGE_2 = 3
        set_pages = [
            [self.guest_client.get(URL_INDEX), POSTS_ON_PAGE],
            [self.guest_client.get(URL_PROFFILE), POSTS_ON_PAGE],
            [self.guest_client.get(URL_GROUP_LIST), POSTS_ON_PAGE],
            [self.guest_client.get(URL_INDEX + "?page=2"), POSTS_ON_PAGE_2],
            [self.guest_client.get(URL_PROFFILE + "?page=2"), POSTS_ON_PAGE_2],
            [self.guest_client.get(
                URL_GROUP_LIST + "?page=2"), POSTS_ON_PAGE_2],
        ]
        for page, exp_posts in set_pages:
            response = page
            self.assertEqual(len(response.context["page_obj"]), exp_posts)
