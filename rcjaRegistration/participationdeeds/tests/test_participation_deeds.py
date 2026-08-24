import datetime

from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse

from common.baseTests import (
    createStates,
    createUsers,
    createSchools,
    createEvents,
    createTeams,
    createWorkshopAttendees,
)
from events.models import AvailableDivision, Event
from participationdeeds.models import ParticipationDeed
from participationdeeds.participants import match_participant
from participationdeeds.tokens import dumps_school_or_mentor, deeds_available_for_event
from teams.models import Student, Team
from workshops.models import WorkshopAttendee


# ***** Shared fixtures *****

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


# ***** Tokens and matching *****

class TestTokensAndAvailability(ParticipationDeedsFixture, TestCase):
    def test_deeds_available_when_enabled_and_before_start(self):
        self.assertTrue(deeds_available_for_event(self.competition))

    def test_deeds_unavailable_when_disabled(self):
        self.competition.electronicParticipationDeedsEnabled = False
        self.competition.save()
        self.assertFalse(deeds_available_for_event(self.competition))

    def test_deeds_available_on_start_date(self):
        self.competition.startDate = datetime.date.today()
        self.competition.save()
        self.assertTrue(deeds_available_for_event(self.competition))

    def test_deeds_unavailable_after_start(self):
        self.competition.startDate = self.state1_pastCompetition.startDate
        self.competition.save()
        self.assertFalse(deeds_available_for_event(self.competition))


class TestMatching(ParticipationDeedsFixture, TestCase):
    def test_match_exact_unique(self):
        matched = match_participant(
            self.competition,
            self.school_student.firstName,
            self.school_student.lastName,
            self.school_student.yearLevel,
            school=self.school1_state1,
        )
        self.assertEqual(matched, self.school_student)

    def test_match_miss_returns_none(self):
        matched = match_participant(
            self.competition,
            'Nope',
            'Nobody',
            99,
            school=self.school1_state1,
        )
        self.assertIsNone(matched)

    def test_teachers_not_matched(self):
        teacher = WorkshopAttendee.objects.create(
            event=self.workshop,
            mentorUser=self.user_state1_school1_mentor1,
            school=self.school1_state1,
            division=self.division3,
            firstName='Teach',
            lastName='Er',
            yearLevel='7-12',
            attendeeType='teacher',
            gender='other',
            email='t@example.com',
        )
        matched = match_participant(
            self.workshop,
            teacher.firstName,
            teacher.lastName,
            teacher.yearLevel,
            school=teacher.school,
        )
        self.assertIsNone(matched)


# ***** Sign page *****

