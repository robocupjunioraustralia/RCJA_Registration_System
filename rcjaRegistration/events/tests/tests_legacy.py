from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.http import HttpRequest

from regions.models import State,Region
from schools.models import School, SchoolAdministrator
from teams.models import Team, Student
from events.models import Event, Division, Year, AvailableDivision, Venue, DivisionCategory
from users.models import User
from coordination.models import Coordinator
from eventfiles.models import EventAvailableFileType, MentorEventFileType
from invoices.models import Invoice, InvoiceGlobalSettings
from events.views import getAdminCompSummary, getAdminWorkSummary
from workshops.models import WorkshopAttendee

import datetime
# Create your tests here.


def commonSetUp(obj):
    obj.username = 'user@user.com'
    obj.password = 'password'
    obj.user = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=obj.username, password=obj.password)
    obj.newState = State.objects.create(
        typeCompetition=True, typeUserRegistration=True,
        name='Victoria',
        abbreviation='VIC'
    )
    obj.state2 = State.objects.create(
        typeCompetition=True, typeUserRegistration=True,
        name='New South Wales',
        abbreviation='NSW'
    )
    obj.globalState = State.objects.create(
        typeCompetition=True, typeUserRegistration=True, typeGlobal = True,
        name='National',
        abbreviation='NAT'
    )
    obj.newRegion = Region.objects.create(
        name='Test Region',
        description='test desc'
    )
    obj.newSchool = School.objects.create(
        name='Melbourne High',
        abbreviation='MHS',
        state=obj.newState,
        region=obj.newRegion
    )
    obj.schoolAdministrator = SchoolAdministrator.objects.create(
        school=obj.newSchool,
        user=obj.user
    )
    obj.year = Year.objects.create(year=2019)
    obj.divCategory = DivisionCategory.objects.create(name='Test')
    obj.division = Division.objects.create(name='test',category = obj.divCategory)

    obj.oldEvent = Event.objects.create(
        year=obj.year,
        state=obj.newState,
        name='test old not reg',
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        event_defaultEntryFee = 4,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
        directEnquiriesTo = obj.user     
    )
    obj.oldEvent.divisions.add(obj.division)

    obj.registrationNotOpenYetEvent = Event.objects.create(
        year=obj.year,
        state=obj.newState,
        name='future event',
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        event_defaultEntryFee = 4,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=10)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=10)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
        directEnquiriesTo = obj.user     
    )
    obj.registrationNotOpenYetEvent.divisions.add(obj.division)

    obj.newEvent = Event.objects.create(
        year=obj.year,
        state=obj.newState,
        name='test new yes reg',
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        event_defaultEntryFee = 4,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=3)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=4)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-2)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=+2)).date(),
        directEnquiriesTo = obj.user     
    )
    obj.newEvent.divisions.add(obj.division)

    obj.oldEventWithTeams = Event.objects.create(
        year=obj.year,
        state=obj.newState,
        name='test old yes reg',
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        event_defaultEntryFee = 4,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=-3)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=-4)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-6)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
        directEnquiriesTo = obj.user     
    )
    obj.oldEventWithTeams.divisions.add(obj.division)
    obj.oldeventTeam = Team.objects.create(event=obj.oldEventWithTeams, division=obj.division, school=obj.newSchool, mentorUser=obj.user, name='test')
    obj.oldTeamStudent = Student.objects.create(team=obj.oldeventTeam,firstName='test',lastName='old',yearLevel=1,gender='Male')

    obj.newEventTeam = Team.objects.create(event=obj.newEvent, division=obj.division, school=obj.newSchool, mentorUser=obj.user, name='test new team')
    obj.newTeamStudent = Student.objects.create(team=obj.newEventTeam,firstName='test',lastName='new',yearLevel=1,gender='Male')

    obj.invoiceSettings = InvoiceGlobalSettings.objects.create(
        invoiceFromName='From Name',
        invoiceFromDetails='Test Details Text',
        invoiceFooterMessage='Test Footer Text',
    )

