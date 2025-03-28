from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, modify_settings
from django.urls import reverse
from django.test import Client
from django.http import HttpRequest
from django.core.exceptions import ValidationError

from invoices.models import InvoiceGlobalSettings, Invoice, InvoicePayment
from users.models import User
from regions.models import State, Region
from schools.models import School, SchoolAdministrator, Campus
from events.models import Event, Year, Division, AvailableDivision
from coordination.models import Coordinator
from teams.models import Team, Student
from workshops.models import WorkshopAttendee
from association.models import AssociationMember

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
        self.user1 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email1, password=self.password)
        self.user1_association_member = AssociationMember.objects.create(user=self.user1, birthday=(datetime.datetime.now() + datetime.timedelta(days=-20*365)).date(), rulesAcceptedDate=datetime.datetime.now(), membershipStartDate=datetime.datetime.now())

        self.user2 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email2, password=self.password)
        self.user2_association_member = AssociationMember.objects.create(user=self.user2, birthday=(datetime.datetime.now() + datetime.timedelta(days=-20*365)).date(), rulesAcceptedDate=datetime.datetime.now(), membershipStartDate=datetime.datetime.now())

        self.user3 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email3, password=self.password)
        self.user3_association_member = AssociationMember.objects.create(user=self.user3, birthday=(datetime.datetime.now() + datetime.timedelta(days=-20*365)).date(), rulesAcceptedDate=datetime.datetime.now(), membershipStartDate=datetime.datetime.now())

        self.superUser = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email_superUser, password=self.password, is_superuser=True)

        self.state1 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='Victoria', abbreviation='VIC')
        self.state2 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='NSW', abbreviation='NSW')
        self.region1 = Region.objects.create(name='Test Region', description='test desc')

        self.school1 = School.objects.create(name='School 1', state=self.state1, region=self.region1)
        self.school2 = School.objects.create(name='School 2', state=self.state1, region=self.region1)
        self.school3 = School.objects.create(name='School 3', state=self.state1, region=self.region1)

        self.year = Year.objects.create(year=2020)
        self.event = Event.objects.create(
            year=self.year,
            state=self.state1,
            name='Test event 1',
            eventType='competition',
            status='published',
            maxMembersPerTeam=5,
            entryFeeIncludesGST=True,
            competition_billingType='team',
            competition_defaultEntryFee = 50,
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
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissionLevel='viewall')
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
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissionLevel='viewall')
        self.client.login(request=HttpRequest(), username=self.email3, password=self.password)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)   

    def testDeniedCoordinator_WrongState(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state2, permissionLevel='viewall')
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testDeniedCoordinator_WrongPermissionLevel(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissionLevel='schoolmanager')
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

    def testMentorSetsInvoicedDate_noDate(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoicedDate, None)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoicedDate, datetime.datetime.today().date())

    def testMentorSetsInvoicedDate_futureDate(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoicedDate=datetime.datetime.now() + datetime.timedelta(days=10))
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoicedDate, (datetime.datetime.now() + datetime.timedelta(days=10)).date())

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoicedDate, datetime.datetime.today().date())

    def testUpdatesTotals(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.invoice.cache_invoiceAmountInclGST_unrounded = 50
        self.invoice.save(skipPrePostSave=True)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amountDueInclGST(), 50)

        url = reverse('invoices:details', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amountDueInclGST(), 0)

    def testDontOverwritePastDate(self):
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
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissionLevel='viewall')
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
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissionLevel='viewall')
        self.client.login(request=HttpRequest(), username=self.email3, password=self.password)

        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)   

    def testDeniedCoordinator_WrongState(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state2, permissionLevel='viewall')
        self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this invoice", status_code=403)

    def testDeniedCoordinator_WrongPermissionLevel(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissionLevel='schoolmanager')
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

    def testMentorSetsInvoicedDate_noDate(self):
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

    def testMentorSetsInvoicedDate_futureDate(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoicedDate=datetime.datetime.now() + datetime.timedelta(days=10))
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoicedDate, (datetime.datetime.now() + datetime.timedelta(days=10)).date())

        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoicedDate, datetime.datetime.today().date())

    def testUpdatesTotals(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.invoice.cache_invoiceAmountInclGST_unrounded = 50
        self.invoice.save(skipPrePostSave=True)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amountDueInclGST(), 50)

        url = reverse('invoices:paypal', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.get(url)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amountDueInclGST(), 0)

    def testDontOverwritePastDate(self):
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
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissionLevel='viewall')
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
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissionLevel='viewall')
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

    def testCampusInvoicingEnabled_updatesOriginalInvoiceTotals(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        setupCampusesAndTeams(self)
        url = reverse('invoices:setCampusInvoice', kwargs= {'invoiceID':self.invoice.id})
        response = self.client.post(url)
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), 0)


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
        self.coordinator = Coordinator.objects.create(user=self.user2, state=self.state1, permissionLevel='viewall')
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
                )
            )

