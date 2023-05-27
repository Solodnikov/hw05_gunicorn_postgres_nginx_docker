import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.user = User.objects.create_user(username='auth')
        cls.user_nonauth = User.objects.create_user(username='nonauth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый текст',
            image=cls.uploaded
        )

        cls.group_next = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-next',
            description='Тестовое описание 2',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_context(self):
        """Проверка контекста index, group_list, profile."""
        data_url = (
            (reverse('posts:index')),
            (reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug})),
            (reverse('posts:profile', args=(self.post.author,))),
        )
        for page in data_url:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertIn(
                    self.post,
                    response.context['page_obj'])

    def test_group_list_do_not_show_incorrect_context(self):
        """Пост группы не выводится на странице другой группы."""
        response = self.guest_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group_next.slug}
            ))
        self.assertNotIn(
            self.post,
            response.context['page_obj'])

    def test_object_group_list(self):
        page = reverse('posts:group_list',
                       kwargs={'slug': self.group.slug})
        response = self.guest_client.get(page)
        self.assertEqual(self.group, response.context.get('group'))

    def test_object_profile(self):
        page = reverse('posts:profile', args=(self.post.author,))
        response = self.guest_client.get(page)
        self.assertEqual(self.post.author, response.context.get('author'))

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context.get('post'), self.post)

    def test_create_edit_show_correct_context(self):
        """Шаблон create_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertEqual(response.context['form'].instance, self.post)

    def test_create_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:create_post'))
        self.assertIsInstance(response.context['form'], PostForm)

    def test_follow_user_another(self):
        """Follow на другого пользователя работает корректно"""
        self.authorized_client.force_login(self.user_nonauth)
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user.username}))
        follow_exist = Follow.objects.filter(
            user=self.user_nonauth,
            author=self.user).exists()
        self.assertTrue(follow_exist)

    def test_follow_on_author(self):
        """Follow на себя работает корректно"""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user.username}))
        follow_exist = Follow.objects.filter(
            user=self.user,
            author=self.user).exists()
        self.assertFalse(follow_exist)

    def test_unfollow_user_another(self):
        """Unfollow от другого пользователя работает корректно"""
        self.authorized_client.force_login(self.user_nonauth)
        Follow.objects.create(
            user=self.user_nonauth,
            author=self.user,
        )
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user.username}))
        follow_exist = Follow.objects.filter(
            user=self.user_nonauth,
            author=self.user).exists()
        self.assertFalse(follow_exist)

    def test_new_post_follow_index_show_correct_context_nonauth(self):
        """Новая запись автора появляется в ленте подписчиков"""
        self.authorized_client.force_login(self.user_nonauth)
        Follow.objects.create(
            user=self.user_nonauth,
            author=self.user,
        )
        response = self.authorized_client.get(
            reverse(('posts:follow_index'))
        )
        self.assertIn(
            self.post,
            response.context['page_obj'])

    def test_new_post_follow_index_show_correct_context_auth(self):
        Follow.objects.create(
            user=self.user_nonauth,
            author=self.user,
        )
        response = self.authorized_client.get(
            reverse(('posts:follow_index'))
        )
        self.assertNotIn(
            self.post,
            response.context['page_obj'])
