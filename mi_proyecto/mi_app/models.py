from django.db import models

# Create your models here.

class users(models.Model):
    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True)
    refresh_token = models.TextField()

    def __str__(self):
        return self.email