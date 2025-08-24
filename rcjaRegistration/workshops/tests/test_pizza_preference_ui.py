from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from events.models import Event, Year, Division, AvailableDivision
from workshops.models import WorkshopAttendee
from regions.models import State
from schools.models import School

User = get_user_model()


class PizzaPreferenceUITests(TestCase):
    def setUp(self):
        # Create test data
        self.client = Client()
        
        # Create state
        self.state = State.objects.create(
            name='Test State',
            abbreviation='TS',
            typeCompetition=True,
            typeUserRegistration=True,
            typeWebsite=True
        )
        
        # Create year
        self.year = Year.objects.create(year=2024, displayEventsOnWebsite=True)
        
        # Create division
        self.division = Division.objects.create(name='Test Division')
        
        # Create user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            homeState=self.state
        )
        
        # Create school
        self.school = School.objects.create(
            name='Test School',
            state=self.state
        )
        
        # Create events with different showPizzaPreference settings
        self.event_with_pizza = Event.objects.create(
            year=self.year,
            state=self.state,
            name='Workshop with Pizza',
            eventType='workshop',
            status='published',
            startDate='2024-06-01',
            endDate='2024-06-01',
            registrationsOpenDate='2024-05-01',
            registrationsCloseDate='2024-05-31',
            showPizzaPreference=True,
            directEnquiriesTo=self.user
        )
        
        self.event_without_pizza = Event.objects.create(
            year=self.year,
            state=self.state,
            name='Workshop without Pizza',
            eventType='workshop',
            status='published',
            startDate='2024-06-01',
            endDate='2024-06-01',
            registrationsOpenDate='2024-05-01',
            registrationsCloseDate='2024-05-31',
            showPizzaPreference=False,
            directEnquiriesTo=self.user
        )
        
        # Create available divisions
        AvailableDivision.objects.create(
            event=self.event_with_pizza,
            division=self.division
        )
        AvailableDivision.objects.create(
            event=self.event_without_pizza,
            division=self.division
        )
        
        # Login the user
        self.client.login(email='test@example.com', password='testpass123')

    def test_pizza_preference_field_shown_when_enabled(self):
        """Test that pizza preference field is shown when event.showPizzaPreference is True"""
        url = reverse('workshops:create', kwargs={'eventID': self.event_with_pizza.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pizza preference:')
        self.assertContains(response, 'pizzaPreference')

    def test_pizza_preference_field_hidden_when_disabled(self):
        """Test that pizza preference field is hidden when event.showPizzaPreference is False"""
        url = reverse('workshops:create', kwargs={'eventID': self.event_without_pizza.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Pizza preference:')
        self.assertNotContains(response, 'pizzaPreference')

    def test_pizza_preference_field_in_edit_form_when_enabled(self):
        """Test that pizza preference field is shown in edit form when enabled"""
        # Create an attendee
        attendee = WorkshopAttendee.objects.create(
            event=self.event_with_pizza,
            mentorUser=self.user,
            school=self.school,
            division=self.division,
            firstName='Test',
            lastName='User',
            yearLevel='10',
            attendeeType='student',
            gender='male'
        )
        
        url = reverse('workshops:details', kwargs={'attendeeID': attendee.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pizza preference:')
        self.assertContains(response, 'pizzaPreference')

    def test_pizza_preference_field_in_edit_form_when_disabled(self):
        """Test that pizza preference field is hidden in edit form when disabled"""
        # Create an attendee
        attendee = WorkshopAttendee.objects.create(
            event=self.event_without_pizza,
            mentorUser=self.user,
            school=self.school,
            division=self.division,
            firstName='Test',
            lastName='User',
            yearLevel='10',
            attendeeType='student',
            gender='male'
        )
        
        url = reverse('workshops:details', kwargs={'attendeeID': attendee.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Pizza preference:')
        self.assertNotContains(response, 'pizzaPreference')
