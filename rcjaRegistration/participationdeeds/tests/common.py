from django.http import HttpRequest
from django.urls import reverse

from common.baseTests import (
    createStates,
    createUsers,
    createSchools,
    createEvents,
    createTeams,
    createWorkshopAttendees,
)
from participationdeeds.models import ParticipationDeed
from teams.models import Student, Team
from workshops.models import WorkshopAttendee


class ParticipationDeedsFixture:
    """Shared database fixture for participation deed tests using common.baseTests."""

    def setUp(self):
        createStates(self)
        createUsers(self)
        createSchools(self)
        createEvents(self)
        createTeams(self)
        createWorkshopAttendees(self)

        self.state1.participationDeedText = '<p>Please <b>agree</b> to participate.</p><script>alert(1)</script>'
        self.state1.save()

        self.competition = self.state1_openCompetition
        self.competition.electronicParticipationDeedsEnabled = True
        self.competition.save()

        self.workshop = self.state1_openWorkshop
        self.workshop.electronicParticipationDeedsEnabled = True
        self.workshop.save()

        self.school_team = self.state1_event1_team1
        self.school_student = Student.objects.create(
            team=self.school_team,
            firstName='Alice',
            lastName='Smith',
            yearLevel=7,
            gender='female',
        )

        self.other_school_team = Team.objects.create(
            event=self.competition,
            division=self.division3,
            mentorUser=self.user_state1_school2_mentor3,
            school=self.school2_state1,
            name='Other School Team',
            hardwarePlatform=self.hardwarePlatform,
            softwarePlatform=self.softwarePlatform,
        )
        self.other_school_student = Student.objects.create(
            team=self.other_school_team,
            firstName='OtherSchool',
            lastName='Student',
            yearLevel=8,
            gender='male',
        )

        self.independent_team = Team.objects.create(
            event=self.competition,
            division=self.division3,
            mentorUser=self.user_state1_independent_mentor5,
            school=None,
            name='Independent Team',
            hardwarePlatform=self.hardwarePlatform,
            softwarePlatform=self.softwarePlatform,
        )
        self.independent_student = Student.objects.create(
            team=self.independent_team,
            firstName='Indie',
            lastName='MentorKid',
            yearLevel=9,
            gender='other',
        )

        self.independent_workshop_student = WorkshopAttendee.objects.create(
            event=self.workshop,
            mentorUser=self.user_state1_independent_mentor5,
            school=None,
            division=self.division3,
            firstName='Indie',
            lastName='WorkshopKid',
            yearLevel='9',
            attendeeType='student',
            gender='other',
        )

        self.own_school = None
        self.own_mentor = None

    def create_unattached_deed(self, *, school=None, mentorUser=None, event=None, firstName='Unmatched', lastName='Kid'):
        return ParticipationDeed.objects.create(
            parentName='Attach Parent',
            submittedFirstName=firstName,
            submittedLastName=lastName,
            submittedYearLevel=7,
            school=school,
            mentorUser=mentorUser,
            originalEvent=event or self.competition,
        )

    def mentor_summary_url(self, event=None):
        return reverse('participationdeeds:mentor_summary', kwargs={'eventID': (event or self.competition).id})

    def attach_url(self, deed, event=None):
        return reverse('participationdeeds:attach', kwargs={
            'eventID': (event or self.competition).id,
            'deedID': deed.id,
        })

    def coordinator_summary_url(self, event=None):
        return reverse('participationdeeds:coordinator_summary', kwargs={'eventID': (event or self.competition).id})

    def event_details_url(self, event=None):
        return reverse('events:details', kwargs={'eventID': (event or self.competition).id})

    def sign_url(self, token):
        return reverse('participationdeeds:sign_participation_deed', kwargs={'token': token})


class SchoolMentorLoginMixin:
    """Log in as school 1 mentor with that school selected."""

    def setUp(self):
        super().setUp()
        self.client.login(
            request=HttpRequest(),
            username=self.email_user_state1_school1_mentor1,
            password=self.password,
        )
        self.user_state1_school1_mentor1.currentlySelectedSchool = self.school1_state1
        self.user_state1_school1_mentor1.save()


class IndependentMentorLoginMixin:
    """Log in as independent mentor (no school selected)."""

    def setUp(self):
        super().setUp()
        self.client.login(
            request=HttpRequest(),
            username=self.email_user_state1_independent_mentor5,
            password=self.password,
        )
        self.user_state1_independent_mentor5.currentlySelectedSchool = None
        self.user_state1_independent_mentor5.save()


class OtherSchoolMentorLoginMixin:
    """Log in as school 2 mentor with that school selected."""

    def setUp(self):
        super().setUp()
        self.client.login(
            request=HttpRequest(),
            username=self.email_user_state1_school2_mentor3,
            password=self.password,
        )
        self.user_state1_school2_mentor3.currentlySelectedSchool = self.school2_state1
        self.user_state1_school2_mentor3.save()


class CoordinatorLoginMixin:
    """Log in as state 1 full coordinator."""

    def setUp(self):
        super().setUp()
        self.client.login(
            request=HttpRequest(),
            username=self.email_user_state1_fullcoordinator,
            password=self.password,
        )
