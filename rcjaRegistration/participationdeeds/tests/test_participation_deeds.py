import datetime

from django.test import TestCase
from django.urls import reverse
from django.http import HttpRequest

from common.baseTests import createStates, createUsers, createSchools, createEvents, createTeams, createWorkshopAttendees
from participationdeeds.models import ParticipationDeed
from participationdeeds.tokens import dumps_school_or_mentor, deeds_available_for_event
from participationdeeds.participants import match_participant
from teams.models import Student
from workshops.models import WorkshopAttendee


class ParticipationDeedBase(TestCase):
    def setUp(self):
        createStates(self)
        createUsers(self)
        createSchools(self)
        createEvents(self)
        createTeams(self)

        self.state1.participationDeedText = '<p>Please <b>agree</b> to participate.</p><script>alert(1)</script>'
        self.state1.save()

        self.event = self.state1_openCompetition
        self.event.electronicParticipationDeedsEnabled = True
        self.event.save()

        self.team = self.state1_event1_team1
        self.student = Student.objects.create(
            team=self.team,
            firstName='Alice',
            lastName='Smith',
            yearLevel=7,
            gender='female',
        )


class TestTokensAndAvailability(ParticipationDeedBase):
    def test_deeds_available_when_enabled_and_before_start(self):
        self.assertTrue(deeds_available_for_event(self.event))

    def test_deeds_unavailable_when_disabled(self):
        self.event.electronicParticipationDeedsEnabled = False
        self.event.save()
        self.assertFalse(deeds_available_for_event(self.event))

    def test_deeds_available_on_start_date(self):
        self.event.startDate = datetime.date.today()
        self.event.save()
        self.assertTrue(deeds_available_for_event(self.event))

    def test_deeds_unavailable_after_start(self):
        self.event.startDate = self.state1_pastCompetition.startDate
        self.event.save()
        self.assertFalse(deeds_available_for_event(self.event))

    def test_school_link_rejected_when_disabled(self):
        self.event.electronicParticipationDeedsEnabled = False
        self.event.save()
        token = dumps_school_or_mentor(self.event, school=self.school1_state1)
        url = reverse('participationdeeds:sign_participation_deed', kwargs={'token': token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)


class TestMatchingAndSigning(ParticipationDeedBase):
    def test_match_exact_unique(self):
        matched = match_participant(
            self.event,
            self.student.firstName,
            self.student.lastName,
            self.student.yearLevel,
            school=self.school1_state1,
        )
        self.assertEqual(matched, self.student)

    def test_match_miss_returns_none(self):
        matched = match_participant(
            self.event,
            'Nope',
            'Nobody',
            99,
            school=self.school1_state1,
        )
        self.assertIsNone(matched)

    def test_school_magic_link_auto_attaches_on_exact_match(self):
        token = dumps_school_or_mentor(self.event, school=self.school1_state1)
        url = reverse('participationdeeds:sign_participation_deed', kwargs={'token': token})

        response = self.client.post(url, {
            'firstName': self.student.firstName,
            'lastName': self.student.lastName,
            'yearLevel': str(self.student.yearLevel),
            'agree': True,
            'parentName': 'Parent One',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thank you')

        self.student.refresh_from_db()
        self.assertIsNotNone(self.student.participationDeed_id)
        self.assertEqual(self.student.participationDeed.parentName, 'Parent One')

    def test_school_magic_link_silent_unattached_on_miss(self):
        token = dumps_school_or_mentor(self.event, school=self.school1_state1)
        url = reverse('participationdeeds:sign_participation_deed', kwargs={'token': token})

        response = self.client.post(url, {
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


class TestMentorUI(ParticipationDeedBase):
    def setUp(self):
        super().setUp()
        self.client.login(
            request=HttpRequest(),
            username=self.email_user_state1_school1_mentor1,
            password=self.password,
        )
        self.user_state1_school1_mentor1.currentlySelectedSchool = self.school1_state1
        self.user_state1_school1_mentor1.save()

    def test_event_details_shows_magic_link_when_enabled(self):
        response = self.client.get(reverse('events:details', kwargs={'eventID': self.event.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'participation-deeds/sign/')
        self.assertContains(response, 'Participation deeds')

    def test_event_details_hides_when_disabled(self):
        self.event.electronicParticipationDeedsEnabled = False
        self.event.save()
        response = self.client.get(reverse('events:details', kwargs={'eventID': self.event.id}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'participation-deeds/sign/')

    def test_mentor_summary_lists_unattached_with_attach(self):
        deed = ParticipationDeed.objects.create(
            parentName='Attach Parent',
            submittedFirstName='Unmatched',
            submittedLastName='Kid',
            submittedYearLevel='7',
            school=self.school1_state1,
            originalEvent=self.event,
        )
        url = reverse('participationdeeds:mentor_summary', kwargs={'eventID': self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student.firstName)
        self.assertContains(response, 'Incomplete')
        self.assertContains(response, 'Unattached deeds')
        self.assertContains(response, 'Unmatched')
        self.assertContains(response, reverse('participationdeeds:attach', kwargs={
            'eventID': self.event.id,
            'deedID': deed.id,
        }))

    def test_attach_unattached_deed(self):
        deed = ParticipationDeed.objects.create(
            parentName='Attach Parent',
            submittedFirstName='Unmatched',
            submittedLastName='Kid',
            submittedYearLevel='7',
            school=self.school1_state1,
            originalEvent=self.event,
        )
        url = reverse('participationdeeds:attach', kwargs={
            'eventID': self.event.id,
            'deedID': deed.id,
        })
        response = self.client.post(url, {'student': self.student.pk})
        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertEqual(self.student.participationDeed_id, deed.pk)

    def test_summary_requires_coordinator(self):
        response = self.client.get(reverse('participationdeeds:coordinator_summary', kwargs={'eventID': self.event.id}))
        self.assertEqual(response.status_code, 403)

    def test_summary_ok_for_coordinator(self):
        self.client.logout()
        self.client.login(
            request=HttpRequest(),
            username=self.email_user_state1_fullcoordinator,
            password=self.password,
        )
        response = self.client.get(reverse('participationdeeds:coordinator_summary', kwargs={'eventID': self.event.id}))
        self.assertEqual(response.status_code, 200)


class TestWorkshopStudentOnly(TestCase):
    def setUp(self):
        createStates(self)
        createUsers(self)
        createSchools(self)
        createEvents(self)
        createWorkshopAttendees(self)

        self.event = self.state1_openWorkshop
        self.event.electronicParticipationDeedsEnabled = True
        self.event.save()

    def test_teachers_not_matched(self):
        teacher = WorkshopAttendee.objects.create(
            event=self.event,
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
            self.event,
            teacher.firstName,
            teacher.lastName,
            teacher.yearLevel,
            school=teacher.school,
        )
        self.assertIsNone(matched)
