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
from eventfiles.models import EventAvailableFileType, MentorEventFileType
from invoices.models import Invoice, InvoiceGlobalSettings
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
        competition_defaultEntryFee = 4,
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
        competition_defaultEntryFee = 4,
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
        competition_defaultEntryFee = 4,
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
        competition_defaultEntryFee = 4,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=-3)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=-4)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-6)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
        directEnquiriesTo = obj.user     
    )
    obj.oldEventWithTeams.divisions.add(obj.division)
    obj.oldeventTeam = Team.objects.create(event=obj.oldEventWithTeams, division=obj.division, school=obj.newSchool, mentorUser=obj.user, name='test')
    obj.oldTeamStudent = Student.objects.create(team=obj.oldeventTeam,firstName='test',lastName='old',yearLevel=1,gender='male')

    obj.newEventTeam = Team.objects.create(event=obj.newEvent, division=obj.division, school=obj.newSchool, mentorUser=obj.user, name='test new team')
    obj.newTeamStudent = Student.objects.create(team=obj.newEventTeam,firstName='test',lastName='new',yearLevel=1,gender='male')

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

    def test_load_sets_associationPromptShown(self):
        self.assertFalse(self.user.associationPromptShown)
        response = self.client.get(reverse('events:dashboard'))
        self.assertTrue(response.context['showAssociationPrompt'])
        self.user.refresh_from_db()
        self.assertTrue(self.user.associationPromptShown)
    
    def test_subsequent_load_does_not_set_associationPromptShown(self):
        self.user.associationPromptShown = True
        self.user.save()
        response = self.client.get(reverse('events:dashboard'))
        self.assertFalse(response.context['showAssociationPrompt'])

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

class TestEventDetailsPage_Competition_school(TestCase):
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

class TestEventDetailsPage_Competition_independent(TestEventDetailsPage_Competition_school):
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

class TestEventDetailsPage_Competition_superuser(TestCase):
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

class TestEventDetailsPage_Workshop_superuser(TestCase):
    def setUp(self):
        commonSetUp(self)
        self.user.is_superuser = True
        self.user.save()
        self.client.login(request=HttpRequest(), username=self.username, password=self.password)
        self.newEvent.eventType = 'workshop'
        self.newEvent.save()

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

    def testNotPublishedLoad(self):
        self.newEvent.status = "draft"
        self.newEvent.save()

        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.newEvent.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Event is not published.')

