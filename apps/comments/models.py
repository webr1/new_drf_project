from django.db import models
from django.conf import settings
# Create your models here.
class Comment(models.Model):
    post = models.ForeignKey('main.Post',on_delete=models.CASCADE,related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="comments")
    parent = models.ForeignKey('self',on_delete=models.CASCADE,null=True,blank=True,related_name='replies')
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table= 'comments'
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post','created_at']),
            models.Index(fields=['author','-created_at']),
            models.Index(fields=['parent','created_at']),
        ]
    def __str__(self):
        # Добавим проверку на self.post, чтобы не упасть, если пост удален
        post_title = self.post.title if self.post else "Deleted Post"
        return f'Comment by {self.author.username} on {post_title}'
    
    @property
    def replies_count(self):
        # Считаем только активные ответы
        return self.replies.filter(is_active=True).count()
    
    @property
    def is_reply(self):
        # Если есть родитель — значит это ответ
        return self.parent is not None
        