class TestEventPermissions(TestCase):
    def setUp(self):
        commonSetUp(self)

    def testDashboardLoginRequired(self):
        url = reverse('events:dashboard')
    
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Login")
    
        response = self.client.get(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/")
        self.assertEqual(response.status_code, 302)

    def testDetailsLoginRequired(self):
        url = reverse('events:details', kwargs= {'eventID':self.newEvent.id})
    
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Login")
    
        response = self.client.get(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/events/{self.newEvent.id}")
        self.assertEqual(response.status_code, 302)

class TestUnderConstruction(TestCase):
    def setUp(self):
        commonSetUp(self)
        self.client.login(request=HttpRequest(), username=self.username, password=self.password)

    def testPageLoad(self):
        response = self.client.get(reverse('events:loggedInConstruction'))
        self.assertEqual(response.status_code, 200)

    def testUsesCorrectTemplate(self):
        response = self.client.get(reverse('events:loggedInConstruction'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'common/loggedInUnderConstruction.html')

class TestDashboard_school(TestCase): #TODO more comprehensive tests
    def setUp(self):
        commonSetUp(self)
        self.client.login(request=HttpRequest(), username=self.username, password=self.password)

    def testPageLoad(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 200)

    def testNonSignedUpOldDoesNotLoad(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertNotContains(response, 'test old not reg')

    def testNewEventWithRegoLoads(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertContains(response, 'test new yes reg')

    def testNewEventWithoutRegoLoads(self):
        self.newEventTeam.delete()
        response = self.client.get(reverse('events:dashboard'))
        self.assertContains(response, 'test new yes reg')

    def testNewEventOtherStateNotLoad(self):
        self.newEventTeam.delete()
        self.newEvent.state = self.state2
        self.newEvent.save()
        response = self.client.get(reverse('events:dashboard'))
        self.assertNotContains(response, 'test new yes reg')

    def testNewEventOtherStateGlobalEventLoad(self):
        self.newEventTeam.delete()
        self.newEvent.state = self.state2
        self.newEvent.globalEvent = True
        self.newEvent.save()
        response = self.client.get(reverse('events:dashboard'))
        self.assertContains(response, 'test new yes reg')

    def testNewEventGlobalStateLoad(self):
        self.newEventTeam.delete()
        self.newEvent.state = self.globalState
        self.newEvent.save()
        response = self.client.get(reverse('events:dashboard'))
        self.assertContains(response, 'test new yes reg')

    def testOldEventWithTeamsLoad(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertContains(response, 'test old yes reg')

    def testCorrectInteraction(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertContains(response, 'You are currently interacting as Melbourne High.')

    def testUsesCorrectTemplate(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/dashboard.html')

class TestDashboard_independent(TestDashboard_school):
    def setUp(self):
        commonSetUp(self)
        self.client.login(request=HttpRequest(), username=self.username, password=self.password)
        self.schoolAdministrator.delete()
        self.user.homeState = self.newState
        self.user.save()

    def testNewEventWithRegoLoads(self):
        self.team2 = Team.objects.create(event=self.newEvent, division=self.division, mentorUser=self.user, name='test new team 2')
        super().testNewEventWithRegoLoads()

    def testOldEventWithTeamsLoad(self):
        self.team1 = Team.objects.create(event=self.oldEventWithTeams, division=self.division, mentorUser=self.user, name='test 2')
        super().testOldEventWithTeamsLoad()

    def testSchoolTeamsNotPresent(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertNotContains(response, 'test old yes reg')

    def testStateFiltering_filtered(self):
        self.user.homeState = None
        self.user.save()
        response = self.client.get(reverse('events:dashboard'))
        self.assertNotContains(response, 'test new yes reg')

    def testStateFiltering_all(self):
        self.user.homeState = None
        self.user.save()
        response = self.client.get(reverse('events:dashboard'), {'viewAll': 'yes'})
        self.assertContains(response, 'test new yes reg')

    def testCorrectInteraction(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertContains(response, 'You are currently interacting as independent.')

    # Need to test events are sorted
    # Need to test invoices are properly filtered

class TestEventDetailsPage_school(TestCase):
    def setUp(self):
        commonSetUp(self)
        self.client.login(request=HttpRequest(), username=self.username, password=self.password)

    def testPageLoad(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.newEvent.id}))
        self.assertEqual(response.status_code, 200)

    def testUsesCorrectTemplate(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.newEvent.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/details.html')

    def testEventTitlePresent(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.newEvent.id}))
        self.assertContains(response, 'test new yes reg')

    def testTeamNamePresent(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.newEvent.id}))
        self.assertContains(response, 'test new team')

    def testNotPublished_denied_get(self):
        self.newEvent.status = "draft"
        self.newEvent.save()
        self.newEventTeam.delete()

        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.newEvent.id}))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'This event is unavailable', status_code=403)

    def testOldEventPermissionDenied(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.oldEvent.id}))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response,'This event is unavailable', status_code=403)

    def testCreationButtonsVisibleWhenRegoOpen(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.newEvent.id}))
        self.assertNotContains(response,'Registration for this event has closed.')
        self.assertContains(response, 'Add team')

    def testLoadsClosedRegoWithTeams(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.oldEventWithTeams.id}))
        self.assertEqual(response.status_code, 200)

    def testCorrectMessage_ClosedRegoWithTeams(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.oldEventWithTeams.id}))
        self.assertContains(response, 'Registration for this event has closed.')

    def testDeniedUnpublishedClosedRegoWithTeams(self):
        self.oldEventWithTeams.status = 'draft'
        self.oldEventWithTeams.save()

        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.oldEventWithTeams.id}))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'This event is unavailable', status_code=403)

    def testCreationButtonsNotVisibleWhenRegoClosed(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.oldEventWithTeams.id}))
        self.assertContains(response,'Registration for this event has closed.')
        self.assertNotContains(response, 'Add team')

    def testCorrectTeams(self):
        self.school2 = School.objects.create(
            name='School 2',
            abbreviation='sch2',
            state=self.newState,
            region=self.newRegion
        )
        self.user2 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email='user2@user.com', password=self.password)

        # Already one team for this user in common setup
        # Teams that should be visible
        self.team1 = Team.objects.create(event=self.newEvent, division=self.division, school=self.newSchool, mentorUser=self.user2, name='Team 1')

        # Teams that should not be visible
        self.team2 = Team.objects.create(event=self.newEvent, division=self.division, school=self.school2, mentorUser=self.user2, name='Team 2') # Wrong school
        self.team3 = Team.objects.create(event=self.newEvent, division=self.division, mentorUser=self.user, name='Team 3') # No school

        url = reverse('events:details', kwargs= {'eventID':self.newEvent.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Team 1')
        self.assertNotContains(response, 'Team 2')
        self.assertNotContains(response, 'Team 3')

        self.assertEqual(response.context['teams'].count(), 2)

        for team in response.context['teams']:
            assert team.school == self.user.currentlySelectedSchool, 'No permission to view this team'

    def testPageLoad_registrationNotOpenYetEvent(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.registrationNotOpenYetEvent.id}))
        self.assertEqual(response.status_code, 200)

    def testCorrectMessage_registrationNotOpenYetEvent(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.registrationNotOpenYetEvent.id}))
        self.assertContains(response, "Registration for this event hasn't opened yet.")