class TestEventClean(TestCase):
    def setUp(self):
        commonSetUp(self)
        self.division1 = Division.objects.create(name='Division 1')
        self.division2 = Division.objects.create(name='Division 2', state=self.newState)
        self.event = Event(
            year=self.year,
            state=self.newState,
            name='Event 1',
            eventType='competition',
            status='published',
            maxMembersPerTeam=5,
            competition_defaultEntryFee = 4,
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
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testStatusDraft(self):
        self.event.status = 'draft'
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testStatusDraftTeamExists(self):
        self.event.status = 'draft'
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')
        self.event.save()
        Team.objects.create(event=self.event, division=self.division, mentorUser=self.user, name='New Test Team')
        self.assertRaises(ValidationError, self.event.clean)

    # Dates validation

    def testStartDateNoneInvalid(self):
        self.event.startDate = None
        self.assertRaisesMessage(ValidationError, 'Event start and end date must either both be set or both be blank', self.event.clean)

    def testEndDateNoneInvalid(self):
        self.event.endDate = None
        self.assertRaisesMessage(ValidationError, 'Event start and end date must either both be set or both be blank', self.event.clean)

    def testRegistrationsOpenDateNoneValid(self):
        self.event.registrationsOpenDate = None
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testRegistrationsCloseDateNoneInvalid(self):
        self.event.registrationsCloseDate = None
        self.assertRaisesMessage(ValidationError, 'Event start date, event end date, and registrations close date must be set if registrations open date is set', self.event.clean)

    def testNoDatesOrDefaultPaymentValid(self):
        self.event.registrationsOpenDate = None
        self.event.registrationsCloseDate = None
        self.event.startDate = None
        self.event.endDate = None
        self.event.competition_defaultEntryFee = None
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testJustStartAndEndDateValid(self):
        self.event.registrationsOpenDate = None
        self.event.registrationsCloseDate = None
        self.event.competition_defaultEntryFee = None
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')
    
    def testJustStartDateInvalid(self):
        self.event.registrationsOpenDate = None
        self.event.registrationsCloseDate = None
        self.event.endDate = None
        self.event.competition_defaultEntryFee = None
        self.assertRaisesMessage(ValidationError, 'Event start and end date must either both be set or both be blank', self.event.clean)
    
    def testJustRegistrationsCloseDateInvalid(self):
        self.event.registrationsOpenDate = None
        self.event.startDate = None
        self.event.endDate = None
        self.event.competition_defaultEntryFee = None
        self.assertRaisesMessage(ValidationError, 'Event start and end date must be set if registrations close date is set', self.event.clean)

    def testJustRegistrationsOpenDateInvalid(self):
        self.event.startDate = None
        self.event.endDate = None
        self.event.competition_defaultEntryFee = None
        self.assertRaisesMessage(ValidationError, 'Event start date, event end date, and registrations close date must be set if registrations open date is set', self.event.clean)
    
    def testDefaultEntryFeeNone_CompetitionInvalid(self):
        self.event.competition_defaultEntryFee = None
        self.assertRaisesMessage(ValidationError, 'Default entry fee must be set if registrations open date is set', self.event.clean)

    def testDefaultEntryFeeNone_WorkshopValid(self):
        self.event.competition_defaultEntryFee = None
        self.event.eventType = 'workshop'
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testAllDetailsRequiredIfRegistrations(self):
        self.oldEventWithTeams.registrationsOpenDate = None
        self.assertRaisesMessage(ValidationError, 'All dates must be set once event registrations exist', self.oldEventWithTeams.clean)

    def testMultidayEventOK(self):
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testSingleDayEventOK(self):
        self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+5)).date()
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

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
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testRegistrationCloseOnEventStartDate(self):
        self.event.startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date()
        self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date()
        self.event.registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-3)).date()
        self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=+5)).date()
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testRegistrationCloseAfterEventStartDate(self):
        self.event.startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date()
        self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date()
        self.event.registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-3)).date()
        self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date()
        self.assertRaises(ValidationError, self.event.clean)

    # Billing settings validation

    def testSpecialRateValidComplete(self):
        self.event.competition_specialRateFee = 50
        self.event.competition_specialRateNumber = 5
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testSpecialRateInvalid(self):
        self.event.competition_specialRateFee = 50
        self.assertRaises(ValidationError, self.event.clean)

    def testSpecialRateStudentInvalid(self):
        self.event.competition_specialRateFee = 50
        self.event.competition_specialRateNumber = 5
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

        self.event.competition_billingType = 'student'
        self.assertRaises(ValidationError, self.event.clean)
    
    def testSpecialRateBillingAvailableDivisionValid(self):
        self.event.save()
        self.availableDivision = AvailableDivision.objects.create(event=self.event, division=self.division1)
        self.event.competition_specialRateFee = 50
        self.event.competition_specialRateNumber = 5
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testSpecialRateBillingAvailableDivisionInValid(self):
        self.event.save()
        self.availableDivision = AvailableDivision.objects.create(event=self.event, division=self.division1)
        self.event.competition_specialRateFee = 50
        self.event.competition_specialRateNumber = 5
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

        self.availableDivision.division_billingType = 'team'
        self.availableDivision.division_entryFee = 50
        self.availableDivision.save()

        self.assertRaises(ValidationError, self.event.clean)

    # Test state validations

    def testVenueStateSuccess(self):
        self.event.venue = self.venue1
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testVenueFailureWrongVenueState(self):
        self.event.venue = self.venue2
        self.assertRaises(ValidationError, self.event.clean)

    def testAvailableDivisionSuccessNoPk(self):
        self.assertEqual(self.event.pk, None)
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testAvailableDivisionSuccessExistingEvent(self):
        self.event.save()
        self.assertNotEqual(self.event.pk, None)

        self.availableDivision = AvailableDivision.objects.create(event=self.event, division=self.division2)
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testAvailableDivision_StateChangeSuccess(self):
        self.event.save()
        self.assertNotEqual(self.event.pk, None)

        self.event.state = self.state2
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

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
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

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

    def testUploadDeadlineNoRegistrationCloseOrStartDate(self):
        self.fileType1 = MentorEventFileType.objects.create(name="File Type 1")
        self.event.registrationsOpenDate = None
        self.event.registrationsCloseDate = None
        self.event.startDate = None
        self.event.endDate = None
        self.event.competition_defaultEntryFee = None
        self.event.save()
        self.availableFileType1 = EventAvailableFileType.objects.create(event=self.event, fileType=self.fileType1, uploadDeadline=(datetime.datetime.now() + datetime.timedelta(days=4)).date())
        self.availableFileType1.save()
        try:
            self.event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

