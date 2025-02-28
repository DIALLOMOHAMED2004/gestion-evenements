from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from decimal import Decimal
from authentification.models import User
from events.models import Event, Category, EventRegistration

class EventModelTests(TestCase):
    def setUp(self):
        # Créer un utilisateur organisateur
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Organizer',
            role=User.Role.ORGANIZER
        )
        
        # Créer une catégorie
        self.category = Category.objects.create(name='Test Category')
        
        # Créer un événement de base
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            location='Test Location',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=2),
            available_seats=100,
            event_type=Event.EventType.PAID,
            ticket_price=Decimal('50.00'),
            organizer=self.organizer,
            category=self.category
        )

    def test_event_creation(self):
        """Test la création d'un événement"""
        self.assertEqual(self.event.title, 'Test Event')
        self.assertEqual(self.event.available_seats, 100)
        self.assertEqual(self.event.ticket_price, Decimal('50.00'))

    def test_event_str_representation(self):
        """Test la représentation string d'un événement"""
        self.assertEqual(str(self.event), 'Test Event')

    def test_remaining_seats(self):
        """Test le calcul des places restantes"""
        # Créer un participant
        participant = User.objects.create_user(
            username='participant',
            email='participant@test.com',
            password='testpass123',
            role=User.Role.PARTICIPANT
        )
        
        # Créer une inscription
        EventRegistration.objects.create(
            event=self.event,
            participant=participant
        )
        
        self.assertEqual(self.event.remaining_seats(), 99)

    def test_is_full(self):
        """Test si l'événement est complet"""
        # Créer un événement avec une seule place
        small_event = Event.objects.create(
            title='Small Event',
            description='Test Description',
            location='Test Location',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=2),
            available_seats=1,
            organizer=self.organizer,
            category=self.category
        )
        
        # Créer un participant et l'inscrire
        participant = User.objects.create_user(
            username='participant',
            email='participant@test.com',
            password='testpass123',
            role=User.Role.PARTICIPANT
        )
        
        EventRegistration.objects.create(
            event=small_event,
            participant=participant
        )
        
        self.assertTrue(small_event.is_full())
        self.assertFalse(self.event.is_full())

    def test_invalid_dates(self):
        """Test la validation des dates"""
        # Tenter de créer un événement avec une date de fin antérieure à la date de début
        with self.assertRaises(ValidationError):
            invalid_event = Event(
                title='Invalid Event',
                description='Test Description',
                location='Test Location',
                start_date=timezone.now() + timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                available_seats=100,
                organizer=self.organizer,
                category=self.category
            )
            invalid_event.full_clean()

    def test_total_revenue(self):
        """Test le calcul du revenu total"""
        # Créer deux participants
        participant1 = User.objects.create_user(
            username='participant1',
            email='participant1@test.com',
            password='testpass123',
            role=User.Role.PARTICIPANT
        )
        participant2 = User.objects.create_user(
            username='participant2',
            email='participant2@test.com',
            password='testpass123',
            role=User.Role.PARTICIPANT
        )
        
        # Créer deux inscriptions payées
        EventRegistration.objects.create(
            event=self.event,
            participant=participant1,
            payment_status=True
        )
        EventRegistration.objects.create(
            event=self.event,
            participant=participant2,
            payment_status=True
        )
        
        # Le revenu total devrait être 100.00 (2 * 50.00)
        self.assertEqual(self.event.total_revenue(), Decimal('100.00'))

class CategoryModelTests(TestCase):
    def test_category_creation(self):
        """Test la création d'une catégorie"""
        category = Category.objects.create(name='Test Category')
        self.assertEqual(str(category), 'Test Category')

class EventRegistrationModelTests(TestCase):
    def setUp(self):
        # Configuration de base pour les tests d'inscription
        self.organizer = User.objects.create_user(
            username='organizer_reg',
            email='organizer@test.com',
            password='testpass123',
            role=User.Role.ORGANIZER
        )
        self.participant = User.objects.create_user(
            username='participant',
            email='participant@test.com',
            password='testpass123',
            role=User.Role.PARTICIPANT
        )
        self.category = Category.objects.create(name='Test Category')
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            location='Test Location',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=2),
            available_seats=100,
            organizer=self.organizer,
            category=self.category
        )

    def test_registration_creation(self):
        """Test la création d'une inscription"""
        registration = EventRegistration.objects.create(
            event=self.event,
            participant=self.participant
        )
        self.assertFalse(registration.payment_status)
        self.assertEqual(registration.event, self.event)
        self.assertEqual(registration.participant, self.participant)

    def test_unique_registration(self):
        """Test qu'un participant ne peut s'inscrire qu'une seule fois"""
        EventRegistration.objects.create(
            event=self.event,
            participant=self.participant
        )
        
        # Tenter de créer une deuxième inscription pour le même participant
        with self.assertRaises(Exception):
            EventRegistration.objects.create(
                event=self.event,
                participant=self.participant
            )