class TestEventDetailsPage_independent(TestEventDetailsPage_school):
    def setUp(self):
        commonSetUp(self)
        self.client.login(request=HttpRequest(), username=self.username, password=self.password)
        self.schoolAdministrator.delete()
        self.team = Team.objects.create(event=self.newEvent, division=self.division, mentorUser=self.user, name='test new team ind')

    def testTeamNamePresent(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.newEvent.id}))
        self.assertContains(response, 'test new team ind')

    def testNotPublished_denied_get(self):
        self.newEvent.status = "draft"
        self.newEvent.save()
        self.team.delete()

        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.newEvent.id}))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'This event is unavailable', status_code=403)

    def testLoadsClosedRegoWithTeams(self):
        self.oldTeam = Team.objects.create(event=self.oldEventWithTeams, division=self.division, mentorUser=self.user, name='test old team ind')

        super().testLoadsClosedRegoWithTeams()

    def testCorrectMessage_ClosedRegoWithTeams(self):
        self.oldTeam = Team.objects.create(event=self.oldEventWithTeams, division=self.division, mentorUser=self.user, name='test old team ind')

        super().testCorrectMessage_ClosedRegoWithTeams()

    def testDeniedUnpublishedClosedRegoWithTeams(self):
        self.oldTeam = Team.objects.create(event=self.oldEventWithTeams, division=self.division, mentorUser=self.user, name='test old team ind')

        super().testDeniedUnpublishedClosedRegoWithTeams()

    def testCreationButtonsNotVisibleWhenRegoClosed(self):
        self.oldTeam = Team.objects.create(event=self.oldEventWithTeams, division=self.division, mentorUser=self.user, name='test old team ind')

        super().testCreationButtonsNotVisibleWhenRegoClosed()

    def testCorrectTeams(self):
        self.school2 = School.objects.create(
            name='School 2',
            abbreviation='sch2',
            state=self.newState,
            region=self.newRegion
        )
        self.user2 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email='user2@user.com', password=self.password)

        # Already one team for this user in common setup
        # Teams that should be visible
        self.team1 = Team.objects.create(event=self.newEvent, division=self.division, mentorUser=self.user, name='Team 1')

        # Teams that should not be visible
        self.team2 = Team.objects.create(event=self.newEvent, division=self.division, school=self.school2, mentorUser=self.user2, name='Team 2') # Has a school
        self.team3 = Team.objects.create(event=self.newEvent, division=self.division, mentorUser=self.user2, name='Team 3') # Wrong mentor

        url = reverse('events:details', kwargs= {'eventID':self.newEvent.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Team 1')
        self.assertNotContains(response, 'Team 2')
        self.assertNotContains(response, 'Team 3')

        self.assertEqual(response.context['teams'].count(), 2)

        for team in response.context['teams']:
            assert team.school is None and team.mentorUser == self.user, 'No permission to view this team'

class TestEventDetailsPage_superuser(TestCase):
    def setUp(self):
        commonSetUp(self)
        self.user.is_superuser = True
        self.user.save()
        self.client.login(request=HttpRequest(), username=self.username, password=self.password)

    def testPageLoad(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.newEvent.id}))
        self.assertEqual(response.status_code, 200)

    def testUsesCorrectTemplate(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.newEvent.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/details.html')

    def testEventTitlePresent(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.newEvent.id}))
        self.assertContains(response, 'test new yes reg')

    def testTeamNamePresent(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.newEvent.id}))
        self.assertContains(response, 'test new team')

    def testNotPublishedLoad(self):
        self.newEvent.status = "draft"
        self.newEvent.save()
        self.newEventTeam.delete()

        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.newEvent.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Event is not published.')

    def testOldEventLoad(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.oldEvent.id}))
        self.assertEqual(response.status_code, 200)