class TestEventMethods(TestCase):
    def setUp(self):
        commonSetUp(self)
        self.division1 = Division.objects.create(name='Division 1')
        self.event = Event.objects.create(
            year=self.year,
            state=self.newState,
            name='Event 1',
            eventType='competition',
            status='published',
            maxMembersPerTeam=5,
            competition_defaultEntryFee = 4,
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

    def testPreSave_competition(self):
        self.event.eventType = 'competition'
        self.event.competition_billingType = 'student'
        self.assertEqual(self.event.maxMembersPerTeam, 5)
        self.assertEqual(self.event.competition_billingType, 'student')

        self.event.save()
        self.assertEqual(self.event.maxMembersPerTeam, 5)
        self.assertEqual(self.event.competition_billingType, 'student')

    def testPreSave_workshop(self):
        self.event.eventType = 'workshop'
        self.event.competition_billingType = 'student'
        self.assertEqual(self.event.maxMembersPerTeam, 5)
        self.assertEqual(self.event.competition_billingType, 'student')

        self.event.save()
        self.assertEqual(self.event.maxMembersPerTeam, 0)
        self.assertEqual(self.event.competition_billingType, 'team')

    def testPreSave_setsWorkshopEntryFees_notSet(self):
        self.assertEqual(self.event.workshopTeacherEntryFee, 4)
        self.assertEqual(self.event.workshopStudentEntryFee, 4)

    def testPreSave_setsWorkshopEntryFees_set(self):
        self.event.workshopTeacherEntryFee = 5
        self.event.workshopStudentEntryFee = 6
        self.event.save()

        self.assertEqual(self.event.workshopTeacherEntryFee, 5)
        self.assertEqual(self.event.workshopStudentEntryFee, 6)

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

    def testPaidEvent_competition_defaultEntryFee(self):
        self.assertTrue(self.event.paidEvent())

    def testPaidEvent_competition_noDefaultEntryFee(self):
        self.event.competition_defaultEntryFee = None
        self.assertFalse(self.event.paidEvent())

    def testPaidEvent_competition_free(self):
        self.event.competition_defaultEntryFee = 0
        self.assertFalse(self.event.paidEvent())

    def testPaidEvent_competition_specialRateFee(self):
        self.event.competition_defaultEntryFee = 0
        self.event.competition_specialRateFee = 5
        self.assertTrue(self.event.paidEvent())

    def testPaidEvent_competition_free_withDivision(self):
        self.event.competition_defaultEntryFee = 0
        self.availableDivision = AvailableDivision.objects.create(event=self.event, division=self.division1)

        self.assertFalse(self.event.paidEvent())

    def testPaidEvent_competition_division_entryFee(self):
        self.event.competition_defaultEntryFee = 0
        self.availableDivision = AvailableDivision.objects.create(event=self.event, division=self.division1)
        self.availableDivision.division_entryFee = 5
        self.availableDivision.save()

        self.assertTrue(self.event.paidEvent())

    def testPaidEvent_workshop_studentEntryFee(self):
        self.event.eventType = 'workshop'
        self.event.competition_defaultEntryFee = 0
        self.event.workshopStudentEntryFee = 5
        self.assertTrue(self.event.paidEvent())

    def testPaidEvent_workshop_teacherEntryFee(self):
        self.event.eventType = 'workshop'
        self.event.competition_defaultEntryFee = 0
        self.event.workshopTeacherEntryFee = 5
        self.assertTrue(self.event.paidEvent())

    def testPaidEvent_workshop_teacherEntryFee_defaultNone(self):
        self.event.eventType = 'workshop'
        self.event.competition_defaultEntryFee = None
        self.event.workshopTeacherEntryFee = 5
        self.assertTrue(self.event.paidEvent())

    def testPaidEvent_workshop_freeDefaultEntryFeeSet(self):
        self.event.eventType = 'workshop'
        self.event.competition_defaultEntryFee = 50
        self.event.workshopTeacherEntryFee = 0
        self.event.workshopStudentEntryFee = 0
        self.assertFalse(self.event.paidEvent())

    def testPaidEvent_workshop_freeDefaultEntryFeeNone(self):
        self.event.eventType = 'workshop'
        self.event.competition_defaultEntryFee = None
        self.event.workshopTeacherEntryFee = 0
        self.event.workshopStudentEntryFee = 0
        self.assertFalse(self.event.paidEvent())

    def testPaidEvent_workshop_allFieldsNone(self):
        self.event.eventType = 'workshop'
        self.event.competition_defaultEntryFee = None
        self.event.workshopTeacherEntryFee = None
        self.event.workshopStudentEntryFee = None
        self.assertFalse(self.event.paidEvent())

    def test_published_draft(self):
        self.event.status = 'draft'
        self.assertFalse(self.event.published())

    def test_published_published(self):
        self.assertTrue(self.event.published())

    def test_hasAllDates_allDates(self):
        self.assertTrue(self.event.hasAllDates())
    
    def test_hasAllDates_noRegistrationsOpenDate(self):
        self.event.registrationsOpenDate = None
        self.assertFalse(self.event.hasAllDates())

    def test_hasAllDetails_allDetails(self):
        self.assertTrue(self.event.hasAllDetails())
    
    def test_hasAllDetails_noRegistrationsOpenDate(self):
        self.event.registrationsOpenDate = None
        self.assertFalse(self.event.hasAllDetails())
    
    def test_hasAllDetails_noDefaultEntryFee_competition(self):
        self.event.competition_defaultEntryFee = None
        self.assertFalse(self.event.hasAllDetails())
    
    def test_hasAllDetails_noDefaultEntryFee_workshop(self):
        self.event.eventType = 'workshop'
        self.event.competition_defaultEntryFee = None
        self.assertTrue(self.event.hasAllDetails())

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

    def test_registrationsOpen_noDates(self):
        self.event.startDate=None
        self.event.endDate = None
        self.event.registrationsOpenDate = None
        self.event.registrationsCloseDate = None
        self.assertFalse(self.event.registrationsOpen())

    def test_registrationsOpen_noDefaultEntryFee_competition(self):
        self.event.registrationsOpenDate = (datetime.datetime.now()).date()
        self.event.registrationsCloseDate = (datetime.datetime.now()).date()
        self.event.competition_defaultEntryFee = None
        self.assertFalse(self.event.registrationsOpen())

    def test_registrationsOpen_noDefaultEntryFee_workshop(self):
        self.event.eventType = 'workshop'
        self.event.registrationsOpenDate = (datetime.datetime.now()).date()
        self.event.registrationsCloseDate = (datetime.datetime.now()).date()
        self.event.competition_defaultEntryFee = None
        self.assertTrue(self.event.registrationsOpen())

    def test_registrationNotOpenYet_open(self):
        self.event.registrationsOpenDate = (datetime.datetime.now()).date()
        self.event.registrationsCloseDate = (datetime.datetime.now()).date()
        self.assertFalse(self.event.registrationNotOpenYet())

    def test_registrationNotOpenYet_notOpenYet(self):
        self.event.registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
        self.assertTrue(self.event.registrationNotOpenYet())

    def test_registrationNotOpenYet_pastEventNoRegistrationDates(self):
        self.event.startDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date()
        self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date()
        self.event.registrationsOpenDate = None
        self.event.registrationsCloseDate = None
        self.assertFalse(self.event.registrationNotOpenYet())

    def test_registrationNotOpenYet_closed(self):
        self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date()
        self.assertFalse(self.event.registrationNotOpenYet())

    def test_registrationsNotOpenYet_noDates(self):
        self.event.startDate=None
        self.event.endDate = None
        self.event.registrationsOpenDate = None
        self.event.registrationsCloseDate = None
        self.assertTrue(self.event.registrationNotOpenYet())

    def test_registrationsNotOpenYet_noDefaultEntryFee_competition(self):
        self.event.registrationsOpenDate = (datetime.datetime.now()).date()
        self.event.registrationsCloseDate = (datetime.datetime.now()).date()
        self.event.competition_defaultEntryFee = None
        self.assertTrue(self.event.registrationNotOpenYet())

    def test_registrationsNotOpenYet_noDefaultEntryFee_workshop(self):
        self.event.eventType = 'workshop'
        self.event.registrationsOpenDate = (datetime.datetime.now()).date()
        self.event.registrationsCloseDate = (datetime.datetime.now()).date()
        self.event.competition_defaultEntryFee = None
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
            competition_defaultEntryFee = 4,
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

    def test_checkBillingDetailsChanged_competition_defaultEntryFee(self):
        self.event.competition_defaultEntryFee = 6
        self.assertTrue(self.event.checkBillingDetailsChanged())

    def test_checkBillingDetailsChanged_competition_billingType(self):
        self.event.competition_billingType = 'student'
        self.assertTrue(self.event.checkBillingDetailsChanged())

    def test_checkBillingDetailsChanged_competition_specialRateNumber(self):
        self.event.competition_specialRateNumber = 10
        self.assertTrue(self.event.checkBillingDetailsChanged())

    def test_checkBillingDetailsChanged_competition_specialRateFee(self):
        self.event.competition_specialRateFee = 50
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
            competition_defaultEntryFee = 4,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=3)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=4)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-2)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=+2)).date(),
            directEnquiriesTo = self.user     
        )

        self.assertFalse(self.unsavedEvent.checkEventConvertedToPaid())
    
    def test_checkEventConvertedToPaid_toFree(self):
        self.event.competition_defaultEntryFee = 0
        self.assertFalse(self.event.checkEventConvertedToPaid())

    def test_checkEventConvertedToPaid_toPaid(self):
        self.event.competition_defaultEntryFee = 0
        self.event.save()

        self.event.competition_defaultEntryFee = 5
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
            competition_defaultEntryFee = 4,
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
            competition_defaultEntryFee = 4,
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
            competition_defaultEntryFee = 4,
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
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        competition_defaultEntryFee = 4,
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
        try:
            self.availableDivision.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testBillingEntryFeeAndTypeValidFilled(self):
        self.availableDivision.division_billingType = 'team'
        self.availableDivision.division_entryFee = 50
        try:
            self.availableDivision.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testBillingEntryFeeAndTypeInValid1(self):
        self.availableDivision.division_billingType = 'team'
        self.assertRaises(ValidationError, self.availableDivision.clean)

    def testBillingEntryFeeAndTypeInValid2(self):
        self.availableDivision.division_entryFee = 50
        self.assertRaises(ValidationError, self.availableDivision.clean)

    def testSpecialRateValid(self):
        self.event.competition_specialRateFee = 50
        self.event.competition_specialRateNumber = 5
        self.event.save()

        try:
            self.availableDivision.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testSpecialRateInValid(self):
        self.event.competition_specialRateFee = 50
        self.event.competition_specialRateNumber = 5
        self.event.save()

        self.availableDivision.division_billingType = 'team'
        self.assertRaises(ValidationError, self.availableDivision.clean)

        self.availableDivision.division_billingType = 'student'
        self.assertRaises(ValidationError, self.availableDivision.clean)

    def testWorkshopValid(self):
        self.event.eventType = 'workshop'
        self.event.save()

        try:
            self.availableDivision.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

        self.availableDivision.division_billingType = 'team'
        self.availableDivision.division_entryFee = 50
        try:
            self.availableDivision.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

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
        try:
            self.division1.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testSuccessValidation_state(self):
        self.availableDivision.delete()
        self.division1.state = self.state2
        try:
            self.division1.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testTeamDivisionValidation(self):
        self.availableDivision.delete()
        self.division1.state = self.state2
        try:
            self.division1.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

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
        try:
            self.venue1.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')
    
    def testIncompatibleEvent(self):
        self.event.venue = self.venue1
        self.event.save()
        try:
            self.venue1.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

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

