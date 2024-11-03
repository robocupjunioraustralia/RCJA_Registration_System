from common.baseTests import createStates, createUsers, createSchools, createEvents, createTeams
from django.http import HttpRequest
from django.urls import reverse
from django.test import TestCase

from invoices.models import Invoice

class TestAdminCSVExport_Invoice(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createSchools(cls)
        createEvents(cls)
        createTeams(cls)
        
        cls.invoice = Invoice.objects.filter(event=cls.state1_openCompetition).first()

    def setUp(self):
        self.client.login(request=HttpRequest(), username=self.email_user_state1_super1, password=self.password)

    def test_export_as_csv_loads(self):
        response = self.client.post(reverse('admin:invoices_invoice_changelist'), {'action': 'export_as_csv', '_selected_action': [self.invoice.pk]})
        self.assertEqual(response.status_code, 200)

    def test_export_as_csv_correctHeaders(self):
        response = self.client.post(reverse('admin:invoices_invoice_changelist'), {'action': 'export_as_csv', '_selected_action': [self.invoice.pk]})
        self.assertContains(response, 'Event')

    def test_export_as_csv_correctValues(self):
        response = self.client.post(reverse('admin:invoices_invoice_changelist'), {'action': 'export_as_csv', '_selected_action': [self.invoice.pk]})
        self.assertContains(response, 'State 1 Open Competition')