class TestEventClean(TestCase):
    def setUp(self):
        commonSetUp(self)
        self.division1 = Division.objects.create(name='Division 1')
        self.division2 = Division.objects.create(name='Division 2', state=self.newState)
        self.event = Event(
            year=self.year,
            state=self.newState,
            name='Event 1',
            status='published',
            maxMembersPerTeam=5,
            event_defaultEntryFee = 4,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            directEnquiriesTo = self.user     
        )
        self.state2 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name="State 2", abbreviation='ST2')
        self.venue1 = Venue.objects.create(name='Venue 1', state=self.newState)
        self.venue2 = Venue.objects.create(name='Venue 2', state=self.state2)

    # Status validation
    def testStatusPublished(self):
        self.event.status = 'published'
        self.event.clean()

    def testStatusDraft(self):
        self.event.status = 'draft'
        self.event.clean()

    def testStatusDraftTeamExists(self):
        self.event.status = 'draft'
        self.event.clean()
        self.event.save()
        Team.objects.create(event=self.event, division=self.division, mentorUser=self.user, name='New Test Team')
        self.assertRaises(ValidationError, self.event.clean)

    # Dates validation

    def teststartDateNoneInvalid(self):
        self.event.startDate = None
        self.assertRaises(ValidationError, self.event.clean)

    def testendDateNoneInvalid(self):
        self.event.endDate = None
        self.assertRaises(ValidationError, self.event.clean)

    def testRegistrationsOpenDateNoneInvalid(self):
        self.event.registrationsOpenDate = None
        self.assertRaises(ValidationError, self.event.clean)

    def testRegistrationsCloseDateNoneInvalid(self):
        self.event.registrationsCloseDate = None
        self.assertRaises(ValidationError, self.event.clean)

    def testMultidayEventOK(self):
        self.event.clean()

    def testSingleDayEventOK(self):
        self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+5)).date()
        self.event.clean()

    def testStartBeforeEnd(self):
        self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+4)).date()
        self.assertRaises(ValidationError, self.event.clean)

    def testRegistrationOpenBeforeClose(self):
        self.event.startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date()
        self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date()
        self.event.registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-3)).date()
        self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-4)).date()
        self.assertRaises(ValidationError, self.event.clean)

    def testOneDayRegistration(self):
        self.event.registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-3)).date()
        self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-3)).date()
        self.event.clean()

    def testRegistrationCloseOnEventStartDate(self):
        self.event.startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date()
        self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date()
        self.event.registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-3)).date()
        self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=+5)).date()
        self.event.clean()

    def testRegistrationCloseAfterEventStartDate(self):
        self.event.startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date()
        self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date()
        self.event.registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-3)).date()
        self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date()
        self.assertRaises(ValidationError, self.event.clean)

    # Billing settings validation

    def testSpecialRateValidComplete(self):
        self.event.event_specialRateFee = 50
        self.event.event_specialRateNumber = 5
        self.event.clean()

    def testSpecialRateInvalid(self):
        self.event.event_specialRateFee = 50
        self.assertRaises(ValidationError, self.event.clean)

    def testSpecialRateStudentInvalid(self):
        self.event.event_specialRateFee = 50
        self.event.event_specialRateNumber = 5
        self.event.clean()

        self.event.event_billingType = 'student'
        self.assertRaises(ValidationError, self.event.clean)
    
    def testSpecialRateBillingAvailableDivisionValid(self):
        self.event.save()
        self.availableDivision = AvailableDivision.objects.create(event=self.event, division=self.division1)
        self.event.event_specialRateFee = 50
        self.event.event_specialRateNumber = 5
        self.event.clean()

    def testSpecialRateBillingAvailableDivisionInValid(self):
        self.event.save()
        self.availableDivision = AvailableDivision.objects.create(event=self.event, division=self.division1)
        self.event.event_specialRateFee = 50
        self.event.event_specialRateNumber = 5
        self.event.clean()

        self.availableDivision.division_billingType = 'team'
        self.availableDivision.division_entryFee = 50
        self.availableDivision.save()

        self.assertRaises(ValidationError, self.event.clean)

    # Test state validations

    def testVenueStateSuccess(self):
        self.event.venue = self.venue1
        self.event.clean()

    def testVenueFailureWrongVenueState(self):
        self.event.venue = self.venue2
        self.assertRaises(ValidationError, self.event.clean)

    def testAvailableDivisionSuccessNoPk(self):
        self.assertEqual(self.event.pk, None)
        self.event.clean()

    def testAvailableDivisionSuccessExistingEvent(self):
        self.event.save()
        self.assertNotEqual(self.event.pk, None)

        self.availableDivision = AvailableDivision.objects.create(event=self.event, division=self.division2)
        self.event.clean()

    def testAvailableDivision_StateChangeSuccess(self):
        self.event.save()
        self.assertNotEqual(self.event.pk, None)

        self.event.state = self.state2
        self.event.clean()

    def testAvailableDivision_StateChangeFailure(self):
        self.event.save()
        self.assertNotEqual(self.event.pk, None)

        self.availableDivision = AvailableDivision.objects.create(event=self.event, division=self.division2)
        self.event.state = self.state2
        self.assertRaises(ValidationError, self.event.clean)

    # Test file upload deadline checking

    def testSuccessCleanWithAvailableEventFile(self):
        self.fileType1 = MentorEventFileType.objects.create(name="File Type 1")
        self.event.save()
        self.availableFileType1 = EventAvailableFileType.objects.create(event=self.event, fileType=self.fileType1, uploadDeadline=(datetime.datetime.now() + datetime.timedelta(days=4)).date())
        self.availableFileType1.save()
        self.assertEqual(self.event.clean(), None)

    def testUploadDeadlineBeforeRegistrationClose(self):
        self.fileType1 = MentorEventFileType.objects.create(name="File Type 1")
        self.event.save()
        self.availableFileType1 = EventAvailableFileType.objects.create(event=self.event, fileType=self.fileType1, uploadDeadline=self.event.registrationsCloseDate + datetime.timedelta(days=-1))
        self.availableFileType1.save()
        self.assertRaises(ValidationError, self.event.clean)

    def testUploadDeadlineAfterStartDate(self):
        self.fileType1 = MentorEventFileType.objects.create(name="File Type 1")
        self.event.save()
        self.availableFileType1 = EventAvailableFileType.objects.create(event=self.event, fileType=self.fileType1, uploadDeadline=self.event.startDate + datetime.timedelta(days=1))
        self.availableFileType1.save()
        self.assertRaises(ValidationError, self.event.clean)