class TestSummaryPage(TestCase):
    def setUp(self):
        commonSetUp(self)
        username = 'admin@admin.com'
        password = 'password'
        self.admin = User.objects.create_superuser(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=username, password=password)
        self.client.login(request=HttpRequest(), username=username, password=password)

        # self.oldeventTeam = Team.objects.create(event=self.oldEventWithTeams, division=self.division, school=self.newSchool, mentorUser=self.user, name='test')
        # self.oldTeamStudent.objects.create = Student(team=self.oldeventTeam,firstName='test',lastName='old',yearLevel=1,gender='male')
        self.oldeventTeam2 = Team.objects.create(event=self.oldEventWithTeams, division=self.division, school=self.newSchool, mentorUser=self.user, name='second')
        Student.objects.create(team=self.oldeventTeam2,firstName='Second1',lastName='Second1',yearLevel=1,gender='female')
        self.oldeventTeam3 = Team.objects.create(event=self.oldEventWithTeams, division=self.division, school=self.newSchool, mentorUser=self.user, name='third')
        Student.objects.create(team=self.oldeventTeam3,firstName='Third1',lastName='Third1',yearLevel=1,gender='male')
        Student.objects.create(team=self.oldeventTeam3,firstName='Third2',lastName='Third2',yearLevel=1,gender='other')

        self.venue = Venue.objects.create(name='Venue 1', state=self.newState)
        self.oldEvent.venue = self.venue
        self.oldEvent.save()

        self.workshop = Event.objects.create(year=self.year,
            state=self.newState,
            name='Workshop',
            eventType='workshop',
            status='published',
            maxMembersPerTeam=5,
            competition_defaultEntryFee = 4,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            directEnquiriesTo = self.user     
            )

        WorkshopAttendee.objects.create(event = self.workshop, division=self.division, school=self.newSchool, mentorUser=self.user,attendeeType='student', firstName='Student',lastName='Student',yearLevel=1,gender='male')
        WorkshopAttendee.objects.create(event = self.workshop, division=self.division, school=self.newSchool, mentorUser=self.user,attendeeType='teacher', firstName='Teacher',lastName='Teacher',yearLevel=1,gender='female')
        WorkshopAttendee.objects.create(event = self.workshop, division=self.division, school=self.newSchool, mentorUser=self.user,attendeeType='student2', firstName='Student2',lastName='Student2',yearLevel=1,gender='other')
        WorkshopAttendee.objects.create(event = self.workshop, division=self.division, school=self.newSchool, mentorUser=self.user,attendeeType='student3', firstName='Student3',lastName='Student2',yearLevel=1,gender='other')

    def createGetQuery(self, state: str, year: int):
        return f"?state={State.objects.get(name=state).id}&year={year}"

    def testLoginRequired(self):
        self.client.logout()
        response = self.client.get(reverse('events:summaryReport'))
        self.assertEqual(response.status_code, 302)

    def testNotStaffDenied(self):
        self.admin.is_superuser = False
        self.admin.save()

        response = self.client.get(reverse('events:summaryReport'))
        self.assertEqual(response.status_code, 403)

    def testPageLoads(self):
        url = reverse('events:summaryReport')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def testTitle(self):
        url = reverse('events:summaryReport') + self.createGetQuery('Victoria', 2019)
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Victoria Activity Summary Report 2019")

    def testCorrectNumberOfEventsForMainState(self):
        url = reverse('events:summaryReport') + self.createGetQuery('Victoria', 2019)
        response = self.client.get(url, follow=True)
        self.assertContains(response, "test old not reg")
        self.assertContains(response, "future event")
        self.assertContains(response, "test new yes reg")
        self.assertContains(response, "test old yes reg")
        
    def testCorrectNumberOfEventsForSecondState(self):
        url = reverse('events:summaryReport') + self.createGetQuery('New South Wales', 2019)
        response = self.client.get(url, follow=True)
        self.assertNotContains(response, "test old not reg")
        self.assertNotContains(response, "future event")
        self.assertNotContains(response, "test new yes reg")
        self.assertNotContains(response, "test old yes reg")

    def testCorrectTeamNumber(self):
        url = reverse('events:summaryReport') + self.createGetQuery('Victoria', 2019)
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Teams: 3")

    def testCorrectStudentNumber(self):
        url = reverse('events:summaryReport') + self.createGetQuery('Victoria', 2019)
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Students: 4")

    def testCorrectGender(self):
        url = reverse('events:summaryReport') + self.createGetQuery('Victoria', 2019)
        response = self.client.get(url, follow=True)
        self.assertContains(response, r"25%F, 50%M, 25% other")
    
    def testWorkshop(self):
        url = reverse('events:summaryReport') + self.createGetQuery('Victoria', 2019)
        response = self.client.get(url, follow=True)
        self.assertContains(response, r"25%F, 25%M, 50% other")

    def testWorkshopNoAttendees(self):
        WorkshopAttendee.objects.all().delete()
        url = reverse('events:summaryReport') + self.createGetQuery('Victoria', 2019)
        response = self.client.get(url, follow=True)
        self.assertContains(response, r"0%F, 0%M, 0% other")

    def testVenues(self):
        url = reverse('events:summaryReport') + self.createGetQuery('Victoria', 2019)
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Venue 1", 1)
        self.assertContains(response, "None", 4)

    def testNoSelection(self):
        url = reverse('events:summaryReport')
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Select State and Year for Activity Summary Report")

    def testPost(self):
        url = reverse('events:summaryReport') + self.createGetQuery('Victoria', 2019)
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 405)