class TestInvoiceCalculations_NoCampuses(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    @classmethod
    def setUpTestData(cls):
        commonSetUp(cls)
        createTeams(cls, cls.school1)
        createStudents(cls)
        cls.invoice = Invoice.objects.get(event=cls.event, school=cls.school1)
        cls.invoice2 = Invoice.objects.create(event=cls.event, school=cls.school2, invoiceToUser=cls.user2)
        cls.invoice3 = Invoice.objects.create(event=cls.event, school=cls.school3, invoiceToUser=cls.user3)
    
    def testDefaultRateTeamInclGST(self):
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50, 2))
        self.assertEqual(self.invoice.invoiceAmountExclGST(), round((12 * 50)/1.1, 2))
        self.assertEqual(self.invoice.amountGST(), round(self.invoice.invoiceAmountInclGST() - self.invoice.invoiceAmountExclGST(), 2))

        self.assertEqual(self.invoice.amountPaid(), 0)
        self.assertEqual(self.invoice.amountDueInclGST(), round(12 * 50, 2))

    def testSurchage(self):
        self.event.eventSurchargeAmount = 11
        self.event.save()
        self.invoice.save()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50 + 12 * 11, 2))
        self.assertEqual(self.invoice.invoiceAmountExclGST(), round((12 * 50 + 12 * 11)/1.1, 2))
        self.assertEqual(self.invoice.amountGST(), round(self.invoice.invoiceAmountInclGST() - self.invoice.invoiceAmountExclGST(), 2))

        self.assertEqual(self.invoice.amountPaid(), 0)
        self.assertEqual(self.invoice.amountDueInclGST(), round(12 * 50 + 12 * 11, 2))

    def testAddTeam(self):
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50, 2))

        Team.objects.create(
            event=self.event,
            school=self.school1,
            mentorUser=self.user1,
            name='New Team',
            division=self.division1,
        )

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(13 * 50, 2))

    def testDeleteTeam(self):
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50, 2))
        self.teams[1].delete()
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(11 * 50, 2))

    def testDefaultRateTeamExclGST(self):
        self.event.entryFeeIncludesGST = False
        self.event.save()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountExclGST(), round(12 * 50, 2))
        self.assertEqual(self.invoice.amountGST(), round((12 * 50) * 0.1, 2))
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round((12 * 50) * 1.1, 2))

        self.assertEqual(self.invoice.amountPaid(), 0)
        self.assertEqual(self.invoice.amountDueInclGST(), round((12 * 50) * 1.1, 2))

    def testAmountPaid(self):
        InvoicePayment.objects.create(
            invoice=self.invoice,
            amountPaid=200,
            datePaid=datetime.datetime.today(),
        )
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50, 2))
        self.assertEqual(self.invoice.invoiceAmountExclGST(), round((12 * 50)/1.1, 2))
        self.assertEqual(self.invoice.amountGST(), round(self.invoice.invoiceAmountInclGST() - self.invoice.invoiceAmountExclGST(), 2))

        self.assertEqual(self.invoice.amountPaid(), 200)
        self.assertEqual(self.invoice.amountDueInclGST(), round(12 * 50 - 200))

    def testAmountDueNotNegative(self):
        InvoicePayment.objects.create(
            invoice=self.invoice,
            amountPaid=20000,
            datePaid=datetime.datetime.today(),
        )
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50, 2))
        self.assertEqual(self.invoice.invoiceAmountExclGST(), round((12 * 50)/1.1, 2))
        self.assertEqual(self.invoice.amountGST(), round(self.invoice.invoiceAmountInclGST() - self.invoice.invoiceAmountExclGST(), 2))

        self.assertEqual(self.invoice.amountPaid(), 20000)
        self.assertEqual(self.invoice.amountDueInclGST(), 0)

    def testDefaultRateStudent(self):
        self.event.competition_billingType = 'student'
        self.event.save()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(36 * 50, 2))

    def testAddStudent(self):
        self.event.competition_billingType = 'student'
        self.event.save()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(36 * 50, 2))

        self.newStudent = Student.objects.create(
            team=self.teams[0],
            firstName='First name',
            lastName='Last name',
            yearLevel=5,
            gender='other',
        )
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(37 * 50, 2))

    def testDeleteStudent(self):
        self.event.competition_billingType = 'student'
        self.event.save()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(36 * 50, 2))

        self.students[0].delete()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(35 * 50, 2))

    def testSpecialRateInclGST(self):
        self.event.competition_specialRateNumber = 4
        self.event.competition_specialRateFee = 30
        self.event.save()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50 - 80, 2))

    def testSpecialRateExclGST(self):
        self.event.entryFeeIncludesGST = False

        self.event.competition_specialRateNumber = 4
        self.event.competition_specialRateFee = 30
        self.event.save()
        self.invoice.refresh_from_db()

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
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50 + 120, 2))

    def testDeleteAvailableDivision(self):
        self.availableDivision = AvailableDivision.objects.create(
            division=self.division1,
            event=self.event,
            division_billingType='team',
            division_entryFee=80,
        )
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50 + 120, 2))

        self.availableDivision.delete()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50, 2))

    def testAvailableDivisionRateStudent(self):
        AvailableDivision.objects.create(
            division=self.division1,
            event=self.event,
            division_billingType='student',
            division_entryFee=80,
        )
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), 1360)

    def testChangeTeamSchool(self):
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50, 2))
        self.invoice2.refresh_from_db()
        self.assertEqual(self.invoice2.invoiceAmountInclGST(), round(0 * 50, 2))

        self.teams[0].school = self.school2
        self.teams[0].save()

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(11 * 50, 2))
        self.invoice2.refresh_from_db()
        self.assertEqual(self.invoice2.invoiceAmountInclGST(), round(1 * 50, 2))

    def testAddInvoiceOverride(self):
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50, 2))
        self.invoice2.refresh_from_db()
        self.assertEqual(self.invoice2.invoiceAmountInclGST(), round(0 * 50, 2))

        self.teams[0].invoiceOverride = self.invoice2
        self.teams[0].save()

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(11 * 50, 2))
        self.invoice2.refresh_from_db()
        self.assertEqual(self.invoice2.invoiceAmountInclGST(), round(1 * 50, 2))

    def testChangeInvoiceOverride(self):
        self.teams[0].invoiceOverride = self.invoice2
        self.teams[0].save()

        self.invoice2.refresh_from_db()
        self.assertEqual(self.invoice2.invoiceAmountInclGST(), round(1 * 50, 2))
        self.invoice3.refresh_from_db()
        self.assertEqual(self.invoice3.invoiceAmountInclGST(), round(0 * 50, 2))

        self.teams[0].invoiceOverride = self.invoice3
        self.teams[0].save()

        self.invoice2.refresh_from_db()
        self.assertEqual(self.invoice2.invoiceAmountInclGST(), round(0 * 50, 2))
        self.invoice3.refresh_from_db()
        self.assertEqual(self.invoice3.invoiceAmountInclGST(), round(1 * 50, 2))


    def testRemoveInvoiceOverride(self):
        self.teams[0].invoiceOverride = self.invoice2
        self.teams[0].save()

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(11 * 50, 2))
        self.invoice2.refresh_from_db()
        self.assertEqual(self.invoice2.invoiceAmountInclGST(), round(1 * 50, 2))

        self.teams[0].invoiceOverride = None
        self.teams[0].save()

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50, 2))
        self.invoice2.refresh_from_db()
        self.assertEqual(self.invoice2.invoiceAmountInclGST(), round(0 * 50, 2))