class TestEventMethods(TestCase):
    def setUp(self):
        commonSetUp(self)
        self.division1 = Division.objects.create(name='Division 1')
        self.event = Event.objects.create(
            year=self.year,
            state=self.newState,
            name='Event 1',
            status='published',
            maxMembersPerTeam=5,
            event_defaultEntryFee = 4,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            directEnquiriesTo = self.user     
        )

        self.user.first_name = 'First'
        self.user.last_name = 'Last'
        self.user.save()

    def testGetState(self):
        self.assertEqual(self.event.getState(), self.newState)

    def testBoolWorkshop_notWorkshop(self):
        self.event.eventType = 'competition'
        self.assertEqual(self.event.boolWorkshop(), False)

    def testBoolWorkshop_isWorkshop(self):
        self.event.eventType = 'workshop'
        self.assertEqual(self.event.boolWorkshop(), True)

    def testSave_competition(self):
        self.event.eventType = 'competition'
        self.event.event_billingType = 'student'
        self.assertEqual(self.event.maxMembersPerTeam, 5)
        self.assertEqual(self.event.event_billingType, 'student')

        self.event.save()
        self.assertEqual(self.event.maxMembersPerTeam, 5)
        self.assertEqual(self.event.event_billingType, 'student')

    def testSave_workshop(self):
        self.event.eventType = 'workshop'
        self.event.event_billingType = 'student'
        self.assertEqual(self.event.maxMembersPerTeam, 5)
        self.assertEqual(self.event.event_billingType, 'student')

        self.event.save()
        self.assertEqual(self.event.maxMembersPerTeam, 0)
        self.assertEqual(self.event.event_billingType, 'team')

    def testStr_state(self):
        self.assertEqual(str(self.event), "Event 1 2019 (VIC)")

    def testStr_global(self):
        self.event.globalEvent = True
        self.assertEqual(str(self.event), "Event 1 2019")

    def testStr_globalState(self):
        self.event.state.typeGlobal = True
        self.assertEqual(str(self.event), "Event 1 2019")

    def testDirectEnquiriesToName(self):
        self.assertEqual(self.event.directEnquiriesToName(), 'First Last')

    def testDirectEnquiriesToEmail(self):
        self.assertEqual(self.event.directEnquiriesToEmail(), self.username)

    def testBleachedEventDetails(self):
        self.event.eventDetails = "<b>Hello</b> <h1>Heading</h1> <script>"
        self.event.save()

        self.assertIn('<b>Hello</b>', self.event.bleachedEventDetails())
        self.assertNotIn('<h1>Heading</h1>', self.event.bleachedEventDetails())
        self.assertNotIn('<script>', self.event.bleachedEventDetails())

        self.assertNotIn('<h1>', self.event.bleachedEventDetails())
        self.assertIn('&lt;h1&gt;', self.event.bleachedEventDetails())

    def testPaidEvent_defaultEntryFee(self):
        self.assertTrue(self.event.paidEvent())

    def testPaidEvent_free(self):
        self.event.event_defaultEntryFee = 0
        self.assertFalse(self.event.paidEvent())

    def testPaidEvent_specialRateFee(self):
        self.event.event_defaultEntryFee = 0
        self.event.event_specialRateFee = 5
        self.assertTrue(self.event.paidEvent())

    def testPaidEvent_free_withDivision(self):
        self.event.event_defaultEntryFee = 0
        self.availableDivision = AvailableDivision.objects.create(event=self.event, division=self.division1)

        self.assertFalse(self.event.paidEvent())

    def testPaidEvent_division_entryFee(self):
        self.event.event_defaultEntryFee = 0
        self.availableDivision = AvailableDivision.objects.create(event=self.event, division=self.division1)
        self.availableDivision.division_entryFee = 5
        self.availableDivision.save()

        self.assertTrue(self.event.paidEvent())

    def testPaidEvent_workshop_studentEntryFee(self):
        self.event.eventType = 'workshop'
        self.event.event_defaultEntryFee = 0
        self.event.workshopStudentEntryFee = 5
        self.assertTrue(self.event.paidEvent())

    def testPaidEvent_workshop_teacherEntryFee(self):
        self.event.eventType = 'workshop'
        self.event.event_defaultEntryFee = 0
        self.event.workshopTeacherEntryFee = 5
        self.assertTrue(self.event.paidEvent())

    def test_published_draft(self):
        self.event.status = 'draft'
        self.assertFalse(self.event.published())

    def test_published_published(self):
        self.assertTrue(self.event.published())

    def test_registrationsOpen_open(self):
        self.event.registrationsOpenDate = (datetime.datetime.now()).date()
        self.event.registrationsCloseDate = (datetime.datetime.now()).date()
        self.assertTrue(self.event.registrationsOpen())

    def test_registrationsOpen_notOpenYet(self):
        self.event.registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
        self.assertFalse(self.event.registrationsOpen())

    def test_registrationsOpen_closed(self):
        self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date()
        self.assertFalse(self.event.registrationsOpen())

    def test_registrationNotOpenYet_open(self):
        self.event.registrationsOpenDate = (datetime.datetime.now()).date()
        self.event.registrationsCloseDate = (datetime.datetime.now()).date()
        self.assertFalse(self.event.registrationNotOpenYet())

    def test_registrationNotOpenYet_notOpenYet(self):
        self.event.registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
        self.assertTrue(self.event.registrationNotOpenYet())

    def test_registrationNotOpenYet_closed(self):
        self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date()
        self.assertFalse(self.event.registrationNotOpenYet())

    def test_checkBillingDetailsChanged_notChanged(self):
        self.assertFalse(self.event.checkBillingDetailsChanged())

    def test_checkBillingDetailsChanged_newEvent(self):
        self.unsavedEvent = Event(
            year=self.year,
            state=self.newState,
            name='Unsaved Event',
            eventType='competition',
            status='published',
            maxMembersPerTeam=5,
            event_defaultEntryFee = 4,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=3)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=4)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-2)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=+2)).date(),
            directEnquiriesTo = self.user     
        )

        self.assertFalse(self.unsavedEvent.checkBillingDetailsChanged())

    def test_checkBillingDetailsChanged_entryFeeIncludesGST(self):
        self.event.entryFeeIncludesGST = False
        self.assertTrue(self.event.checkBillingDetailsChanged())

    def test_checkBillingDetailsChanged_event_defaultEntryFee(self):
        self.event.event_defaultEntryFee = 6
        self.assertTrue(self.event.checkBillingDetailsChanged())

    def test_checkBillingDetailsChanged_event_billingType(self):
        self.event.event_billingType = 'student'
        self.assertTrue(self.event.checkBillingDetailsChanged())

    def test_checkBillingDetailsChanged_event_specialRateNumber(self):
        self.event.event_specialRateNumber = 10
        self.assertTrue(self.event.checkBillingDetailsChanged())

    def test_checkBillingDetailsChanged_event_specialRateFee(self):
        self.event.event_specialRateFee = 50
        self.assertTrue(self.event.checkBillingDetailsChanged())

    def test_checkBillingDetailsChanged_workshopTeacherEntryFee(self):
        self.event.workshopTeacherEntryFee = 50
        self.assertTrue(self.event.checkBillingDetailsChanged())

    def test_checkBillingDetailsChanged_workshopStudentEntryFee(self):
        self.event.workshopStudentEntryFee = 50
        self.assertTrue(self.event.checkBillingDetailsChanged())

    def test_checkEventConvertedToPaid_notChanged(self):
        self.assertFalse(self.event.checkEventConvertedToPaid())
    
    def test_checkEventConvertedToPaid_newEvent(self):
        self.unsavedEvent = Event(
            year=self.year,
            state=self.newState,
            name='Unsaved Event',
            eventType='competition',
            status='published',
            maxMembersPerTeam=5,
            event_defaultEntryFee = 4,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=3)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=4)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-2)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=+2)).date(),
            directEnquiriesTo = self.user     
        )

        self.assertFalse(self.unsavedEvent.checkEventConvertedToPaid())
    
    def test_checkEventConvertedToPaid_toFree(self):
        self.event.event_defaultEntryFee = 0
        self.assertFalse(self.event.checkEventConvertedToPaid())

    def test_checkEventConvertedToPaid_toPaid(self):
        self.event.event_defaultEntryFee = 0
        self.event.save()

        self.event.event_defaultEntryFee = 5
        self.assertTrue(self.event.checkEventConvertedToPaid())

    def test_preSave_surchageAmount_notSet(self):
        self.invoiceSettings.surchargeAmount = 5
        self.invoiceSettings.save()

        self.invoiceEvent = Event.objects.create(
            year=self.year,
            state=self.newState,
            name='Invoice Event',
            eventType='competition',
            status='published',
            maxMembersPerTeam=5,
            event_defaultEntryFee = 4,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=3)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=4)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-2)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=+2)).date(),
            directEnquiriesTo = self.user     
        )
        self.assertEqual(self.invoiceEvent.eventSurchargeAmount, 5)

    def test_preSave_surchageAmount_set(self):
        self.invoiceSettings.surchargeAmount = 5
        self.invoiceSettings.save()

        self.invoiceEvent = Event.objects.create(
            year=self.year,
            state=self.newState,
            name='Invoice Event',
            eventType='competition',
            status='published',
            maxMembersPerTeam=5,
            event_defaultEntryFee = 4,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=3)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=4)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-2)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=+2)).date(),
            directEnquiriesTo = self.user     
        )
        self.assertEqual(self.invoiceEvent.eventSurchargeAmount, 5)

        # Assert doesn't change after creation
        self.invoiceSettings.surchargeAmount = 10
        self.invoiceSettings.save()

        self.invoiceEvent.save()
        self.invoiceEvent.refresh_from_db()
        self.assertEqual(self.invoiceEvent.eventSurchargeAmount, 5)

    def test_preSave_surchageAmount_noSettings(self):
        self.invoiceSettings.delete()

        self.invoiceEvent = Event.objects.create(
            year=self.year,
            state=self.newState,
            name='Invoice Event',
            eventType='competition',
            status='published',
            maxMembersPerTeam=5,
            event_defaultEntryFee = 4,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=3)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=4)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-2)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=+2)).date(),
            directEnquiriesTo = self.user     
        )
        self.assertEqual(self.invoiceEvent.eventSurchargeAmount, 0)

    def test_surchargeName_exists(self):
        self.invoiceSettings.surchargeName = 'Test Surcharge Name'
        self.invoiceSettings.save()

        self.assertEqual(self.event.surchargeName(), 'Test Surcharge Name')

    def test_surchargeEventDescription_exists(self):
        self.invoiceSettings.surchargeEventDescription = 'Test Surcharge Event Description'
        self.invoiceSettings.save()

        self.assertEqual(self.event.surchargeEventDescription(), 'Test Surcharge Event Description')

    def test_surchargeName_notExists(self):
        self.invoiceSettings.delete()

        self.assertEqual(self.event.surchargeName(), '')

    def test_surchargeEventDescription_notExists(self):
        self.invoiceSettings.delete()

        self.assertEqual(self.event.surchargeEventDescription(), '')

