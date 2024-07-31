from django.db import models

# Create your models here.
class Genre(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class BlacklistedToken(models.Model):
    token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)