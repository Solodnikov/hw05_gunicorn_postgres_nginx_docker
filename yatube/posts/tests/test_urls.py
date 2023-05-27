from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class URLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.user = User.objects.create_user(
            username='not_auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        cache.clear()

    def test_urls_pages(self):
        """Доступность страниц"""
        self.authorized_client.force_login(self.author)

        status_data = (
            (reverse('posts:index'),
             HTTPStatus.OK, False),
            ((reverse('posts:group_list', kwargs={
                'slug': self.group.slug})),
                HTTPStatus.OK, False),
            ((reverse('posts:profile', kwargs={
                'username': self.post.author})),
                HTTPStatus.OK, False),
            ((reverse('posts:post_detail', kwargs={
                'post_id': self.post.id})),
                HTTPStatus.OK, False),
            ((reverse('posts:post_edit', kwargs={
                'post_id': self.post.id})),
                HTTPStatus.FOUND, False),
            (reverse('posts:create_post'),
             HTTPStatus.FOUND, False),
            ('/unexisting_page/', HTTPStatus.NOT_FOUND, False),
            ((reverse('posts:post_edit', kwargs={'post_id': self.post.id})),
             HTTPStatus.OK, True),
            (reverse('posts:create_post'), HTTPStatus.OK,
             True),
            (reverse('posts:create_post'), HTTPStatus.OK,
             True),
        )

        for page, expected_value, flag in status_data:
            with self.subTest(page=page):
                if flag:
                    response = self.authorized_client.get(page).status_code
                else:
                    response = self.guest_client.get(page).status_code
                self.assertEqual(response, expected_value)

    def test_redirect(self):
        """Страница перенаправит анонимного пользователя на страницу логина.
        Страница post_edit перенаправит не автора на страницу поста"""
        self.authorized_client.force_login(self.user)

        redirects_data = (
            (reverse('posts:post_edit',
             kwargs={'post_id': self.post.id}),
             reverse('login') + '?next='
             + reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
             False),
            (reverse('posts:create_post'),
             reverse('login') + '?next=' + reverse('posts:create_post'),
             False),
            (reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
             reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
             True),
        )

        for page, expected_value, flag in redirects_data:
            with self.subTest(page=page):
                if flag:
                    response = self.authorized_client.get(page, follow=True)
                else:
                    response = self.guest_client.get(page, follow=True)
                self.assertRedirects(response, expected_value)

    def test_pages_uses_correct_template(self):
        """URL-адреса использует соответствующий шаблон."""
        self.authorized_client.force_login(self.author)

        templates_data = (
            ((reverse('posts:index'), 'posts/index.html')),
            ((reverse('posts:group_list', kwargs={
                'slug': self.group.slug})), 'posts/group_list.html'),
            ((reverse('posts:profile', kwargs={
                'username': self.post.author})), 'posts/profile.html'),
            ((reverse('posts:post_detail', kwargs={
                'post_id': self.post.id})), 'posts/post_detail.html'),
            ((reverse('posts:post_edit', kwargs={
                'post_id': self.post.id})), 'posts/create_post.html'),
            (reverse('posts:create_post'), 'posts/create_post.html'),
        )
        for url, template in templates_data:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_pages_adres(self):
        """Адреса страниц соответствуют их именам."""
        templates_data = (
            (reverse('posts:index'), '/'),
            ((reverse('posts:group_list', kwargs={
                'slug': self.group.slug})), (f'/group/{self.group.slug}/')),
            ((reverse('posts:profile', kwargs={
                'username': self.post.author})
              ), (f'/profile/{self.post.author}/')),
            ((reverse('posts:post_detail', kwargs={
                'post_id': self.post.id})
              ), (f'/posts/{self.post.id}/')),
            ((reverse('posts:post_edit', kwargs={
                'post_id': self.post.id})
              ), (f'/posts/{self.post.id}/edit/')),
            (reverse('posts:create_post'), '/create/'),
        )

        for name, adress in templates_data:
            with self.subTest(name=name):
                self.assertEqual(name, adress)