def newSetupEvent(self):
    self.division1 = Division.objects.create(name='Division 1')
    self.event = Event(
        year=self.year,
        state=self.newState,
        name='Event 1',
        status='published',
        maxMembersPerTeam=5,
        event_defaultEntryFee = 4,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
        directEnquiriesTo = self.user
    )
    self.event.save()
    self.availableDivision = AvailableDivision.objects.create(event=self.event, division=self.division1)

class TestAvailableDivisionClean(TestCase):
    def setUp(self):
        commonSetUp(self)
        newSetupEvent(self)

    def testBillingEntryFeeAndTypeValidBlank(self):
        self.availableDivision.clean()

    def testBillingEntryFeeAndTypeValidFilled(self):
        self.availableDivision.division_billingType = 'team'
        self.availableDivision.division_entryFee = 50
        self.availableDivision.clean()

    def testBillingEntryFeeAndTypeInValid1(self):
        self.availableDivision.division_billingType = 'team'
        self.assertRaises(ValidationError, self.availableDivision.clean)

    def testBillingEntryFeeAndTypeInValid2(self):
        self.availableDivision.division_entryFee = 50
        self.assertRaises(ValidationError, self.availableDivision.clean)

    def testSpecialRateValid(self):
        self.event.event_specialRateFee = 50
        self.event.event_specialRateNumber = 5
        self.event.save()

        self.availableDivision.clean()

    def testSpecialRateInValid(self):
        self.event.event_specialRateFee = 50
        self.event.event_specialRateNumber = 5
        self.event.save()

        self.availableDivision.division_billingType = 'team'
        self.assertRaises(ValidationError, self.availableDivision.clean)

        self.availableDivision.division_billingType = 'student'
        self.assertRaises(ValidationError, self.availableDivision.clean)

    def testWorkshopValid(self):
        self.event.eventType = 'workshop'
        self.event.save()

        self.availableDivision.clean()

        self.availableDivision.division_billingType = 'team'
        self.availableDivision.division_entryFee = 50
        self.availableDivision.clean()

    def testWorkshopInValid(self):
        self.event.eventType = 'workshop'
        self.event.save()

        self.availableDivision.division_billingType = 'student'
        self.availableDivision.division_entryFee = 50
        self.assertRaises(ValidationError, self.availableDivision.clean)

    def testStateValidation(self):
        self.state2 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name="State 2", abbreviation='ST2')
        self.division2 = Division.objects.create(name='Division 2', state=self.state2)
        self.availableDivision.division=self.division2
        self.assertRaises(ValidationError, self.availableDivision.clean)

