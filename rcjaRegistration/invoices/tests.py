from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, modify_settings
from django.urls import reverse
from django.test import Client
from django.http import HttpRequest
from django.core.exceptions import ValidationError

from .models import InvoiceGlobalSettings, Invoice, InvoicePayment
from users.models import User
from regions.models import State, Region
from schools.models import School, SchoolAdministrator, Campus
from events.models import Event, Year
from coordination.models import Coordinator

import datetime

class TestInvoiceGlobalSettings(TestCase):
    def setUp(self):
        pass

    def testStr(self):
        settingsObj = InvoiceGlobalSettings.objects.create(invoiceFromName='1', invoiceFromDetails='1')
        self.assertEqual(str(settingsObj), 'Invoice settings')

    def testObject1Limit(self):
        ob1 = InvoiceGlobalSettings.objects.create(invoiceFromName='1', invoiceFromDetails='1')
        self.assertEqual(str(ob1), 'Invoice settings')

        obj2 = InvoiceGlobalSettings(invoiceFromName='2', invoiceFromDetails='2')
        self.assertRaises(ValidationError, obj2.clean)

def commonSetUp(self):
        self.user1 = User.objects.create_user(email=self.email1, password=self.password)
        self.user2 = User.objects.create_user(email=self.email2, password=self.password)
        self.user3 = User.objects.create_user(email=self.email3, password=self.password)
        self.superUser = User.objects.create_user(email=self.email_superUser, password=self.password, is_superuser=True)

        self.state1 = State.objects.create(treasurer=self.user1, name='Victoria', abbreviation='VIC')
        self.state2 = State.objects.create(treasurer=self.user1, name='NSW', abbreviation='NSW')
        self.region1 = Region.objects.create(name='Test Region', description='test desc')

        self.school1 = School.objects.create(name='School 1', abbreviation='sch1', state=self.state1, region=self.region1)
        self.school2 = School.objects.create(name='School 2', abbreviation='sch2', state=self.state1, region=self.region1)
        self.school3 = School.objects.create(name='School 3', abbreviation='sch3', state=self.state1, region=self.region1)

        self.year = Year.objects.create(year=2020)
        self.event = Event.objects.create(
            year=self.year,
            state=self.state1,
            name='Test event 1',
            maxMembersPerTeam=5,
            event_defaultEntryFee = 50,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=5)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date(),
            directEnquiriesTo = self.user1     
        )

        self.invoiceSettings = InvoiceGlobalSettings.objects.create(
            invoiceFromName='Name',
            invoiceFromDetails='Details',
            invoiceFooterMessage='Footer',
        )

class TestInvoiceDetailPermissions(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)

    def testLoginRequired(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1)
        url = reverse('invoices:detail', kwargs= {'invoiceID':self.invoice.id})
    
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Login")
    
        response = self.client.get(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/invoice/{self.invoice.id}/detail")
        self.assertEqual(response.status_code, 302)

    def testSuccessInvoiceToUserMentor(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        url = reverse('invoices:detail', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def testDeniedInvoiceToUserMentor(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1)
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:detail', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testSuccessSchoolInvoice(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1, school=self.school1)
        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:detail', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def testDeniedSchoolInvoice(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1, school=self.school1)
        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)
        self.client.login(request=HttpRequest(), username=self.email3, password=self.password)

        url = reverse('invoices:detail', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testSuccessCoordinator(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissions='viewall')
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:detail', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)     

    def testSuccessSuperUser(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1)
        self.client.login(request=HttpRequest(), username=self.email_superUser, password=self.password)

        url = reverse('invoices:detail', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)    

    def testDeniedCoordinator_NotCoordinator(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissions='viewall')
        self.client.login(request=HttpRequest(), username=self.email3, password=self.password)

        url = reverse('invoices:detail', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)   

    def testDeniedCoordinator_WrongState(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state2, permissions='viewall')
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:detail', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)   

    def testDeniedCoordinator_WrongPermissionLevel(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissions='schoolmanager')
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:detail', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)   

class TestSetInvoiceToPermissions(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)

    def testLoginRequired(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1)
        url = reverse('invoices:setInvoiceTo', kwargs= {'invoiceID':self.invoice.id})
    
        response = self.client.post(url, follow=True)
        self.assertContains(response, "Login")
    
        response = self.client.get(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/invoice/{self.invoice.id}/setInvoiceTo")
        self.assertEqual(response.status_code, 302)

    def testSuccessInvoiceToUserMentor(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        url = reverse('invoices:setInvoiceTo', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    def testDeniedInvoiceToUserMentor(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1)
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:setInvoiceTo', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testDeniedGet(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        url = reverse('invoices:setInvoiceTo', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def testSuccessSchoolInvoice(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1, school=self.school1)
        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:setInvoiceTo', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    def testDeniedSchoolInvoice(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1, school=self.school1)
        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)
        self.client.login(request=HttpRequest(), username=self.email3, password=self.password)

        url = reverse('invoices:setInvoiceTo', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testDeniedCoordinator(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissions='viewall')
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:setInvoiceTo', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)    

    def testDeniedSuperUser(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoiceNumber=1)
        self.client.login(request=HttpRequest(), username=self.email_superUser, password=self.password)

        url = reverse('invoices:setInvoiceTo', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)    
