from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse

# Create your models here.
class Category(models.Model):
    """
    Модель категории для постов блога.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PostManager(models.Manager):
    """Менеджер для модели Post с дополнительными методами"""

    def pusblished(self):
        return self.filter(status='published')
    
    def pinned_posts(self):
        """Возвращает закрепленные посты в порядке закрепления"""
        return self.filter(
            pin_info__isnull=False,
            pin_info__user__subscription__status='active',
            pin_info__user__subscription__end_date__gt=models.functions.Now(),
            status='published'
        ).select_related(
            'pin_info', 'pin_info__user', 'pin_info__user__subcription'
        ).order_by('pin_info__pinned_at')
    
    def regular_posts(self):
        """Возвращает обычные (незакрепленные) посты"""
        return self.filter(pin_info__isnull=True, status='published')
    
    def with_subscription_info(self):
        """Добавляет информацию о подписке автора"""
        return self.select_related(
            'author', 'author__subscription', 'category'
        ).prefetch_related('pin_info')


class Post(models.Model):
    """
    Модель поста блога c поддержкой закрепления.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='published'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)

    objects = PostManager()

    class Meta:
        db_table = 'posts'
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'slug': self.slug})

    @property
    def comments_count(self):
        """Количество комментариев к посту"""
        return self.comments.filter(is_active=True).count()
