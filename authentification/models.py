from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    class Role(models.TextChoices):
        ORGANIZER = 'ORGANIZER', 'Organisateur'
        PARTICIPANT = 'PARTICIPANT', 'Participant'

    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.PARTICIPANT,
    )

    def is_organizer(self):
        return self.role == self.Role.ORGANIZER

    def is_participant(self):
        return self.role == self.Role.PARTICIPANT

    def get_role_display_name(self):
        return self.get_role_display()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f'Profil de {self.user.username}'
