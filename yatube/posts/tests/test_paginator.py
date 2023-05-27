from math import ceil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаем автора и группу."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.POSTS_FOR_TEST = 31
        cls.PAGES_COUNT = ceil(
            cls.POSTS_FOR_TEST / settings.POSTS_ON_PAGE
        )

        Post.objects.bulk_create([Post(
            text=f"test-text {post}",
            group=cls.group,
            author=cls.user) for post in range(cls.POSTS_FOR_TEST)])

    def setUp(self):
        self.client = Client()

    def test_pages_pagination(self):
        """Проверяет пагинацию."""
        if self.POSTS_FOR_TEST >= settings.POSTS_ON_PAGE:
            FIRST_PAGE_POSTS = settings.POSTS_ON_PAGE
        else:
            FIRST_PAGE_POSTS = self.POSTS_FOR_TEST

        LAST_PAGE_POSTS = self.POSTS_FOR_TEST - (
            (self.PAGES_COUNT - 1) * settings.POSTS_ON_PAGE)

        urls_data = (
            ((reverse('posts:index') + '?page=1'), FIRST_PAGE_POSTS),
            ((reverse('posts:group_list', args=[self.group.slug])
             + '?page=1'), FIRST_PAGE_POSTS),
            ((reverse('posts:profile', args=[self.user])
             + '?page=1'), FIRST_PAGE_POSTS),

            ((reverse('posts:index') + f'?page={self.PAGES_COUNT}'),
             LAST_PAGE_POSTS),
            ((reverse('posts:group_list', args=[self.group.slug])
             + f'?page={self.PAGES_COUNT}'), LAST_PAGE_POSTS),
            ((reverse('posts:profile', args=[self.user])
             + f'?page={self.PAGES_COUNT}'), LAST_PAGE_POSTS)
        )

        for page_url, posts_on_page in urls_data:
            with self.subTest(page_url=page_url):
                response = self.client.get(page_url)
                self.assertEqual(
                    len(response.context['page_obj']),
                    posts_on_page)
