from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.http import HttpRequest

from regions.models import State,Region
from schools.models import School, SchoolAdministrator
from teams.models import Team, Student
from events.models import Event, Division, Year, AvailableDivision, Venue
from users.models import User
from coordination.models import Coordinator

import datetime
# Create your tests here.


def commonSetUp(obj):
    obj.username = 'user@user.com'
    obj.password = 'password'
    obj.user = user = User.objects.create_user(email=obj.username, password=obj.password)
    obj.newState = State.objects.create(
        typeRegistration=True,
        name='Victoria',
        abbreviation='VIC'
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
    obj.division = Division.objects.create(name='test')

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
    obj.oldTeamStudent = Student(team=obj.oldeventTeam,firstName='test',lastName='old',yearLevel=1,gender='Male',birthday=datetime.datetime.now().date())
    
    obj.newEventTeam = Team.objects.create(event=obj.newEvent, division=obj.division, school=obj.newSchool, mentorUser=obj.user, name='test new team')
    obj.newTeamStudent = Student(team=obj.newEventTeam,firstName='test',lastName='new',yearLevel=1,gender='Male',birthday=datetime.datetime.now().date())

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
        response = self.client.get(reverse('events:dashboard'))
        self.assertNotContains(response, 'test new yes reg')

    def testStateFiltering_all(self):
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
        self.user2 = User.objects.create(email='user2@user.com', password=self.password)

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

    def testCreationButtonsNotVisibleWhenRegoClosed(self):
        self.oldTeam = Team.objects.create(event=self.oldEventWithTeams, division=self.division, mentorUser=self.user, name='test old team ind')

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
        self.user2 = User.objects.create(email='user2@user.com', password=self.password)

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
        self.state2 = State.objects.create(typeRegistration=True, name="State 2", abbreviation='ST2')
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
        self.assertRaises(ValidationError, self.event.clean)

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

class TestEventMethods(TestCase):
    def setUp(self):
        commonSetUp(self)
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

    def testDirectEnquiriesToName(self):
        self.assertEqual(self.event.directEnquiriesToName(), 'First Last')

    def testDirectEnquiriesToEmail(self):
        self.assertEqual(self.event.directEnquiriesToEmail(), self.username)

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
        self.state2 = State.objects.create(typeRegistration=True, name="State 2", abbreviation='ST2')
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
        self.state2 = State.objects.create(typeRegistration=True, name="State 2", abbreviation='ST2')

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
        self.state2 = State.objects.create(typeRegistration=True, name="State 2", abbreviation='ST2')

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
        self.state2 = State.objects.create(typeRegistration=True, name="State 2", abbreviation='ST2')
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
        self.state2 = State.objects.create(typeRegistration=True, name="State 2", abbreviation='ST2')
        createVenues(self)

    def testGetState(self):
        self.assertEqual(self.venue1.getState(), self.newState)

def adminSetUp(self):
    self.user1 = User.objects.create_user(email=self.email1, password=self.password)
    self.user2 = User.objects.create_user(email=self.email2, password=self.password)
    self.user3 = User.objects.create_user(email=self.email3, password=self.password)

    self.state1 = State.objects.create(typeRegistration=True, name='Victoria', abbreviation='VIC')
    self.state2 = State.objects.create(typeRegistration=True, name='South Australia', abbreviation='SA')

    self.usersuper = User.objects.create_user(email=self.emailsuper, password=self.password, is_staff=True, is_superuser=True)

    self.division0 = Division.objects.create(name='Division 0')
    self.division1 = Division.objects.create(name='Division 1', state=self.state1)
    self.division2 = Division.objects.create(name='Division 2', state=self.state2)

    self.venue1 = Venue.objects.create(name='Venue 1', state=self.state1)
    self.venue2 = Venue.objects.create(name='Venue 2', state=self.state2)

class TestDivisionAdmin(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    emailsuper = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        adminSetUp(self)

    # Division filtering

    def testListLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:events_division_changelist'))
        self.assertEqual(response.status_code, 200)

    def testChangeLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:events_division_change', args=(self.division1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save')

    def testListContent_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:events_division_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Division 0')
        self.assertContains(response, 'Division 1')
        self.assertContains(response, 'Division 2')

    def testDeleteLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:events_division_delete', args=(self.division1.id,)))
        self.assertEqual(response.status_code, 200)

    def testListNonStaff_denied(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_division_changelist'))
        self.assertEqual(response.status_code, 302)

    def testListLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_division_changelist'))
        self.assertEqual(response.status_code, 200)

    def testListContent_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_division_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Division 0')
        self.assertContains(response, 'Division 1')
        self.assertNotContains(response, 'Division 2')

    def testChangeLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_division_change', args=(self.division1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save')

    def testAddLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_division_add'))
        self.assertEqual(response.status_code, 200)

    def testDeleteLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_division_delete', args=(self.division1.id,)))
        self.assertEqual(response.status_code, 200)

    def testChangeDenied_wrongState_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_division_change', args=(self.division2.id,)))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('admin:events_division_change', args=(self.division2.id,)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'doesn’t exist. Perhaps it was deleted?')

    def testViewLoads_viewonly_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='viewall', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_division_change', args=(self.division1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Save')

    def testAddDenied_viewPermission_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='viewall', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_division_add'))
        self.assertEqual(response.status_code, 403)

    def testDeleteDenied_viewPermission_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='viewall', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_division_delete', args=(self.division1.id,)))
        self.assertEqual(response.status_code, 403)

    # Change Post

    def testChangePostAllowed_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 1',
            'state': self.state1.id,
        }
        response = self.client.post(reverse('admin:events_division_change', args=(self.division1.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('admin:events_division_change', args=(self.division1.id,)), data=payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'was changed successfully')

        self.division1.refresh_from_db()
        self.assertEqual(self.division1.name, 'Renamed 1')

    def testChangePostDenied_wrongState_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 2',
            'state': self.state2.id,
        }
        response = self.client.post(reverse('admin:events_division_change', args=(self.division2.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('admin:events_division_change', args=(self.division2.id,)), data=payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'doesn’t exist. Perhaps it was deleted?')

    def testChangePostDenied_noState_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 0',
            'state': self.state1.id,
        }
        response = self.client.post(reverse('admin:events_division_change', args=(self.division0.id,)), data=payload)
        self.assertEqual(response.status_code, 403)

    def testChangePostDenied_viewPermission_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='viewall', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 1',
            'state': self.state1.id,
        }
        response = self.client.post(reverse('admin:events_division_change', args=(self.division1.id,)), data=payload)
        self.assertEqual(response.status_code, 403)

    # Division FK filtering

    # State field
    def testStateFieldSuccess_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        payload = {
            'name': 'Renamed 1',
            'state': self.state1.id,
        }
        response = self.client.post(reverse('admin:events_division_change', args=(self.division1.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

    def testStateFieldSuccess_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 1',
            'state': self.state1.id,
        }
        response = self.client.post(reverse('admin:events_division_change', args=(self.division1.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

    def testStateFieldDenied_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 1',
            'state': self.state2.id,
        }
        response = self.client.post(reverse('admin:events_division_change', args=(self.division1.id,)), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

    def testStateFieldBlankDenied_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 1',
            'state': '',
        }
        response = self.client.post(reverse('admin:events_division_change', args=(self.division1.id,)), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'This field is required.')

class TestVenueAdmin(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    emailsuper = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        adminSetUp(self)

    # Venue filtering

    def testListLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:events_venue_changelist'))
        self.assertEqual(response.status_code, 200)

    def testChangeLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:events_venue_change', args=(self.venue1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save')

    def testListContent_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:events_venue_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Venue 1')
        self.assertContains(response, 'Venue 2')

    def testDeleteLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:events_venue_delete', args=(self.venue1.id,)))
        self.assertEqual(response.status_code, 200)

    def testListNonStaff_denied(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_venue_changelist'))
        self.assertEqual(response.status_code, 302)

    def testListLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_venue_changelist'))
        self.assertEqual(response.status_code, 200)

    def testListContent_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_venue_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Venue 1')
        self.assertNotContains(response, 'Venue 2')

    def testChangeLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_venue_change', args=(self.venue1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save')

    def testAddLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_venue_add'))
        self.assertEqual(response.status_code, 200)

    def testDeleteLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_venue_delete', args=(self.venue1.id,)))
        self.assertEqual(response.status_code, 200)

    def testChangeDenied_wrongState_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_venue_change', args=(self.venue2.id,)))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('admin:events_venue_change', args=(self.venue2.id,)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'doesn’t exist. Perhaps it was deleted?')

    def testViewLoads_viewonly_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='viewall', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_venue_change', args=(self.venue1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Save')

    def testAddDenied_viewPermission_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='viewall', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_venue_add'))
        self.assertEqual(response.status_code, 403)

    def testDeleteDenied_viewPermission_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='viewall', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:events_venue_delete', args=(self.venue1.id,)))
        self.assertEqual(response.status_code, 403)

    # Change Post

    def testChangePostAllowed_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 1',
            'state': self.state1.id,
        }
        response = self.client.post(reverse('admin:events_venue_change', args=(self.venue1.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('admin:events_venue_change', args=(self.venue1.id,)), data=payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'was changed successfully')

        self.venue1.refresh_from_db()
        self.assertEqual(self.venue1.name, 'Renamed 1')

    def testChangePostDenied_wrongState_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 2',
            'state': self.state2.id,
        }
        response = self.client.post(reverse('admin:events_venue_change', args=(self.venue2.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('admin:events_venue_change', args=(self.venue2.id,)), data=payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'doesn’t exist. Perhaps it was deleted?')

    def testChangePostDenied_viewPermission_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='viewall', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 1',
            'state': self.state1.id,
        }
        response = self.client.post(reverse('admin:events_venue_change', args=(self.venue1.id,)), data=payload)
        self.assertEqual(response.status_code, 403)

    # Venue FK filtering

    # State field
    def testStateFieldSuccess_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        payload = {
            'name': 'Renamed 1',
            'state': self.state1.id,
        }
        response = self.client.post(reverse('admin:events_venue_change', args=(self.venue1.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

    def testStateFieldSuccess_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 1',
            'state': self.state1.id,
        }
        response = self.client.post(reverse('admin:events_venue_change', args=(self.venue1.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

    def testStateFieldDenied_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 1',
            'state': self.state2.id,
        }
        response = self.client.post(reverse('admin:events_venue_change', args=(self.venue1.id,)), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

    def testStateFieldBlankDenied_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 1',
            'state': '',
        }
        response = self.client.post(reverse('admin:events_venue_change', args=(self.venue1.id,)), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'This field is required.')

class TestEventAdmin(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    emailsuper = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        adminSetUp(self)

        self.year = Year.objects.create(year=2020)
        self.event = Event.objects.create(
            year=self.year,
            state=self.state1,
            name='Event 1',
            status='published',
            maxMembersPerTeam=5,
            event_defaultEntryFee = 4,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            directEnquiriesTo = self.user1
        )

    # Test readonly fields on change page

    def testCorrectReadonlyFields_add(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:events_event_add'))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, '<label>Status:</label>')
        self.assertNotContains(response, '<select name="status" id="id_status">')

        self.assertNotContains(response, '<label>Event type:</label>')
        self.assertContains(response, '<select name="eventType" required id="id_eventType">')

    def testCorrectReadonlyFields_change_draft(self):
        self.event.status = 'draft'
        self.event.save()

        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:events_event_change', args=(self.event.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, '<label>Status:</label>')
        self.assertContains(response, '<select name="status" id="id_status">')

        self.assertContains(response, '<label>Event type:</label>')
        self.assertNotContains(response, '<select name="eventType" required id="id_eventType">')

    def testCorrectReadonlyFields_change_published_noTeams(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:events_event_change', args=(self.event.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, '<label>Status:</label>')
        self.assertContains(response, '<select name="status" id="id_status">')

        self.assertContains(response, '<label>Event type:</label>')
        self.assertNotContains(response, '<select name="eventType" required id="id_eventType">')

    def testCorrectReadonlyFields_change_published_teams(self):
        Team.objects.create(event=self.event, division=self.division1, mentorUser=self.user1, name='Test Team')

        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:events_event_change', args=(self.event.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, '<label>Status:</label>')
        self.assertNotContains(response, '<select name="status" id="id_status">')

        self.assertContains(response, '<label>Event type:</label>')
        self.assertNotContains(response, '<select name="eventType" required id="id_eventType">')