class TestSignPage(ParticipationDeedsFixture, TestCase):
    def test_page_load_ok_school_token(self):
        token = dumps_school_or_mentor(self.competition, school=self.school1_state1)
        response = self.client.get(self.sign_url(token))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Participation deed')

    def test_page_load_ok_independent_token(self):
        token = dumps_school_or_mentor(self.competition, mentorUser=self.user_state1_independent_mentor5)
        response = self.client.get(self.sign_url(token))
        self.assertEqual(response.status_code, 200)

    def test_rejects_incorrect_url(self):
        response = self.client.get(self.sign_url('not-a-valid-token'))
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'unavailable', status_code=400)

    def test_does_not_load_when_disabled(self):
        self.competition.electronicParticipationDeedsEnabled = False
        self.competition.save()
        token = dumps_school_or_mentor(self.competition, school=self.school1_state1)
        response = self.client.get(self.sign_url(token))
        self.assertEqual(response.status_code, 400)

    def test_does_not_load_after_start_date(self):
        self.competition.startDate = self.state1_pastCompetition.startDate
        self.competition.save()
        token = dumps_school_or_mentor(self.competition, school=self.school1_state1)
        response = self.client.get(self.sign_url(token))
        self.assertEqual(response.status_code, 400)

    def test_post_lookup_then_sign_auto_attaches_school(self):
        token = dumps_school_or_mentor(self.competition, school=self.school1_state1)
        url = self.sign_url(token)

        lookup = self.client.post(url, {
            'firstName': self.school_student.firstName,
            'lastName': self.school_student.lastName,
            'yearLevel': str(self.school_student.yearLevel),
        })
        self.assertEqual(lookup.status_code, 200)
        self.assertContains(lookup, 'Parent / guardian')

        response = self.client.post(url, {
            'firstName': self.school_student.firstName,
            'lastName': self.school_student.lastName,
            'yearLevel': str(self.school_student.yearLevel),
            'agree': True,
            'parentName': 'Parent One',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thank you')
        self.school_student.refresh_from_db()
        self.assertIsNotNone(self.school_student.participationDeed_id)
        self.assertEqual(self.school_student.participationDeed.parentName, 'Parent One')

    def test_post_silent_unattached_on_miss(self):
        token = dumps_school_or_mentor(self.competition, school=self.school1_state1)
        response = self.client.post(self.sign_url(token), {
            'firstName': 'Missing',
            'lastName': 'Child',
            'yearLevel': '7',
            'agree': True,
            'parentName': 'Parent Two',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thank you')
        deed = ParticipationDeed.objects.get(parentName='Parent Two')
        self.assertEqual(deed.submittedFirstName, 'Missing')
        self.assertFalse(deed.isAttached())

    def test_post_auto_attaches_independent(self):
        token = dumps_school_or_mentor(self.competition, mentorUser=self.user_state1_independent_mentor5)
        response = self.client.post(self.sign_url(token), {
            'firstName': self.independent_student.firstName,
            'lastName': self.independent_student.lastName,
            'yearLevel': str(self.independent_student.yearLevel),
            'agree': True,
            'parentName': 'Indie Parent',
        })
        self.assertEqual(response.status_code, 200)
        self.independent_student.refresh_from_db()
        self.assertEqual(self.independent_student.participationDeed.parentName, 'Indie Parent')


# ***** Mentor summary *****

class MentorSummaryAccessBase(ParticipationDeedsFixture):
    """Shared access / availability tests for mentor summary; subclasses set login + expected student."""

    own_student_attr = None
    other_student_attr = None
    own_school = None
    own_mentor = None

    def test_page_load_ok(self):
        response = self.client.get(self.mentor_summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Participation deeds')

    def test_filters_to_own_students_and_teams(self):
        response = self.client.get(self.mentor_summary_url())
        self.assertEqual(response.status_code, 200)
        own = getattr(self, self.own_student_attr)
        other = getattr(self, self.other_student_attr)
        self.assertContains(response, own.firstName)
        self.assertNotContains(response, other.firstName)

    def test_unattached_deeds_show_for_own_context(self):
        kwargs = {'school': self.own_school} if self.own_school is not None else {'mentorUser': self.own_mentor}
        deed = self.create_unattached_deed(**kwargs, firstName='OwnUnattached')
        other_kwargs = {'school': self.school2_state1} if self.own_school is not None else {'school': self.school1_state1}
        self.create_unattached_deed(**other_kwargs, firstName='OtherUnattached')

        response = self.client.get(self.mentor_summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Unattached deeds')
        self.assertContains(response, 'OwnUnattached')
        self.assertNotContains(response, 'OtherUnattached')
        self.assertContains(response, self.attach_url(deed))

    def test_does_not_load_when_disabled(self):
        self.competition.electronicParticipationDeedsEnabled = False
        self.competition.save()
        response = self.client.get(self.mentor_summary_url())
        self.assertEqual(response.status_code, 403)

    def test_does_not_load_if_no_registrations(self):
        # Use a competition event with no teams for this actor
        empty_event = Event.objects.create(
            year=self.year,
            state=self.state1,
            name='Empty Competition For Deeds',
            eventType='competition',
            status='published',
            competition_defaultEntryFee=50,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=20)).date(),
            endDate=(datetime.datetime.now() + datetime.timedelta(days=20)).date(),
            registrationsOpenDate=(datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
            registrationsCloseDate=(datetime.datetime.now() + datetime.timedelta(days=10)).date(),
            directEnquiriesTo=self.user_state1_super1,
            electronicParticipationDeedsEnabled=True,
        )
        AvailableDivision.objects.create(event=empty_event, division=self.division3)
        response = self.client.get(self.mentor_summary_url(empty_event))
        self.assertEqual(response.status_code, 403)

    def test_mentor_cannot_access_coordinator_page(self):
        response = self.client.get(self.coordinator_summary_url())
        self.assertEqual(response.status_code, 403)


class TestMentorSummary_SchoolMentor(SchoolMentorLoginMixin, MentorSummaryAccessBase, TestCase):
    own_student_attr = 'school_student'
    other_student_attr = 'independent_student'

    def setUp(self):
        super().setUp()
        self.own_school = self.school1_state1
        self.own_mentor = None


class TestMentorSummary_IndependentMentor(IndependentMentorLoginMixin, MentorSummaryAccessBase, TestCase):
    own_student_attr = 'independent_student'
    other_student_attr = 'school_student'

    def setUp(self):
        super().setUp()
        self.own_school = None
        self.own_mentor = self.user_state1_independent_mentor5


class TestMentorSummary_OtherSchoolCannotAccessOwnFilter(OtherSchoolMentorLoginMixin, ParticipationDeedsFixture, TestCase):
    def test_cannot_see_school1_students(self):
        response = self.client.get(self.mentor_summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.other_school_student.firstName)
        self.assertNotContains(response, self.school_student.firstName)
        self.assertNotContains(response, self.independent_student.firstName)


# ***** Attach page *****

class AttachPageAccessBase(ParticipationDeedsFixture):
    own_student_attr = None
    other_student_attr = None
    own_school = None
    own_mentor = None

    def own_unattached_deed(self):
        kwargs = {'school': self.own_school} if self.own_school is not None else {'mentorUser': self.own_mentor}
        return self.create_unattached_deed(**kwargs)

    def test_page_load_ok(self):
        deed = self.own_unattached_deed()
        response = self.client.get(self.attach_url(deed))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Attach participation deed')

    def test_students_filtered_on_attach_page(self):
        deed = self.own_unattached_deed()
        response = self.client.get(self.attach_url(deed))
        self.assertEqual(response.status_code, 200)
        own = getattr(self, self.own_student_attr)
        other = getattr(self, self.other_student_attr)
        self.assertContains(response, str(own))
        self.assertNotContains(response, str(other))

    def test_post_attaches_deed(self):
        deed = self.own_unattached_deed()
        own = getattr(self, self.own_student_attr)
        response = self.client.post(self.attach_url(deed), {'student': own.pk})
        self.assertEqual(response.status_code, 302)
        own.refresh_from_db()
        self.assertEqual(own.participationDeed_id, deed.pk)

    def test_denied_for_attached_deed(self):
        deed = self.own_unattached_deed()
        own = getattr(self, self.own_student_attr)
        own.participationDeed = deed
        own.save()
        response = self.client.get(self.attach_url(deed))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.mentor_summary_url())

    def test_does_not_load_when_disabled(self):
        deed = self.own_unattached_deed()
        self.competition.electronicParticipationDeedsEnabled = False
        self.competition.save()
        response = self.client.get(self.attach_url(deed))
        self.assertEqual(response.status_code, 403)

    def test_mentor_cannot_access_coordinator_page(self):
        response = self.client.get(self.coordinator_summary_url())
        self.assertEqual(response.status_code, 403)


class TestAttachPage_SchoolMentor(SchoolMentorLoginMixin, AttachPageAccessBase, TestCase):
    own_student_attr = 'school_student'
    other_student_attr = 'independent_student'

    def setUp(self):
        super().setUp()
        self.own_school = self.school1_state1
        self.own_mentor = None

    def test_cannot_access_other_school_deed(self):
        deed = self.create_unattached_deed(school=self.school2_state1)
        response = self.client.get(self.attach_url(deed))
        self.assertEqual(response.status_code, 403)

    def test_cannot_access_independent_deed(self):
        deed = self.create_unattached_deed(mentorUser=self.user_state1_independent_mentor5)
        response = self.client.get(self.attach_url(deed))
        self.assertEqual(response.status_code, 403)


class TestAttachPage_IndependentMentor(IndependentMentorLoginMixin, AttachPageAccessBase, TestCase):
    own_student_attr = 'independent_student'
    other_student_attr = 'school_student'

    def setUp(self):
        super().setUp()
        self.own_school = None
        self.own_mentor = self.user_state1_independent_mentor5

    def test_cannot_access_school_deed(self):
        deed = self.create_unattached_deed(school=self.school1_state1)
        response = self.client.get(self.attach_url(deed))
        self.assertEqual(response.status_code, 403)


class TestAttachPage_OtherSchoolMentor(OtherSchoolMentorLoginMixin, ParticipationDeedsFixture, TestCase):
    def test_cannot_access_school1_deed(self):
        deed = self.create_unattached_deed(school=self.school1_state1)
        response = self.client.get(self.attach_url(deed))
        self.assertEqual(response.status_code, 403)


# ***** Coordinator summary *****

class TestCoordinatorSummary(CoordinatorLoginMixin, ParticipationDeedsFixture, TestCase):
    def test_page_load_ok(self):
        response = self.client.get(self.coordinator_summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Participation deeds summary')

    def test_filters_to_correct_students_and_teams(self):
        response = self.client.get(self.coordinator_summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.school1_state1))
        self.assertContains(response, str(self.school2_state1))
        self.assertContains(response, self.school_student.firstName)
        self.assertContains(response, self.other_school_student.firstName)
        self.assertContains(response, self.independent_student.firstName)

    def test_unattached_deeds_show(self):
        self.create_unattached_deed(school=self.school1_state1, firstName='CoordUnattached')
        response = self.client.get(self.coordinator_summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CoordUnattached')

    def test_shows_disabled_message_when_turned_off(self):
        self.competition.electronicParticipationDeedsEnabled = False
        self.competition.save()
        response = self.client.get(self.coordinator_summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'not enabled')


class TestCoordinatorSummary_MentorDenied(SchoolMentorLoginMixin, ParticipationDeedsFixture, TestCase):
    def test_school_mentor_denied(self):
        response = self.client.get(self.coordinator_summary_url())
        self.assertEqual(response.status_code, 403)


class TestCoordinatorSummary_IndependentMentorDenied(IndependentMentorLoginMixin, ParticipationDeedsFixture, TestCase):
    def test_independent_mentor_denied(self):
        response = self.client.get(self.coordinator_summary_url())
        self.assertEqual(response.status_code, 403)


# ***** Event details *****

class EventDetailsDeedsBase(ParticipationDeedsFixture):
    def test_contains_magic_link_when_enabled_and_registered(self):
        response = self.client.get(self.event_details_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'participation-deeds/sign/')
        self.assertContains(response, 'Participation deeds')

    def test_no_magic_link_when_turned_off(self):
        self.competition.electronicParticipationDeedsEnabled = False
        self.competition.save()
        response = self.client.get(self.event_details_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'participation-deeds/sign/')

    def test_no_magic_link_when_not_registered(self):
        empty_event = Event.objects.create(
            year=self.year,
            state=self.state1,
            name='No Reg Competition Deeds',
            eventType='competition',
            status='published',
            competition_defaultEntryFee=50,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=25)).date(),
            endDate=(datetime.datetime.now() + datetime.timedelta(days=25)).date(),
            registrationsOpenDate=(datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
            registrationsCloseDate=(datetime.datetime.now() + datetime.timedelta(days=10)).date(),
            directEnquiriesTo=self.user_state1_super1,
            electronicParticipationDeedsEnabled=True,
        )
        AvailableDivision.objects.create(event=empty_event, division=self.division3)
        response = self.client.get(self.event_details_url(empty_event))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'participation-deeds/sign/')

    def test_no_magic_link_after_start_date(self):
        self.competition.startDate = self.state1_pastCompetition.startDate
        self.competition.endDate = self.state1_pastCompetition.endDate
        self.competition.save()
        response = self.client.get(self.event_details_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'participation-deeds/sign/')


class TestEventDetails_SchoolMentor(SchoolMentorLoginMixin, EventDetailsDeedsBase, TestCase):
    def test_teams_table_shows_deed_column_when_enabled(self):
        response = self.client.get(self.event_details_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Participation deeds')
        self.assertContains(response, self.school_team.deedSummary())

    def test_teams_table_hides_deed_column_when_disabled(self):
        self.competition.electronicParticipationDeedsEnabled = False
        self.competition.save()
        response = self.client.get(self.event_details_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, f'<th>Participation deeds</th>')


class TestEventDetails_IndependentMentor(IndependentMentorLoginMixin, EventDetailsDeedsBase, TestCase):
    pass


class TestEventDetails_WorkshopTables(SchoolMentorLoginMixin, ParticipationDeedsFixture, TestCase):
    def test_attendees_table_shows_deed_column_when_enabled(self):
        response = self.client.get(self.event_details_url(self.workshop))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<th>Participation deed</th>')

    def test_attendees_table_hides_deed_column_when_disabled(self):
        self.workshop.electronicParticipationDeedsEnabled = False
        self.workshop.save()
        response = self.client.get(self.event_details_url(self.workshop))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<th>Participation deed</th>')


# ***** Team copy *****

class TestTeamCopyCopiesDeed(SchoolMentorLoginMixin, ParticipationDeedsFixture, TestCase):
    def test_copy_preserves_participation_deed(self):
        source_event = self.state1_closedCompetition1
        source_team = Team.objects.create(
            event=source_event,
            division=self.division3,
            mentorUser=self.user_state1_school1_mentor1,
            school=self.school1_state1,
            name='Source Copy Team',
            hardwarePlatform=self.hardwarePlatform,
            softwarePlatform=self.softwarePlatform,
        )
        source_student = Student.objects.create(
            team=source_team,
            firstName='Copy',
            lastName='Student',
            yearLevel=6,
            gender='female',
        )
        deed = ParticipationDeed.objects.create(
            parentName='Copy Parent',
            submittedFirstName='Copy',
            submittedLastName='Student',
            submittedYearLevel=6,
            school=self.school1_state1,
            originalEvent=source_event,
        )
        source_student.participationDeed = deed
        source_student.save()

        url = reverse('teams:copyTeam', kwargs={
            'eventID': self.competition.id,
            'sourceTeamID': source_team.id,
        })
        response = self.client.post(url, {
            'student_set-TOTAL_FORMS': 1,
            'student_set-INITIAL_FORMS': 0,
            'student_set-MIN_NUM_FORMS': 1,
            'student_set-MAX_NUM_FORMS': self.competition.maxMembersPerTeam,
            'name': source_team.name,
            'division': source_team.division.id,
            'hardwarePlatform': self.hardwarePlatform.id,
            'softwarePlatform': self.softwarePlatform.id,
            'student_set-0-firstName': source_student.firstName,
            'student_set-0-lastName': source_student.lastName,
            'student_set-0-yearLevel': source_student.yearLevel,
            'student_set-0-gender': source_student.gender,
        })
        self.assertEqual(response.status_code, 302)

        copied = Team.objects.get(event=self.competition, copiedFrom=source_team)
        copied_student = copied.student_set.get()
        self.assertEqual(copied_student.participationDeed_id, deed.pk)
