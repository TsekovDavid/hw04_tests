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
POST_CREATE_URL = reverse("posts:post_create")
LOGIN_URL = reverse("users:login")
FOLLOW_REDIRECT_CREATE_TO_LOGIN = f"{LOGIN_URL}?next={POST_CREATE_URL}"
SECOND_GROUP_LIST_URL = reverse("posts:group_list", args=[SECOND_SLUG])
GROUP_LIST_URL = reverse("posts:group_list", args=[SLUG])
INDEX_URL = reverse("posts:index")
PROFFILE_URL = reverse("posts:profile", args=[AUTHOR_USERNAME])


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
        cls.POST_DETAIL_URL = reverse("posts:post_detail", args=[cls.post.id])

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
            INDEX_URL,
            GROUP_LIST_URL,
            PROFFILE_URL,
            self.POST_DETAIL_URL
        ]
        for adress in adresses:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                if adress == self.POST_DETAIL_URL:
                    self.assertEqual(
                        self.post, response.context["post"])
                elif adress == PROFFILE_URL:
                    self.assertEqual(
                        response.context["author"],
                        self.post.author)
                elif adress == GROUP_LIST_URL:
                    self.assertEqual(
                        response.context["group"],
                        self.post.group)
                else:
                    post = response.context["page_obj"][0]
                    self.assertEqual(len(response.context["page_obj"]), 1)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(self.auth_user, self.post.author)

    def test_post_is_not_displayed_in_someone_elses_group(self):
        """Пост неотображается в чужом сообществе."""
        response = self.authorized_client.get(SECOND_GROUP_LIST_URL)
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
        cls.BATCH_SIZE = POSTS_ON_PAGE + 3
        Post.objects.bulk_create(
            Post(author=cls.user, text=f"Текст {i}", group=cls.group)
            for i in range(cls.BATCH_SIZE))

    def setUp(self):
        self.guest_client = Client()

    def test_page_contains_the_correct_number_of_posts(self):
        """Паджинатор выводит правильное количество постов на страницу."""
        POSTS_ON_PAGE_2 = self.BATCH_SIZE - POSTS_ON_PAGE
        set = [
            [INDEX_URL, POSTS_ON_PAGE],
            [PROFFILE_URL, POSTS_ON_PAGE],
            [GROUP_LIST_URL, POSTS_ON_PAGE],
            [INDEX_URL + "?page=2", POSTS_ON_PAGE_2],
            [PROFFILE_URL + "?page=2", POSTS_ON_PAGE_2],
            [GROUP_LIST_URL + "?page=2", POSTS_ON_PAGE_2],
        ]
        for url, posts_count in set:
            response = self.guest_client.get(url)
            self.assertEqual(len(response.context["page_obj"]), posts_count)
