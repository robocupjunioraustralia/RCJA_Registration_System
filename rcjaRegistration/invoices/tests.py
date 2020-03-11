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
from events.models import Event, Year, Division, AvailableDivision
from coordination.models import Coordinator
from teams.models import Team, Student

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
            entryFeeIncludesGST=True,
            event_billingType='team',
            event_defaultEntryFee = 50,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=5)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date(),
            directEnquiriesTo = self.user1,
        )
        self.division1 = Division.objects.create(name='Division 1')
        self.division2 = Division.objects.create(name='Division 2')
        self.division3 = Division.objects.create(name='Division 3')

        self.invoiceSettings = InvoiceGlobalSettings.objects.create(
            invoiceFromName='From Name',
            invoiceFromDetails='Test Details Text',
            invoiceFooterMessage='Test Footer Text',
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
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
    
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Login")
    
        response = self.client.get(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/invoices/{self.invoice.id}")
        self.assertEqual(response.status_code, 302)

    def testSuccessInvoiceToUserMentor(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def testDeniedInvoiceToUserMentor(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testSuccessSchoolInvoice(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def testDeniedSchoolInvoice(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)
        self.client.login(request=HttpRequest(), username=self.email3, password=self.password)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testSuccessCoordinator(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissions='viewall')
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)     

    def testSuccessSuperUser(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email_superUser, password=self.password)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)    

    def testDeniedCoordinator_NotCoordinator(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissions='viewall')
        self.client.login(request=HttpRequest(), username=self.email3, password=self.password)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)   

    def testDeniedCoordinator_WrongState(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state2, permissions='viewall')
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testDeniedCoordinator_WrongPermissionLevel(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissions='schoolmanager')
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

class TestInvoiceDetailView(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)

    def testMentorSetsInvoicedDate(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoicedDate, None)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoicedDate, datetime.datetime.today().date())

    def testDontOverwriteDate(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoicedDate=datetime.datetime.now() + datetime.timedelta(days=-10))
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoicedDate, (datetime.datetime.now() + datetime.timedelta(days=-10)).date())

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoicedDate, (datetime.datetime.now() + datetime.timedelta(days=-10)).date())

    def testAdminDoesntSetDate(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email_superUser, password=self.password)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoicedDate, None)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoicedDate, None)

    def testInvoiceGlobalSettingsInInvoice(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "From Name")
        self.assertContains(response, "Test Details Text")
        self.assertContains(response, "Test Footer Text")

    def testContainsInvoiceToDetails(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user1.email)     

    def testUsesCorrectTemplate(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices/details.html')

# Need to test invoice content

class TestPaypalViewPermissions(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
        self.state1.paypalEmail = 'test@test.com'
        self.state1.save()

    def testLoginRequired(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
    
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Login")
    
        response = self.client.get(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/invoices/{self.invoice.id}/paypal")
        self.assertEqual(response.status_code, 302)

    def testSuccessInvoiceToUserMentor(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def testDeniedInvoiceToUserMentor(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testSuccessSchoolInvoice(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1, school=self.school1)
        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def testDeniedSchoolInvoice(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1, school=self.school1)
        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)
        self.client.login(request=HttpRequest(), username=self.email3, password=self.password)

        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testDeniedCoordinator(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissions='viewall')
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)     

    def testDeniedSuperUser(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.client.login(request=HttpRequest(), username=self.email_superUser, password=self.password)

        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)   

    def testDeniedCoordinator_NotCoordinator(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissions='viewall')
        self.client.login(request=HttpRequest(), username=self.email3, password=self.password)

        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)   

    def testDeniedCoordinator_WrongState(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state2, permissions='viewall')
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testDeniedCoordinator_WrongPermissionLevel(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissions='schoolmanager')
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

class TestPaypalView(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
        self.state1.paypalEmail = 'test@test.com'
        self.state1.save()

    def testMentorSetsInvoicedDate(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoicedDate, None)

        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoicedDate, datetime.datetime.today().date())

    def testDontOverwriteDate(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoicedDate=datetime.datetime.now() + datetime.timedelta(days=-10))
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoicedDate, (datetime.datetime.now() + datetime.timedelta(days=-10)).date())

        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoicedDate, (datetime.datetime.now() + datetime.timedelta(days=-10)).date())

    def testUsesCorrectTemplate(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices/paypal.html')

    def testDeniedIfNoPaypalEmail(self):
        self.state1.paypalEmail = ''
        self.state1.save()

        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "PayPal not enabled for this invoice", status_code=403)

class TestSetInvoiceToPermissions(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)

    def testLoginRequired(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        url = reverse('invoices:setInvoiceTo', kwargs= {'invoiceID':self.invoice.id})
    
        response = self.client.post(url, follow=True)
        self.assertContains(response, "Login")
    
        response = self.client.get(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/invoices/{self.invoice.id}/setInvoiceTo")
        self.assertEqual(response.status_code, 302)

    def testSuccessInvoiceToUserMentor(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        url = reverse('invoices:setInvoiceTo', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    def testDeniedInvoiceToUserMentor(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:setInvoiceTo', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testDeniedGet(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        url = reverse('invoices:setInvoiceTo', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def testSuccessSchoolInvoice(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:setInvoiceTo', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    def testDeniedSchoolInvoice(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)
        self.client.login(request=HttpRequest(), username=self.email3, password=self.password)

        url = reverse('invoices:setInvoiceTo', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testDeniedCoordinator(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissions='viewall')
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:setInvoiceTo', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testDeniedSuperUser(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email_superUser, password=self.password)

        url = reverse('invoices:setInvoiceTo', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

class TestSetInvoiceToView(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
    
    def testInvoiceToUpdates(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceToUser, self.user1)

        url = reverse('invoices:setInvoiceTo', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceToUser, self.user2)

class TestSetCampusInvoiceePermissions(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)

    def testLoginRequired(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        url = reverse('invoices:setCampusInvoice', kwargs= {'invoiceID':self.invoice.id})
    
        response = self.client.post(url, follow=True)
        self.assertContains(response, "Login")
    
        response = self.client.get(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/invoices/{self.invoice.id}/setCampusInvoice")
        self.assertEqual(response.status_code, 302)

    def testDeniedInvoiceToUserMentor(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:setCampusInvoice', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testDeniedGet(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        url = reverse('invoices:setCampusInvoice', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def testDeniedSchoolInvoice(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)
        self.client.login(request=HttpRequest(), username=self.email3, password=self.password)

        url = reverse('invoices:setCampusInvoice', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testDeniedCoordinator(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissions='viewall')
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:setCampusInvoice', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testDeniedSuperUser(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email_superUser, password=self.password)

        url = reverse('invoices:setCampusInvoice', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

def setupCampusesAndTeams(self):
    self.campus1 = Campus.objects.create(school=self.school1, name='Campus 1')
    self.campus2 = Campus.objects.create(school=self.school1, name='Campus 2')

    self.team1 = Team.objects.create(event=self.event, school=self.school1, campus=self.campus1, mentorUser=self.user3, name='Team 1', division=self.division1)
    self.team2 = Team.objects.create(event=self.event, school=self.school1, campus=self.campus2, mentorUser=self.user3, name='Team 2', division=self.division1)

class TestCampusInvoicing(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
    
    def testCampusInvoicingNotEnabled_noSchool(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.assertEqual(self.invoice.campusInvoicingEnabled(), False)
    
    def testCampusInvoicingNotAvailable_noSchool(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.assertEqual(self.invoice.campusInvoicingAvailable(), False)
    
    def testCampusInvoicingNotAvailable_paymentMade(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)

        self.assertEqual(self.invoice.campusInvoicingEnabled(), False)
        self.assertEqual(self.invoice.campusInvoicingAvailable(), False)

        setupCampusesAndTeams(self)
        self.assertEqual(self.invoice.campusInvoicingEnabled(), False)
        self.assertEqual(self.invoice.campusInvoicingAvailable(), True)

        self.payment = InvoicePayment.objects.create(invoice=self.invoice, amountPaid=0, datePaid=datetime.datetime.today())

        self.assertEqual(self.invoice.campusInvoicingEnabled(), False)
        self.assertEqual(self.invoice.campusInvoicingAvailable(), False)

class TestSetCampusInvoiceeView(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
    
    def testCampusInvoicingDisabled(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        self.assertEqual(self.invoice.campusInvoicingEnabled(), False)
        self.assertEqual(self.invoice.campusInvoicingAvailable(), False)

        url = reverse('invoices:setCampusInvoice', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Campus invoicing is not available for this event", status_code=403)

        self.assertEqual(self.invoice.campusInvoicingEnabled(), False)
        self.assertEqual(self.invoice.campusInvoicingAvailable(), False)

    def testCampusInvoicingEnabled_invoiceUser(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        self.assertEqual(self.invoice.campusInvoicingEnabled(), False)
        self.assertEqual(self.invoice.campusInvoicingAvailable(), False)

        setupCampusesAndTeams(self)
        self.assertEqual(self.invoice.campusInvoicingEnabled(), False)
        self.assertEqual(self.invoice.campusInvoicingAvailable(), True)

        url = reverse('invoices:setCampusInvoice', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        # Would be good to validate json

        self.assertEqual(self.invoice.campusInvoicingEnabled(), True)
        self.assertEqual(self.invoice.campusInvoicingAvailable(), False)
        self.assertEqual(Invoice.objects.filter(event=self.event, invoiceToUser=self.user1).count(), 3)
        self.assertEqual(Invoice.objects.filter(event=self.event, school=self.school1).count(), 3)

    def testCampusInvoicingEnabled_schoolAdmin(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        self.assertEqual(self.invoice.campusInvoicingEnabled(), False)
        self.assertEqual(self.invoice.campusInvoicingAvailable(), False)

        setupCampusesAndTeams(self)
        self.assertEqual(self.invoice.campusInvoicingEnabled(), False)
        self.assertEqual(self.invoice.campusInvoicingAvailable(), True)

        url = reverse('invoices:setCampusInvoice', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        # Would be good to validate json

        self.assertEqual(self.invoice.campusInvoicingEnabled(), True)
        self.assertEqual(self.invoice.campusInvoicingAvailable(), False)
        self.assertEqual(Invoice.objects.filter(event=self.event, school=self.school1).count(), 3)

class TestEditInvoicePOAJAXPermissions(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)

    def testLoginRequired(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        url = reverse('invoices:invoicePOAJAX', kwargs= {'invoiceID':self.invoice.id})
    
        response = self.client.post(url, follow=True, data={'PONumber': 'TEST'})
        self.assertContains(response, "Login")
    
        response = self.client.get(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/invoices/{self.invoice.id}/setPONumber")
        self.assertEqual(response.status_code, 302)

    def testSuccessInvoiceToUserMentor(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        url = reverse('invoices:invoicePOAJAX', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url, data={'PONumber': 'TEST'})
        self.assertEqual(response.status_code, 200)

    def testDeniedInvoiceToUserMentor(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:invoicePOAJAX', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url, data={'PONumber': 'TEST'})
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testDeniedGet(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        url = reverse('invoices:invoicePOAJAX', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url, data={'PONumber': 'TEST'})
        self.assertEqual(response.status_code, 403)

    def testSuccessSchoolInvoice(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:invoicePOAJAX', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url, data={'PONumber': 'TEST'})
        self.assertEqual(response.status_code, 200)

    def testDeniedSchoolInvoice(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)
        self.client.login(request=HttpRequest(), username=self.email3, password=self.password)

        url = reverse('invoices:invoicePOAJAX', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url, data={'PONumber': 'TEST'})
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testDeniedCoordinator(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissions='viewall')
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:invoicePOAJAX', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url, data={'PONumber': 'TEST'})
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testDeniedSuperUser(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email_superUser, password=self.password)

        url = reverse('invoices:invoicePOAJAX', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url, data={'PONumber': 'TEST'})
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

class TestEditInvoicePOAJAXView(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
    
    def testSetPONumber(self):
        poNumber = 'Test0001'
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.purchaseOrderNumber, "")

        url = reverse('invoices:invoicePOAJAX', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url, data={'PONumber': poNumber})
        self.assertEqual(response.status_code, 200)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.purchaseOrderNumber, poNumber)

    def testClearPONumber(self):
        poNumber = 'Test0002'
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, purchaseOrderNumber=poNumber)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.purchaseOrderNumber, poNumber)

        url = reverse('invoices:invoicePOAJAX', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url, data={'PONumber': ""})
        self.assertEqual(response.status_code, 200)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.purchaseOrderNumber, '')

    def testEmptyPostFails(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.purchaseOrderNumber, "")

        url = reverse('invoices:invoicePOAJAX', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.purchaseOrderNumber, '')

def createCammpuses(self):
    self.campuses = []
    for i in range(2):
        self.campuses.append(
            Campus.objects.create(school=self.school1, name=f'Campus {i}')
        )

def createTeams(self, school, campuses=None):
    self.teams = []
    for division in [self.division1, self.division2, self.division3]:
        if campuses is not None:
            for j in range(2):
                for campus in self.campuses:
                    self.teams.append(
                        Team.objects.create(
                            event=self.event,
                            school=school,
                            campus=campus,
                            mentorUser=self.user1,
                            name=f'Team {j}{division}{campus}',
                            division=division,
                        )
                    )
        else:
            for j in range(4):
                self.teams.append(
                    Team.objects.create(
                        event=self.event,
                        school=school,
                        mentorUser=self.user1,
                        name=f'Team {j}{division}',
                        division=division,
                    )
                )

def createStudents(self):
    self.students = []
    for team in self.teams:
        for i in range(3):
            self.students.append(
                Student.objects.create(
                    team=team,
                    firstName='First name',
                    lastName='Last name',
                    yearLevel=5,
                    gender='other',
                    birthday=datetime.datetime.today(),
                )
            )

class TestInvoiceCalculations_NoCampuses(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
        createTeams(self, self.school1)
        createStudents(self)
        self.invoice = Invoice.objects.get(event=self.event, school=self.school1)
    
    def testDefaultRateTeamInclGST(self):
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50, 2))
        self.assertEqual(self.invoice.invoiceAmountExclGST(), round((12 * 50)/1.1, 2))
        self.assertEqual(self.invoice.amountGST(), round(self.invoice.invoiceAmountInclGST() - self.invoice.invoiceAmountExclGST(), 2))

        self.assertEqual(self.invoice.amountPaid(), 0)
        self.assertEqual(self.invoice.amountDueInclGST(), round(12 * 50, 2))
        self.assertEqual(self.invoice.amountDueExclGST(), round((12 * 50)/1.1, 2))

    def testDefaultRateTeamExclGST(self):
        self.event.entryFeeIncludesGST = False
        self.event.save()

        self.assertEqual(self.invoice.invoiceAmountExclGST(), round(12 * 50, 2))
        self.assertEqual(self.invoice.amountGST(), round((12 * 50) * 0.1, 2))
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round((12 * 50) * 1.1, 2))

        self.assertEqual(self.invoice.amountPaid(), 0)
        self.assertEqual(self.invoice.amountDueExclGST(), round(12 * 50, 2))
        self.assertEqual(self.invoice.amountDueInclGST(), round((12 * 50) * 1.1, 2))

    def testAmountPaid(self):
        InvoicePayment.objects.create(
            invoice=self.invoice,
            amountPaid=200,
            datePaid=datetime.datetime.today(),
        )

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50, 2))
        self.assertEqual(self.invoice.invoiceAmountExclGST(), round((12 * 50)/1.1, 2))
        self.assertEqual(self.invoice.amountGST(), round(self.invoice.invoiceAmountInclGST() - self.invoice.invoiceAmountExclGST(), 2))

        self.assertEqual(self.invoice.amountPaid(), 200)
        self.assertEqual(self.invoice.amountDueInclGST(), round(12 * 50 - 200))
        self.assertEqual(self.invoice.amountDueExclGST(), round((12 * 50)/1.1 - 200, 2))

    def testDefaultRateStudent(self):
        self.event.event_billingType = 'student'
        self.event.save()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(36 * 50, 2))

    def testSpecialRateInclGST(self):
        self.event.event_specialRateNumber = 4
        self.event.event_specialRateFee = 30
        self.event.save()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50 - 80, 2))

    def testSpecialRateExclGST(self):
        self.event.entryFeeIncludesGST = False

        self.event.event_specialRateNumber = 4
        self.event.event_specialRateFee = 30
        self.event.save()

        self.assertEqual(self.invoice.invoiceAmountExclGST(), round(12 * 50 - 80, 2))
        self.assertEqual(self.invoice.amountGST(), round((12 * 50 - 80)*0.1, 2))
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round((12 * 50 - 80)*1.1, 2))

    def testAvailableDivisionRateTeam(self):
        AvailableDivision.objects.create(
            division=self.division1,
            event=self.event,
            division_billingType='team',
            division_entryFee=80,
        )

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50 + 120, 2))

    def testAvailableDivisionRateStudent(self):
        AvailableDivision.objects.create(
            division=self.division1,
            event=self.event,
            division_billingType='student',
            division_entryFee=80,
        )

        self.assertEqual(self.invoice.invoiceAmountInclGST(), 1360)

class TestInvoiceCalculations_Campuses(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
        createCammpuses(self)
        createTeams(self, self.school1, campuses = self.campuses)
        createStudents(self)
        self.campus1 = self.campuses[0]
        self.invoice = Invoice.objects.create(event=self.event, school=self.school1, campus=self.campus1, invoiceToUser=self.user1)
    
    def testDefaultRateTeam(self):
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(6 * 50, 2))

    def testDefaultRateStudent(self):
        self.event.event_billingType = 'student'
        self.event.save()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(18 * 50, 2))

    def testSpecialRate(self):
        self.event.event_specialRateNumber = 4
        self.event.event_specialRateFee = 30
        self.event.save()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(6 * 50 - 40, 2))

    def testAvailableDivisionRateTeam(self):
        AvailableDivision.objects.create(
            division=self.division1,
            event=self.event,
            division_billingType='team',
            division_entryFee=80,
        )

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(6 * 50 + 60, 2))

    def testAvailableDivisionRateStudent(self):
        AvailableDivision.objects.create(
            division=self.division1,
            event=self.event,
            division_billingType='student',
            division_entryFee=80,
        )

        self.assertEqual(self.invoice.invoiceAmountInclGST(), 680)

class TestInvoiceCalculations_Independent(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
        createTeams(self, None)
        createStudents(self)
        self.invoice = Invoice.objects.get(event=self.event, invoiceToUser=self.user1)
    
    def testDefaultRateTeam(self):
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50, 2))

    def testDefaultRateStudent(self):
        self.event.event_billingType = 'student'
        self.event.save()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(36 * 50, 2))

    def testSpecialRate(self):
        self.event.event_specialRateNumber = 4
        self.event.event_specialRateFee = 30
        self.event.save()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50 - 80, 2))

    def testAvailableDivisionRateTeam(self):
        AvailableDivision.objects.create(
            division=self.division1,
            event=self.event,
            division_billingType='team',
            division_entryFee=80,
        )

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50 + 120, 2))

    def testAvailableDivisionRateStudent(self):
        AvailableDivision.objects.create(
            division=self.division1,
            event=self.event,
            division_billingType='student',
            division_entryFee=80,
        )

        self.assertEqual(self.invoice.invoiceAmountInclGST(), 1360)

class TestInvoiceMethods(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
        createCammpuses(self)
        self.user1.first_name = 'First'
        self.user1.last_name = 'Last'
        self.user1.save()

    def testGetState(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.assertEqual(self.invoice.getState(), self.state1)

    def testStr_campus(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1, campus=self.campuses[0])
        self.assertEqual(str(self.invoice), "Test event 1 2020 (VIC): School 1, Campus 0")

    def testStr_schoolNoCampus(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.assertEqual(str(self.invoice), "Test event 1 2020 (VIC): School 1")

    def testStr_independent(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.assertEqual(str(self.invoice), "Test event 1 2020 (VIC): First Last")

    def testInvoiceToUserName(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.assertEqual(self.invoice.invoiceToUserName(), 'First Last')

    def testInvoiceToUserEmail(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.assertEqual(self.invoice.invoiceToUserEmail(), self.email1)

class TestInvoiceSummaryView(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
        self.campus1 = Campus.objects.create(school=self.school1, name='Campus 1')

    def testLoginRequired(self):
        url = reverse('invoices:summary')
    
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Login")
    
        response = self.client.get(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/invoices")
        self.assertEqual(response.status_code, 302)

    def testPageLoads_noInvoices(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        url = reverse('invoices:summary')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'], self.user1)
        self.assertQuerysetEqual(response.context['invoices'], Invoice.objects.none())

    def testPageLoads_invoices(self):
        self.invoice3 = Invoice.objects.create(event=self.event, invoiceToUser=self.user2)

        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)
        url = reverse('invoices:summary')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'], self.user2)
        self.assertEqual(response.context['invoices'].count(), 1)

    def testTemplateQuerysetCorrectlyFiltered(self):
        # Invoices that user 2 should have access to
        self.invoice1 = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1) # Through school admin
        self.invoice1c = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1, campus=self.campus1) # Through school admin
        self.invoice2 = Invoice.objects.create(event=self.event, invoiceToUser=self.user2, school=self.school2) # Through invoice to
        self.invoice3 = Invoice.objects.create(event=self.event, invoiceToUser=self.user2) # Through invoice to
        self.schoolAdmin = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)

        # Invoices that should not have access to
        self.invoice2 = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school3)

        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)
        url = reverse('invoices:summary')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'], self.user2)

        self.assertEqual(response.context['invoices'].count(), 4)

        for invoice in response.context['invoices']:
            assert invoice.invoiceToUser == self.user2 or invoice.school.id in self.user2.schooladministrator_set.values_list('school', flat=True), 'No permission to view this invoice'

    def testUsesCorrectTemplate(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        url = reverse('invoices:summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices/summary.html')
