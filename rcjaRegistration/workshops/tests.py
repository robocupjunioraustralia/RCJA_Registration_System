from django.test import TestCase
from django.urls import reverse
from django.http import HttpRequest
from django.core.exceptions import ValidationError

from invoices.models import InvoiceGlobalSettings, Invoice, InvoicePayment
from users.models import User
from regions.models import State, Region
from schools.models import School, SchoolAdministrator, Campus
from events.models import Event, Year, Division, AvailableDivision
from coordination.models import Coordinator
from .models import WorkshopAttendee

import datetime

# Create your tests here.

def newCommonSetUp(self):
        self.user1 = User.objects.create_user(email=self.email1, password=self.password)

        self.state1 = State.objects.create(typeRegistration=True, name='Victoria', abbreviation='VIC')
        self.state2 = State.objects.create(typeRegistration=True, name='NSW', abbreviation='NSW')
        self.region1 = Region.objects.create(name='Test Region', description='test desc')

        self.user2 = User.objects.create_user(email=self.email2, password=self.password, homeState=self.state1)
        self.user3 = User.objects.create_user(email=self.email3, password=self.password)
        self.superUser = User.objects.create_user(email=self.email_superUser, password=self.password, is_superuser=True, is_staff=True)

        self.school1 = School.objects.create(name='School 1', abbreviation='sch1', state=self.state1, region=self.region1)
        self.school2 = School.objects.create(name='School 2', abbreviation='sch2', state=self.state1, region=self.region1)
        self.school3 = School.objects.create(name='School 3', abbreviation='sch3', state=self.state2, region=self.region1)

        self.campus1 = Campus.objects.create(school=self.school1, name='Campus 1')
        self.campus2 = Campus.objects.create(school=self.school1, name='Campus 2')

        self.year = Year.objects.create(year=2020)
        self.event = Event.objects.create(
            year=self.year,
            state=self.state1,
            name='Test event 1',
            eventType='workshop',
            status='published',
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
        self.division4 = Division.objects.create(name='Division 4', state=self.state2)

        self.invoiceSettings = InvoiceGlobalSettings.objects.create(
            invoiceFromName='From Name',
            invoiceFromDetails='Test Details Text',
            invoiceFooterMessage='Test Footer Text',
        )

class TestWorkshopAttendeeClean(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        newCommonSetUp(self)

        self.attendee1 = WorkshopAttendee(
            event=self.event,
            mentorUser=self.user1,
            school=self.school1,
            division=self.division1,
            attendeeType='teacher',
            firstName='First1',
            lastName='Last1',
            yearLevel='10',
            gender='male',
            email='test@test.com'
        )
        self.attendee2 = WorkshopAttendee(
            event=self.event,
            mentorUser=self.user1,
            school=self.school2,
            division=self.division1,
            attendeeType='student',
            firstName='First2',
            lastName='Last2',
            yearLevel='10',
            gender='male',
            birthday=datetime.datetime.today()
        )

        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user1)
        self.schoolAdmin2 = SchoolAdministrator.objects.create(school=self.school2, user=self.user1)

    # Base event attendance components

    def testWrongEventType(self):
        self.event.eventType = 'competition'
        self.event.save()

        self.assertRaises(ValidationError, self.attendee1.clean)

    def testNoCampus(self):
        self.assertEqual(self.attendee1.clean(), None)

    def testCampusValid(self):
        self.attendee1.campus = self.campus1
        self.assertEqual(self.attendee1.clean(), None)

    def testCampusWrongSchool(self):
        self.attendee2.campus = self.campus1
        self.assertRaises(ValidationError, self.attendee2.clean)

    def testDivisionWrongState(self):
        self.attendee1.division = self.division4
        self.assertRaises(ValidationError, self.attendee1.clean)     

    def testCheckMentorIsAdminOfSchool_noSchool(self):
        self.attendee3 = WorkshopAttendee(
            event=self.event,
            mentorUser=self.user1,
            division=self.division1,
            attendeeType='teacher',
            firstName='First3',
            lastName='Last3',
            yearLevel='10',
            gender='male',
            email='test@test.com'
        )
        self.assertEqual(self.attendee3.clean(), None)

    def testCheckMentorIsAdminOfSchool(self):
        self.attendee3 = WorkshopAttendee(
            event=self.event,
            mentorUser=self.user1,
            school=self.school1,
            division=self.division1,
            attendeeType='teacher',
            firstName='First3',
            lastName='Last3',
            yearLevel='10',
            gender='male',
            email='test@test.com'
        )
        self.assertEqual(self.attendee3.clean(), None)

    def testCheckMentorIsAdminOfSchool_existing(self):
        self.schoolAdmin1.delete()
        self.attendee3 = WorkshopAttendee.objects.create(
            event=self.event,
            mentorUser=self.user1,
            school=self.school1,
            division=self.division1,
            attendeeType='teacher',
            firstName='First3',
            lastName='Last3',
            yearLevel='10',
            gender='male',
            email='test@test.com'
        )
        self.assertEqual(self.attendee3.clean(), None)

    def testCheckMentorIsAdminOfSchool_notAdmin(self):
        self.schoolAdmin1.delete()
        self.attendee3 = WorkshopAttendee(
            event=self.event,
            mentorUser=self.user1,
            school=self.school1,
            division=self.division1,
            attendeeType='teacher',
            firstName='First3',
            lastName='Last3',
            yearLevel='10',
            gender='male',
            email='test@test.com'
        )
        self.assertRaises(ValidationError, self.attendee3.clean)

    # Workshop components

    def testTeacherMissingEmail(self):
        self.attendee3 = WorkshopAttendee(
            event=self.event,
            mentorUser=self.user1,
            school=self.school1,
            division=self.division1,
            attendeeType='teacher',
            firstName='First1',
            lastName='Last1',
            yearLevel='10',
            gender='male',
        )
        self.assertRaises(ValidationError, self.attendee3.clean)

    def testStudentMissingBirthday(self):
        self.attendee3 = WorkshopAttendee(
            event=self.event,
            mentorUser=self.user1,
            school=self.school1,
            division=self.division1,
            attendeeType='student',
            firstName='First1',
            lastName='Last1',
            yearLevel='10',
            gender='male',
        )
        self.assertRaises(ValidationError, self.attendee3.clean)

    def testTeacherValidYearLevel(self):
        self.attendee3 = WorkshopAttendee(
            event=self.event,
            mentorUser=self.user1,
            school=self.school1,
            division=self.division1,
            attendeeType='teacher',
            firstName='First1',
            lastName='Last1',
            yearLevel='3,5-7',
            gender='male',
            email='test@test.com'
        )
        self.assertEqual(self.attendee3.clean(), None)

    def testTeacherInvalidYearLevel(self):
        self.attendee3 = WorkshopAttendee(
            event=self.event,
            mentorUser=self.user1,
            school=self.school1,
            division=self.division1,
            attendeeType='teacher',
            firstName='First1',
            lastName='Last1',
            yearLevel='10a',
            gender='male',
            email='test@test.com'
        )
        self.assertRaises(ValidationError, self.attendee3.clean)

    def testStudentValidYearLevel(self):
        self.attendee3 = WorkshopAttendee(
            event=self.event,
            mentorUser=self.user1,
            school=self.school1,
            division=self.division1,
            attendeeType='student',
            firstName='First1',
            lastName='Last1',
            yearLevel='9',
            gender='male',
            birthday=datetime.datetime.today()
        )
        self.assertEqual(self.attendee3.clean(), None)

    def testStudentInvalidYearLevel(self):
        self.attendee3 = WorkshopAttendee(
            event=self.event,
            mentorUser=self.user1,
            school=self.school1,
            division=self.division1,
            attendeeType='student',
            firstName='First1',
            lastName='Last1',
            yearLevel='3-5',
            gender='male',
            birthday=datetime.datetime.today()
        )
        self.assertRaises(ValidationError, self.attendee3.clean)

class TestWorkshopAttendeeCreateFrontend(TestCase): #TODO more comprehensive tests, check teams actually saved to db properly
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        newCommonSetUp(self)
        self.event.divisions.add(self.division1)
        self.closedEvent = Event.objects.create(
            year=self.year,
            state=self.state1,
            name='Test event 2',
            eventType='workshop',
            status='published',
            maxMembersPerTeam=5,
            entryFeeIncludesGST=True,
            event_billingType='team',
            event_defaultEntryFee = 50,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=5)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            directEnquiriesTo = self.user1,
        )
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

    def testOpenRegoDoesLoad(self):
        response = self.client.get(reverse('workshops:create',kwargs={'eventID':self.event.id}))
        self.assertEqual(200, response.status_code)

    def testClosedRegoReturnsError_get(self):
        response = self.client.get(reverse('workshops:create', kwargs={'eventID':self.closedEvent.id}))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Registration has closed for this event', status_code=403)

    def testCompetitionReturnsError_get(self):
        self.event.eventType = 'competition'
        self.event.save()

        response = self.client.get(reverse('workshops:create', kwargs={'eventID':self.event.id}))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Teams/ attendees cannot be created for this event type', status_code=403)

    def testWorkingAttendeeCreate(self):
        numberAttendees = WorkshopAttendee.objects.count()
        payload = {
            'division':self.division1.id,
            'attendeeType':'teacher',
            'firstName':'First1',
            'lastName':'Last1',
            'yearLevel':'10',
            'gender':'male',
            'email':'test@test.com'
        }
        response = self.client.post(reverse('workshops:create',kwargs={'eventID':self.event.id}),data=payload,follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/events/{self.event.id}")
        self.assertEqual(WorkshopAttendee.objects.count(), numberAttendees+1)

    def testWorkingAttendeeCreate_addAnother(self):
        numberAttendees = WorkshopAttendee.objects.count()
        payload = {
            'division':self.division1.id,
            'attendeeType':'teacher',
            'firstName':'First1',
            'lastName':'Last1',
            'yearLevel':'10',
            'gender':'male',
            'email':'test@test.com',
            'add_text': 'blah',
        }
        response = self.client.post(reverse('workshops:create', kwargs={'eventID':self.event.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/workshopattendee/create/{self.event.id}")
        self.assertEqual(WorkshopAttendee.objects.count(), numberAttendees+1)