class TestInvoiceCalculations_Campuses(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    @classmethod
    def setUpTestData(cls):
        commonSetUp(cls)
        createCammpuses(cls)
        createTeams(cls, cls.school1, campuses = cls.campuses)
        createStudents(cls)
        cls.campus1 = cls.campuses[0]
        cls.invoice = Invoice.objects.create(event=cls.event, school=cls.school1, campus=cls.campus1, invoiceToUser=cls.user1)
    
    def testDefaultRateTeam(self):
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(6 * 50, 2))

    def testSurchage(self):
        self.event.eventSurchargeAmount = 11
        self.event.save()
        self.invoice.save()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(6 * 50 + 6 * 11, 2))

    def testDefaultRateStudent(self):
        self.event.competition_billingType = 'student'
        self.event.save()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(18 * 50, 2))

    def testChangeStudentTeam(self):
        self.event.competition_billingType = 'student'
        self.event.save()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(18 * 50, 2))

        self.students[0].team = self.teams[1]
        self.students[0].save()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(17 * 50, 2))

    def testSpecialRate(self):
        self.event.competition_specialRateNumber = 4
        self.event.competition_specialRateFee = 30
        self.event.save()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(6 * 50 - 40, 2))

    def testAvailableDivisionRateTeam(self):
        AvailableDivision.objects.create(
            division=self.division1,
            event=self.event,
            division_billingType='team',
            division_entryFee=80,
        )
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(6 * 50 + 60, 2))

    def testAvailableDivisionRateStudent(self):
        AvailableDivision.objects.create(
            division=self.division1,
            event=self.event,
            division_billingType='student',
            division_entryFee=80,
        )
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), 680)

    def testChangeTeamCampus(self):
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(6 * 50, 2))

        self.teams[0].campus = self.campuses[1]
        self.teams[0].save()
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(5 * 50, 2))

