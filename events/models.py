from django.db import models
from django.core.validators import MinValueValidator
from authentification.models import User
from decimal import Decimal

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

import uuid

class Event(models.Model):
    class EventType(models.TextChoices):
        FREE = 'FREE', 'Gratuit'
        PAID = 'PAID', 'Payant'

    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(verbose_name="Description")
    image = models.ImageField(upload_to='event_images/', null=True, blank=True, verbose_name="Image")
    location = models.CharField(max_length=200, verbose_name="Lieu")
    start_date = models.DateTimeField(verbose_name="Date de début")
    end_date = models.DateTimeField(verbose_name="Date de fin")
    available_seats = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Places disponibles"
    )
    event_type = models.CharField(
        max_length=4,
        choices=EventType.choices,
        default=EventType.FREE,
        verbose_name="Type d'événement"
    )
    ticket_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Prix du billet"
    )
    organizer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organized_events',
        verbose_name="Organisateur"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='events'
    )
    is_public = models.BooleanField(default=True, verbose_name="Événement public")
    invitation_link = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def generate_invitation_link(self):
        self.invitation_link = uuid.uuid4()
        self.save()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_private = models.BooleanField(default=False, verbose_name="Événement privé")
    

    class Meta:
        ordering = ['-start_date']
        verbose_name = "Événement"
        verbose_name_plural = "Événements"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_date <= self.start_date:
            raise ValidationError('La date de fin doit être postérieure à la date de début.')

    def __str__(self):
        return self.title

    def remaining_seats(self):
        return self.available_seats - self.registrations.count()

    def is_full(self):
        return self.remaining_seats() <= 0

    def is_upcoming(self):
        from django.utils import timezone
        return self.start_date > timezone.now()
    
    def is_finished(self):
        from django.utils import timezone
        return self.end_date < timezone.now()
    
    def is_ongoing(self):
        from django.utils import timezone
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    def total_revenue(self):
        if self.event_type == self.EventType.FREE:
            return Decimal('0.00')
        paid_registrations = self.registrations.filter(payment_status=True).count()
        return self.ticket_price * Decimal(str(paid_registrations))
    
    def paid_tickets_count(self):
        return self.registrations.filter(payment_status=True).count()
    
    def registration_rate(self):
        if self.available_seats == 0:
            return 0
        return (self.registrations.count() / self.available_seats) * 100

class EventRegistration(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='registrations',
        verbose_name="Événement"
    )
    participant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='event_registrations',
        verbose_name="Participant"
    )
    registration_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.BooleanField(default=False, verbose_name="Paiement effectué")

    class Meta:
        unique_together = ['event', 'participant']
        verbose_name = "Inscription"
        verbose_name_plural = "Inscriptions"

    def __str__(self):
        return f"{self.participant.username} - {self.event.title}"