class TestAvailableDivisionMethods(TestCase):
    def setUp(self):
        commonSetUp(self)
        newSetupEvent(self)

    def testGetState(self):
        self.assertEqual(self.availableDivision.getState(), self.newState)

class TestDivisionClean(TestCase):
    def setUp(self):
        commonSetUp(self)
        newSetupEvent(self)
        self.state2 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name="State 2", abbreviation='ST2')

    def testSuccessValidation_noState(self):
        self.division1.clean()

    def testSuccessValidation_state(self):
        self.availableDivision.delete()
        self.division1.state = self.state2
        self.division1.clean()

    def testTeamDivisionValidation(self):
        self.availableDivision.delete()
        self.division1.state = self.state2
        self.division1.clean()

        Team.objects.create(event=self.event, division=self.division1, mentorUser=self.user, name='New Team 1')
        self.assertRaises(ValidationError, self.division1.clean)

    def testAvailableDivisionValidation(self):
        self.division1.state = self.state2
        self.assertRaises(ValidationError, self.division1.clean)

class TestDivisionMethods(TestCase):
    def setUp(self):
        commonSetUp(self)
        newSetupEvent(self)
        self.state2 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name="State 2", abbreviation='ST2')

    def testStrNoState(self):
        self.assertEqual(str(self.division1), 'Division 1')

    def testStrState(self):
        self.division1.state = self.state2
        self.assertEqual(str(self.division1), 'Division 1 (State 2)')
    
    def testGetState_noState(self):
        self.assertEqual(self.division1.getState(), None)

    def testGetState_state(self):
        self.division1.state = self.state2
        self.assertEqual(self.division1.getState(), self.state2)

def createVenues(self):
    self.venue1 = Venue.objects.create(name='Venue 1', state=self.newState)
    self.venue2 = Venue.objects.create(name='Venue 2', state=self.state2)

class TestVenueClean(TestCase):
    def setUp(self):
        commonSetUp(self)
        newSetupEvent(self)
        self.state2 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name="State 2", abbreviation='ST2')
        createVenues(self)

    def testSuccess(self):
        self.venue1.clean()
    
    def testIncompatibleEvent(self):
        self.event.venue = self.venue1
        self.event.save()
        self.venue1.clean()

        self.venue1.state = self.state2
        self.assertRaises(ValidationError, self.venue1.clean)

class TestVenueMethods(TestCase):
    def setUp(self):
        commonSetUp(self)
        newSetupEvent(self)
        self.state2 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name="State 2", abbreviation='ST2')
        createVenues(self)

    def testGetState(self):
        self.assertEqual(self.venue1.getState(), self.newState)

