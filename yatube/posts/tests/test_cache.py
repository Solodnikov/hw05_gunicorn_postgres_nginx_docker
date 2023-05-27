import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class CacheViewsTest(TestCase):
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

        settings.MEDIA_ROOT = TEMP_MEDIA_ROOT
        cls.author = User.objects.create_user(username='Тест_автор')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            group=cls.group,
            author=cls.author,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_cache_index(self):
        """Проверка хранения и обновления кэша для /."""
        response_first = self.authorized_client.get(reverse('posts:index'))
        posts = response_first.content
        self.post.delete()
        response_second = self.authorized_client.get(reverse('posts:index'))
        cache_posts = response_second.content
        self.assertEqual(
            posts,
            cache_posts,
            'Не возвращается кэшированная страница.'
        )

        cache.clear()
        response_without_cache = self.authorized_client.get(
            reverse('posts:index'))
        posts_without_cache = response_without_cache.content
        self.assertNotEqual(
            posts_without_cache,
            posts,
            'Не сбрасывается кэш.'
        )