class TestInvoiceCalculations_Independent(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    @classmethod
    def setUpTestData(cls):
        commonSetUp(cls)
        createTeams(cls, None)
        createStudents(cls)
        cls.invoice = Invoice.objects.get(event=cls.event, invoiceToUser=cls.user1)
    
    def testDefaultRateTeam(self):
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50, 2))

    def testSurchage(self):
        self.event.eventSurchargeAmount = 11
        self.event.save()
        self.invoice.save()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50 + 12 * 11, 2))

    def testDefaultRateStudent(self):
        self.event.competition_billingType = 'student'
        self.event.save()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(36 * 50, 2))

    def testSpecialRate(self):
        self.event.competition_specialRateNumber = 4
        self.event.competition_specialRateFee = 30
        self.event.save()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50 - 80, 2))

    def testAvailableDivisionRateTeam(self):
        AvailableDivision.objects.create(
            division=self.division1,
            event=self.event,
            division_billingType='team',
            division_entryFee=80,
        )
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50 + 120, 2))

    def testAvailableDivisionRateStudent(self):
        AvailableDivision.objects.create(
            division=self.division1,
            event=self.event,
            division_billingType='student',
            division_entryFee=80,
        )
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), 1360)

    def testChangeTeamMentor(self):
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(12 * 50, 2))

        self.teams[0].mentorUser = self.user2
        self.teams[0].save()
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(11 * 50, 2))