class TestAdminSummaryContext(TestCase):
    def setUp(self):
        self.maxDiff = None
        commonSetUp(self)
        newSetupEvent(self)

        self.school2 = School.objects.create(
            name='School 2',
            abbreviation='sch2',
            state=self.newState,
            region=self.newRegion
        )

        self.division2 = Division.objects.create(name='Div2',category = self.divCategory)
        self.oldEventWithTeams.divisions.add(self.division2)

        # self.oldeventTeam = Team.objects.create(event=self.oldEventWithTeams, division=self.division, school=self.newSchool, mentorUser=self.user, name='test')
        # self.oldTeamStudent.objects.create = Student(team=self.oldeventTeam,firstName='test',lastName='old',yearLevel=1,gender='male')
        self.oldeventTeam2 = Team.objects.create(event=self.oldEventWithTeams, division=self.division, school=self.newSchool, mentorUser=self.user, name='second')
        Student.objects.create(team=self.oldeventTeam2,firstName='Second1',lastName='Second1',yearLevel=1,gender='female')
        self.oldeventTeam3 = Team.objects.create(event=self.oldEventWithTeams, division=self.division, school=self.school2, mentorUser=self.user, name='third')
        Student.objects.create(team=self.oldeventTeam3,firstName='Third1',lastName='Third1',yearLevel=1,gender='male')
        Student.objects.create(team=self.oldeventTeam3,firstName='Third2',lastName='Third2',yearLevel=1,gender='other')
        self.oldeventTeam4 = Team.objects.create(event=self.oldEventWithTeams, division=self.division2, school=self.newSchool, mentorUser=self.user, name='second')
        Student.objects.create(team=self.oldeventTeam4,firstName='Fourth1',lastName='Fourth1',yearLevel=1,gender='male')

        self.venue = Venue.objects.create(name='Venue 1', state=self.newState)
        self.oldEvent.venue = self.venue
        
        self.oldEvent.save()

        self.workshop = Event.objects.create(year=self.year,
            state=self.newState,
            name='Workshop Test',
            eventType='workshop',
            status='published',
            maxMembersPerTeam=5,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            directEnquiriesTo = self.user     
            )
        self.workshop.divisions.add(self.division)
        self.workshop.divisions.add(self.division2)

        WorkshopAttendee.objects.create(event = self.workshop, division=self.division, school=self.newSchool, mentorUser=self.user,attendeeType='student', firstName='Student',lastName='Student',yearLevel=1,gender='male')
        WorkshopAttendee.objects.create(event = self.workshop, division=self.division, school=self.newSchool, mentorUser=self.user,attendeeType='teacher', firstName='Teacher',lastName='Teacher',yearLevel=1,gender='female')
        WorkshopAttendee.objects.create(event = self.workshop, division=self.division, school=self.newSchool, mentorUser=self.user,attendeeType='student', firstName='Student2',lastName='Student2',yearLevel=1,gender='other')
        WorkshopAttendee.objects.create(event = self.workshop, division=self.division, school=self.school2, mentorUser=self.user,attendeeType='student', firstName='Student3',lastName='Student2',yearLevel=1,gender='other')
        WorkshopAttendee.objects.create(event = self.workshop, division=self.division2, school=self.newSchool, mentorUser=self.user,attendeeType='student', firstName='Student',lastName='Student',yearLevel=1,gender='male')

        self.workshop2 = Event.objects.create(year=self.year,
            state=self.newState,
            name='Workshop 2 Test',
            eventType='workshop',
            status='published',
            maxMembersPerTeam=5,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            directEnquiriesTo = self.user     
            )
        self.workshop2.divisions.add(self.division)

        WorkshopAttendee.objects.create(event = self.workshop2, division=self.division, school=self.newSchool, mentorUser=self.user,attendeeType='student', firstName='Student',lastName='Student',yearLevel=1,gender='male')
        WorkshopAttendee.objects.create(event = self.workshop2, division=self.division, school=self.newSchool, mentorUser=self.user,attendeeType='teacher', firstName='Teacher',lastName='Teacher',yearLevel=1,gender='female')
        
        self.client.login(request=HttpRequest(), username=self.username, password=self.password)

    def testCompetitionDict(self):
        returned = getAdminCompSummary(self.oldEventWithTeams)
        context = {
            "name": self.oldEventWithTeams.name,
            "division_categories": {self.divCategory.pk:
                {'divisions':[
                    {
                        'name': 'Div2',
                        'teams': 1,
                        'students': 1,
                    },
                    {
                        'name': 'test',
                        'teams': 3,
                        'students': 4,
                    },
                    ],
                'name': 'Test', 'rows': 3,'students': 5,'teams': 4}},
            'division_teams': 4,
            'division_students': 5,
            "schools": [{'name':self.newSchool.name,'teams':3,'students':3},{'name':self.school2.name,'teams':1,'students':2},{'name': 'Independent', 'teams': 0, 'students': 0}],
            'school_teams': 4,
            'school_students': 5,
        }
        self.assertEqual(context, returned)

    def testWorkshopDict(self):
        returned = getAdminWorkSummary(self.workshop)
        context = {
            "name": self.workshop.name,
            "division_categories": {self.divCategory.pk:
                {'divisions':[
                    {
                        'name': 'Div2',
                        'students': 1,
                        'teachers': 0,
                    },
                    {
                        'name': 'test',
                        'students': 3,
                        'teachers': 1,
                    },],
                'name':'Test','rows':3,'students':4,'teachers':1}},
            'division_students': 4,
            'division_teachers': 1,
            "schools": [{'name':self.newSchool.name,'students':3,'teachers':1},{'name':self.school2.name,'students':1,'teachers':0},{'name': 'Independent', 'students': 0, 'teachers': 0}],
            'school_students': 4,
            'school_teachers': 1,
        }
        self.assertEqual(context, returned)

    def testBlankForm(self):
        response = self.client.get(reverse('events:eventAdminSummary'))
        self.assertContains(response,'Event Comparisons')

    def testWorkshopAndCompetition(self):
        response = self.client.post(reverse('events:eventAdminSummary'), {'competitions':[self.oldEventWithTeams.id],'workshops':[self.workshop.id]})
        self.assertContains(response,'Cannot directly compare workshops and competitions')

    def testCompetitionFromURL(self):
        response = self.client.post(reverse('events:eventAdminSummarySpecific', kwargs= {'eventID':self.oldEventWithTeams.id}))
        self.assertContains(response,'Students', 3)
        self.assertContains(response,'Teams', 3)
        self.assertContains(response,'Divisions', 1)
        self.assertContains(response,'Schools', 1)

    def testCompetitionFromForm(self):
        response = self.client.post(reverse('events:eventAdminSummary'), {'competitions':[self.oldEventWithTeams.id],'workshops':[]})
        self.assertContains(response,'Students', 3)
        self.assertContains(response,'Teams', 3)
        self.assertContains(response,'Divisions', 1)
        self.assertContains(response,'Schools', 1)

    def testMultipleCompetitions(self):
        response = self.client.post(reverse('events:eventAdminSummary'), {'competitions':[self.oldEventWithTeams.id, self.newEvent.id],'workshops':[]})
        self.assertContains(response,'Students Per Division', 1)
        self.assertContains(response,'Teams Per Division', 1)
        self.assertContains(response,'Students Per School', 1)
        self.assertContains(response,'Teams Per School', 1)
        self.assertContains(response,self.oldEventWithTeams.name, 4)
        self.assertContains(response,self.newEvent.name, 4)

    def testWorkshopFromURL(self):
        response = self.client.post(reverse('events:eventAdminSummarySpecific', kwargs= {'eventID':self.workshop.id}))
        self.assertContains(response,'Students', 3)
        self.assertContains(response,'Teachers', 2)
        self.assertContains(response,'Divisions', 1)
        self.assertContains(response,'Schools', 1)

    def testWorkshopFromForm(self):
        response = self.client.post(reverse('events:eventAdminSummary'), {'competitions':[],'workshops':[self.workshop.id]})
        self.assertContains(response,'Students', 3)
        self.assertContains(response,'Teachers', 2)
        self.assertContains(response,'Divisions', 1)
        self.assertContains(response,'Schools', 1)

    def testMultipleWorkshop(self):
        response = self.client.post(reverse('events:eventAdminSummary'), {'competitions':[],'workshops':[self.workshop.id, self.workshop2.id]})
        self.assertContains(response,'Students Per Division', 1)
        self.assertContains(response,'Teachers Per Division', 1)
        self.assertContains(response,'Students Per School', 1)
        self.assertContains(response,'Teachers Per School', 1)
        self.assertContains(response,self.workshop.name, 4)
        self.assertContains(response,self.workshop2.name, 4)