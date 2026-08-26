from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse

from common.baseTests import createEvents, createSchools, createStates, createUsers
from coordination.models import Coordinator


class EventDetailsInvoiceButtonBase:
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createSchools(cls)
        createEvents(cls)

    def event_details_url(self):
        return reverse('events:details', kwargs={'eventID': self.state1_openCompetition.id})

    def login(self, email):
        self.client.login(request=HttpRequest(), email=email, password=self.password)


class TestEventDetailsInvoiceButton_FullCoordinator(EventDetailsInvoiceButtonBase, TestCase):
    def test_shows_view_invoices(self):
        self.login(self.email_user_state1_fullcoordinator)
        response = self.client.get(self.event_details_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View Invoices')
        self.assertTrue(response.context['hasInvoiceViewPermissions'])


class TestEventDetailsInvoiceButton_ViewCoordinator(EventDetailsInvoiceButtonBase, TestCase):
    def test_shows_view_invoices(self):
        self.login(self.email_user_state1_viewcoordinator)
        response = self.client.get(self.event_details_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View Invoices')
        self.assertTrue(response.context['hasInvoiceViewPermissions'])


class TestEventDetailsInvoiceButton_BillingManager(EventDetailsInvoiceButtonBase, TestCase):
    def test_shows_view_invoices(self):
        self.coord_state1_fullcoordinator.permissionLevel = 'billingmanager'
        self.coord_state1_fullcoordinator.save()
        self.login(self.email_user_state1_fullcoordinator)
        response = self.client.get(self.event_details_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View Invoices')
        self.assertTrue(response.context['hasInvoiceViewPermissions'])


class TestEventDetailsInvoiceButton_EventManager(EventDetailsInvoiceButtonBase, TestCase):
    def test_hides_view_invoices(self):
        self.coord_state1_fullcoordinator.permissionLevel = 'eventmanager'
        self.coord_state1_fullcoordinator.save()
        self.login(self.email_user_state1_fullcoordinator)
        response = self.client.get(self.event_details_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Administration')
        self.assertNotContains(response, 'View Invoices')
        self.assertFalse(response.context['hasInvoiceViewPermissions'])


class TestEventDetailsInvoiceButton_Superuser(EventDetailsInvoiceButtonBase, TestCase):
    def test_shows_view_invoices(self):
        self.login(self.email_user_state1_super1)
        response = self.client.get(self.event_details_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View Invoices')
        self.assertTrue(response.context['hasInvoiceViewPermissions'])


class TestEventDetailsInvoiceButton_Mentor(EventDetailsInvoiceButtonBase, TestCase):
    def test_hides_view_invoices(self):
        self.login(self.email_user_state1_school1_mentor1)
        self.user_state1_school1_mentor1.currentlySelectedSchool = self.school1_state1
        self.user_state1_school1_mentor1.save()
        response = self.client.get(self.event_details_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'View Invoices')
        self.assertFalse(response.context['hasInvoiceViewPermissions'])


class TestEventDetailsInvoiceButton_OtherStateCoordinator(EventDetailsInvoiceButtonBase, TestCase):
    def test_hides_view_invoices_for_other_state_event(self):
        self.login(self.email_user_state2_fullcoordinator)
        response = self.client.get(self.event_details_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'View Invoices')
        self.assertFalse(response.context['hasInvoiceViewPermissions'])


class TestEventDetailsInvoiceButton_MixedStatePermissions(EventDetailsInvoiceButtonBase, TestCase):
    def test_invoice_permission_is_checked_for_event_state(self):
        # Event manager for this event's state, billing manager for another state
        self.coord_state1_fullcoordinator.permissionLevel = 'eventmanager'
        self.coord_state1_fullcoordinator.save()
        Coordinator.objects.create(
            user=self.user_state1_fullcoordinator,
            state=self.state2,
            permissionLevel='billingmanager',
            position='Text',
        )
        self.login(self.email_user_state1_fullcoordinator)
        response = self.client.get(self.event_details_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'View Invoices')
        self.assertFalse(response.context['hasInvoiceViewPermissions'])