class TestInvoiceCalculations_NoCampuses_Workshop(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    @classmethod
    def setUpTestData(cls):
        commonSetUp(cls)
        cls.event = Event.objects.create(
            year=cls.year,
            state=cls.state1,
            name='Workshop Event',
            eventType='workshop',
            status='published',
            maxMembersPerTeam=5,
            entryFeeIncludesGST=True,
            competition_billingType='team',
            competition_defaultEntryFee = 35,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=5)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date(),
            directEnquiriesTo = cls.user1,
        )
        cls.attendee1 = WorkshopAttendee.objects.create(
            event=cls.event,
            school=cls.school1,
            mentorUser=cls.user1,
            division=cls.division1,
            attendeeType='student',
            firstName='Name 1',
            lastName='Last 1',
            yearLevel='5',
            gender='other',
            email='test@test.com'
        )
        cls.attendee2 = WorkshopAttendee.objects.create(
            event=cls.event,
            school=cls.school1,
            mentorUser=cls.user1,
            division=cls.division1,
            attendeeType='teacher',
            firstName='Name 2',
            lastName='Last 2',
            yearLevel='5',
            gender='other',
            email='test@test.com'
        )
        cls.invoice = Invoice.objects.get(event=cls.event, school=cls.school1)
        cls.invoice2 = Invoice.objects.create(event=cls.event, school=cls.school2, invoiceToUser=cls.user2)
        cls.invoice3 = Invoice.objects.create(event=cls.event, school=cls.school3, invoiceToUser=cls.user3)

    def testDefaultRateAttendeeInclGST(self):
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(2 * 35, 2))
        self.assertEqual(self.invoice.invoiceAmountExclGST(), round((2 * 35)/1.1, 2))
        self.assertEqual(self.invoice.amountGST(), round(self.invoice.invoiceAmountInclGST() - self.invoice.invoiceAmountExclGST(), 2))

        self.assertEqual(self.invoice.amountPaid(), 0)
        self.assertEqual(self.invoice.amountDueInclGST(), round(2 * 35, 2))

    def testSurchage(self):
        self.event.eventSurchargeAmount = 11
        self.event.save()
        self.invoice.save()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(2 * 35 + 2 * 11, 2))

    def testAddAttendee(self):
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(2 * 35, 2))

        WorkshopAttendee.objects.create(
            event=self.event,
            school=self.school1,
            mentorUser=self.user1,
            division=self.division1,
            attendeeType='student',
            firstName='Name 2',
            lastName='Last 2',
            yearLevel='5',
            gender='other',
            email='test@test.com'
        )

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(3 * 35, 2))

    def testDeleteAttendee(self):
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(2 * 35, 2))
        self.attendee1.delete()
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(1 * 35, 2))

    def testDefaultRateTeamExclGST(self):
        self.event.entryFeeIncludesGST = False
        self.event.save()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountExclGST(), round(2 * 35, 2))
        self.assertEqual(self.invoice.amountGST(), round((2 * 35) * 0.1, 2))
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round((2 * 35) * 1.1, 2))

        self.assertEqual(self.invoice.amountPaid(), 0)
        self.assertEqual(self.invoice.amountDueInclGST(), round((2 * 35) * 1.1, 2))

    def testDifferentRates(self):
        self.event.workshopTeacherEntryFee = 2
        self.event.workshopStudentEntryFee = 15
        self.event.save()
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(17, 2))
        self.assertEqual(self.invoice.invoiceAmountExclGST(), round((17)/1.1, 2))
        self.assertEqual(self.invoice.amountGST(), round(self.invoice.invoiceAmountInclGST() - self.invoice.invoiceAmountExclGST(), 2))

        self.assertEqual(self.invoice.amountPaid(), 0)
        self.assertEqual(self.invoice.amountDueInclGST(), round(17, 2))

    def testAmountPaid(self):
        InvoicePayment.objects.create(
            invoice=self.invoice,
            amountPaid=50,
            datePaid=datetime.datetime.today(),
        )
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(2 * 35, 2))
        self.assertEqual(self.invoice.invoiceAmountExclGST(), round((2 * 35)/1.1, 2))
        self.assertEqual(self.invoice.amountGST(), round(self.invoice.invoiceAmountInclGST() - self.invoice.invoiceAmountExclGST(), 2))

        self.assertEqual(self.invoice.amountPaid(), 50)
        self.assertEqual(self.invoice.amountDueInclGST(), round(2 * 35 - 50))

    def testChangeWorkshopSchool(self):
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(2 * 35, 2))
        self.invoice2.refresh_from_db()
        self.assertEqual(self.invoice2.invoiceAmountInclGST(), round(0 * 35, 2))

        self.attendee1.school = self.school2
        self.attendee1.save()

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(1 * 35, 2))
        self.invoice2.refresh_from_db()
        self.assertEqual(self.invoice2.invoiceAmountInclGST(), round(1 * 35, 2))

    def testAddInvoiceOverride(self):
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(2 * 35, 2))
        self.invoice2.refresh_from_db()
        self.assertEqual(self.invoice2.invoiceAmountInclGST(), round(0 * 35, 2))

        self.attendee1.invoiceOverride = self.invoice2
        self.attendee1.save()

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(1 * 35, 2))
        self.invoice2.refresh_from_db()
        self.assertEqual(self.invoice2.invoiceAmountInclGST(), round(1 * 35, 2))

    def testChangeInvoiceOverride(self):
        self.attendee1.invoiceOverride = self.invoice2
        self.attendee1.save()

        self.invoice2.refresh_from_db()
        self.assertEqual(self.invoice2.invoiceAmountInclGST(), round(1 * 35, 2))
        self.invoice3.refresh_from_db()
        self.assertEqual(self.invoice3.invoiceAmountInclGST(), round(0 * 35, 2))

        self.attendee1.invoiceOverride = self.invoice3
        self.attendee1.save()

        self.invoice2.refresh_from_db()
        self.assertEqual(self.invoice2.invoiceAmountInclGST(), round(0 * 35, 2))
        self.invoice3.refresh_from_db()
        self.assertEqual(self.invoice3.invoiceAmountInclGST(), round(1 * 35, 2))


    def testRemoveInvoiceOverride(self):
        self.attendee1.invoiceOverride = self.invoice2
        self.attendee1.save()

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(1 * 35, 2))
        self.invoice2.refresh_from_db()
        self.assertEqual(self.invoice2.invoiceAmountInclGST(), round(1 * 35, 2))

        self.attendee1.invoiceOverride = None
        self.attendee1.save()

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), round(2 * 35, 2))
        self.invoice2.refresh_from_db()
        self.assertEqual(self.invoice2.invoiceAmountInclGST(), round(0 * 35, 2))

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
        self.assertEqual(str(self.invoice), "Invoice 1: School 1, Campus 0")

    def testStr_schoolNoCampus(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.assertEqual(str(self.invoice), "Invoice 1: School 1")

    def testStr_independent(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.assertEqual(str(self.invoice), "Invoice 1: First Last")

    def testInvoiceToUserName(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.assertEqual(self.invoice.invoiceToUserName(), 'First Last')

    def testInvoiceToUserEmail(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.assertEqual(self.invoice.invoiceToUserEmail(), self.email1)

    def testSaveUpdatesTotals(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.invoice.cache_invoiceAmountInclGST_unrounded = 50
        self.invoice.save(skipPrePostSave=True)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amountDueInclGST(), 50)

        self.invoice.save()

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amountDueInclGST(), 0)

    def testDeleteUpdatesOtherInvoices(self):
        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)

        self.team1 = Team.objects.create(event=self.event, school=self.school1, campus=self.campuses[0], mentorUser=self.user3, name='Team 1', division=self.division1)
        self.team2 = Team.objects.create(event=self.event, school=self.school1, campus=self.campuses[1], mentorUser=self.user3, name='Team 2', division=self.division1)

        self.invoice1 = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1, campus=self.campuses[0])
        self.invoice2 = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1, campus=self.campuses[1])

        self.invoice.calculateAndSaveAllTotals()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), 0)

        self.invoice1.delete()
        self.invoice2.delete()

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.invoiceAmountInclGST(), 100)

    def baseTestTotalsNone(self, field, value):
        self.team1 = Team.objects.create(event=self.event, school=self.school1, mentorUser=self.user3, name='Team 1', division=self.division1)
        self.invoice = Invoice.objects.get(event=self.event, school=self.school1)
        self.invoice.cache_amountGST_unrounded = None
        self.invoice.cache_totalQuantity = None
        self.invoice.cache_invoiceAmountExclGST_unrounded = None
        self.invoice.cache_invoiceAmountInclGST_unrounded = None
        self.invoice.save(skipPrePostSave=True)
        self.invoice.refresh_from_db()

        # Check cache fields are none
        self.assertEqual(self.invoice.cache_amountGST_unrounded, None)
        self.assertEqual(self.invoice.cache_totalQuantity, None)
        self.assertEqual(self.invoice.cache_invoiceAmountExclGST_unrounded, None)
        self.assertEqual(self.invoice.cache_invoiceAmountInclGST_unrounded, None)

        # Check correct value returned
        self.assertEqual(getattr(self.invoice, field)(), value)

        # Check cache fields are not none
        self.assertNotEqual(self.invoice.cache_amountGST_unrounded, None)
        self.assertNotEqual(self.invoice.cache_totalQuantity, None)
        self.assertNotEqual(self.invoice.cache_invoiceAmountExclGST_unrounded, None)
        self.assertNotEqual(self.invoice.cache_invoiceAmountInclGST_unrounded, None)

    def testNone_amountGST(self):
        self.baseTestTotalsNone('amountGST', round(50/11,2))

    def testNone_totalQuantity(self):
        self.baseTestTotalsNone('totalQuantity', 1)

    def testNone_invoiceAmountExclGST(self):
        self.baseTestTotalsNone('invoiceAmountExclGST', round(50/1.1, 2))

    def testNone_invoiceAmountInclGST(self):
        self.baseTestTotalsNone('invoiceAmountInclGST', 50)

    def test_preSave_setsInvoicedDate_noDate(self):
        self.event.paymentDueDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date()
        self.event.save()

        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1)
        self.assertEqual(self.invoice.invoicedDate, self.event.paymentDueDate)

    def test_preSave_setsInvoicedDate_existingDate(self):
        self.event.paymentDueDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date()
        self.event.save()

        self.invoice = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, invoicedDate=(datetime.datetime.now() + datetime.timedelta(days=1)).date())
        self.assertEqual(self.invoice.invoicedDate, (datetime.datetime.now() + datetime.timedelta(days=1)).date())

class TestInvoiceCreation(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    @classmethod
    def setUpTestData(cls):
        commonSetUp(cls)
        cls.freeEvent = Event.objects.create(
            year=cls.year,
            state=cls.state1,
            name='Free event 1',
            eventType='competition',
            status='published',
            maxMembersPerTeam=5,
            entryFeeIncludesGST=True,
            competition_billingType='team',
            competition_defaultEntryFee = 0,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=5)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date(),
            directEnquiriesTo = cls.user1,
        )
        cls.team1 = Team.objects.create(event=cls.freeEvent, school=cls.school1, mentorUser=cls.user3, name='Team 1', division=cls.division1)

    def testFreeEventToPaidCreatesInvoices(self):
        self.assertEqual(Invoice.objects.count(), 0)
        self.freeEvent.competition_defaultEntryFee = 50
        self.freeEvent.save()

        self.assertEqual(Invoice.objects.count(), 1)

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
        self.assertQuerySetEqual(response.context['invoices'], Invoice.objects.none())

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

class TestAmountDueFilter(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
        self.client.login(request=HttpRequest(), username=self.email_superUser, password=self.password)
        self.invoice1 = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.invoice2 = Invoice.objects.create(event=self.event, invoiceToUser=self.user2, school=self.school2)
        Team.objects.create(
            event=self.event,
            school=self.school1,
            mentorUser=self.user1,
            name='New Team',
            division=self.division1,
        )
        Team.objects.create(
            event=self.event,
            school=self.school2,
            mentorUser=self.user2,
            name='New Team 2',
            division=self.division1,
        )

    def testNotFiltered(self):
        response = self.client.get(reverse(f'admin:invoices_invoice_changelist'))
        self.assertContains(response, f'2 Invoices')

    def testPaid(self):
        response = self.client.get(reverse(f'admin:invoices_invoice_changelist')+"?amountDueStatus=True")
        self.assertContains(response, f'0 Invoices')

    def testNotPaid(self):
        response = self.client.get(reverse(f'admin:invoices_invoice_changelist')+"?amountDueStatus=False")
        self.assertContains(response, f'2 Invoices')

    def testNotPaid_invoiceFullyPaid(self):
        InvoicePayment.objects.create(invoice=self.invoice1, amountPaid=50, datePaid=datetime.datetime.now().date())
        response = self.client.get(reverse(f'admin:invoices_invoice_changelist')+"?amountDueStatus=True")
        self.assertContains(response, f'1 Invoice')

    def testNotPaid_invoicePartiallyPaid(self):
        InvoicePayment.objects.create(invoice=self.invoice1, amountPaid=5, datePaid=datetime.datetime.now().date())
        response = self.client.get(reverse(f'admin:invoices_invoice_changelist')+"?amountDueStatus=True")
        self.assertContains(response, f'0 Invoices')

class TestInvoiceAmountFilter(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
        self.client.login(request=HttpRequest(), username=self.email_superUser, password=self.password)
        self.invoice1 = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.invoice2 = Invoice.objects.create(event=self.event, invoiceToUser=self.user2, school=self.school2)
        self.invoice2 = Invoice.objects.create(event=self.event, invoiceToUser=self.user3, school=self.school3)
        Team.objects.create(
            event=self.event,
            school=self.school1,
            mentorUser=self.user1,
            name='New Team',
            division=self.division1,
        )

    def testDefault(self):
        response = self.client.get(reverse(f'admin:invoices_invoice_changelist'))
        self.assertContains(response, f'1 Invoice')

    def testAll(self):
        response = self.client.get(reverse(f'admin:invoices_invoice_changelist')+"?invoiceAmountStatus=all")
        self.assertContains(response, f'3 Invoices')

    def testZero(self):
        response = self.client.get(reverse(f'admin:invoices_invoice_changelist')+"?invoiceAmountStatus=zero")
        self.assertContains(response, f'2 Invoice')
