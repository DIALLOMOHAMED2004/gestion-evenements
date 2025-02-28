from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from authentification.models import User
from events.models import Event, Category, EventRegistration

class EventViewsTest(TestCase):
    def setUp(self):
        # Créer un client pour les tests
        self.client = Client()
        
        # Créer un organisateur
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Organizer',
            role=User.Role.ORGANIZER
        )
        
        # Créer un participant
        self.participant = User.objects.create_user(
            username='participant',
            email='participant@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Participant',
            role=User.Role.PARTICIPANT
        )
        
        # Créer une catégorie
        self.category = Category.objects.create(name='Test Category')
        
        # Créer un événement
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

    def test_event_list_view(self):
        """Test la vue de liste des événements"""
        # Connecter l'utilisateur
        login_success = self.client.login(username='participant', password='testpass123')
        self.assertTrue(login_success)
        
        # Accéder à la page de liste
        response = self.client.get(reverse('events:event_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/event_list.html')
        self.assertContains(response, 'Test Event')

    def test_event_detail_view(self):
        """Test la vue de détail d'un événement"""
        # Connecter l'utilisateur
        login_success = self.client.login(username='participant', password='testpass123')
        self.assertTrue(login_success)
        
        # Accéder à la page de détail
        response = self.client.get(reverse('events:event_detail', args=[self.event.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/event_detail.html')
        self.assertContains(response, self.event.title)
        self.assertContains(response, self.event.description)

    def test_create_event_view(self):
        """Test la création d'un événement"""
        # Connecter l'organisateur
        login_success = self.client.login(username='organizer', password='testpass123')
        self.assertTrue(login_success)
        
        # Données pour créer un événement
        event_data = {
            'title': 'New Event',
            'description': 'New Description',
            'location': 'New Location',
            'start_date': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'end_date': (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            'available_seats': 50,
            'event_type': Event.EventType.PAID,
            'ticket_price': '75.00',
            'category': self.category.id,
            'visibility': 'public'
        }
        
        # Envoyer la requête POST
        response = self.client.post(reverse('events:create_event'), event_data)
        
        # Vérifier que l'événement a été créé
        self.assertTrue(Event.objects.filter(title='New Event').exists())
        
        # Vérifier la redirection
        new_event = Event.objects.get(title='New Event')
        self.assertRedirects(response, reverse('events:event_detail', args=[new_event.id]))

    def test_event_registration_view(self):
        """Test l'inscription à un événement"""
        # Connecter le participant
        login_success = self.client.login(username='participant', password='testpass123')
        self.assertTrue(login_success)
        
        # Envoyer la requête POST pour s'inscrire
        response = self.client.post(reverse('events:event_register', args=[self.event.id]))
        
        # Vérifier que l'inscription a été créée
        self.assertTrue(
            EventRegistration.objects.filter(
                event=self.event,
                participant=self.participant
            ).exists()
        )
        
        # Vérifier la redirection
        self.assertRedirects(response, reverse('events:event_detail', args=[self.event.id]))

    def test_dashboard_view(self):
        """Test la vue du tableau de bord"""
        # Connecter l'organisateur
        login_success = self.client.login(username='organizer', password='testpass123')
        self.assertTrue(login_success)
        
        # Accéder au tableau de bord
        response = self.client.get(reverse('events:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/dashboard.html')

    def test_edit_event_view(self):
        """Test la modification d'un événement"""
        # Connecter l'organisateur
        login_success = self.client.login(username='organizer', password='testpass123')
        self.assertTrue(login_success)
        
        # Données pour modifier l'événement
        updated_data = {
            'title': 'Updated Event',
            'description': 'Updated Description',
            'location': 'Updated Location',
            'start_date': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'end_date': (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            'available_seats': 75,
            'event_type': Event.EventType.PAID,
            'ticket_price': '100.00',
            'category': self.category.id,
            'visibility': 'public'
        }
        
        # Envoyer la requête POST
        response = self.client.post(
            reverse('events:edit_event', args=[self.event.id]),
            updated_data
        )
        
        # Rafraîchir l'événement depuis la base de données
        self.event.refresh_from_db()
        
        # Vérifier les modifications
        self.assertEqual(self.event.title, 'Updated Event')
        self.assertEqual(self.event.description, 'Updated Description')
        self.assertEqual(self.event.available_seats, 75)

    def test_delete_event_view(self):
        """Test la suppression d'un événement"""
        # Connecter l'organisateur
        login_success = self.client.login(username='organizer', password='testpass123')
        self.assertTrue(login_success)
        
        # Envoyer la requête POST pour supprimer
        response = self.client.post(reverse('events:delete_event', args=[self.event.id]))
        
        # Vérifier que l'événement a été supprimé
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())
        
        # Vérifier la redirection
        self.assertRedirects(response, reverse('events:event_list'))

    def test_unauthorized_access(self):
        """Test l'accès non autorisé"""
        # Connecter le participant
        self.client.login(email='participant@test.com', password='testpass123')
        
        # Essayer d'accéder à la création d'événement
        response = self.client.get(reverse('events:create_event'))
        self.assertEqual(response.status_code, 302)  # Redirection
        
        # Essayer d'accéder au tableau de bord
        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirection
