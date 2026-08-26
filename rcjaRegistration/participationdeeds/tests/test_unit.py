import datetime

from django.core import signing
from django.test import TestCase

from events.models import eventCoordinatorEditPermissions
from participationdeeds.models import ParticipationDeed
from participationdeeds.participants import match_participant, participant_deed_counts
from participationdeeds.tokens import (
    SALT_SCHOOL,
    deeds_available_for_event,
    dumps_school_or_mentor,
    loads_school_or_mentor,
)
from workshops.models import WorkshopAttendee

from .common import ParticipationDeedsFixture


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

    def test_deeds_unavailable_when_start_date_none(self):
        self.competition.startDate = None
        self.competition.save()
        self.assertFalse(deeds_available_for_event(self.competition))

    def test_loads_school_or_mentor_missing_school_and_mentor(self):
        token = signing.dumps({'event': self.competition.pk}, salt=SALT_SCHOOL)
        with self.assertRaises(signing.BadSignature):
            loads_school_or_mentor(token)

    def test_dumps_and_loads_school(self):
        token = dumps_school_or_mentor(self.competition, school=self.school1_state1)
        event, school, mentorUser = loads_school_or_mentor(token)
        self.assertEqual(event, self.competition)
        self.assertEqual(school, self.school1_state1)
        self.assertIsNone(mentorUser)


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


class TestParticipantDeedCounts(ParticipationDeedsFixture, TestCase):
    def test_counts_school_students(self):
        complete, incomplete = participant_deed_counts(
            self.competition,
            school=self.school1_state1,
        )
        self.assertEqual(complete, 0)
        self.assertEqual(incomplete, 1)

        deed = self.create_unattached_deed(school=self.school1_state1)
        self.school_student.participationDeed = deed
        self.school_student.save()

        complete, incomplete = participant_deed_counts(
            self.competition,
            school=self.school1_state1,
        )
        self.assertEqual(complete, 1)
        self.assertEqual(incomplete, 0)

    def test_counts_independent_separately(self):
        complete, incomplete = participant_deed_counts(
            self.competition,
            mentorUser=self.user_state1_independent_mentor5,
        )
        self.assertEqual(complete, 0)
        self.assertEqual(incomplete, 1)


class TestParticipationDeedMethods(ParticipationDeedsFixture, TestCase):
    def setUp(self):
        super().setUp()
        self.deed = ParticipationDeed.objects.create(
            parentName='Parent Name',
            submittedFirstName='Alice',
            submittedLastName='Smith',
            submittedYearLevel=7,
            school=self.school1_state1,
            originalEvent=self.competition,
        )

    def test_getState(self):
        self.assertEqual(self.deed.getState(), self.state1)

    def test_submittedFullName(self):
        self.assertEqual(self.deed.submittedFullName(), 'Alice Smith')

    def test_str(self):
        self.assertEqual(str(self.deed), 'Alice Smith (Parent Name)')

    def test_isAttached_false(self):
        self.assertFalse(self.deed.isAttached())

    def test_isAttached_student(self):
        self.school_student.participationDeed = self.deed
        self.school_student.save()
        self.assertTrue(self.deed.isAttached())

    def test_isAttached_workshop_attendee(self):
        attendee = WorkshopAttendee.objects.create(
            event=self.workshop,
            mentorUser=self.user_state1_school1_mentor1,
            school=self.school1_state1,
            division=self.division3,
            firstName='Workshop',
            lastName='Kid',
            yearLevel='7',
            attendeeType='student',
            gender='female',
            participationDeed=self.deed,
        )
        self.assertTrue(self.deed.isAttached())
        self.assertEqual(attendee.participationDeed_id, self.deed.pk)

    def test_create_sets_participationDeedText(self):
        self.assertEqual(self.deed.participationDeedText, self.state1.participationDeedText)

    def test_update_does_not_set_participationDeedText(self):
        original_text = self.deed.participationDeedText
        self.state1.participationDeedText = '<p>Changed after signing</p>'
        self.state1.save()
        self.deed.parentName = 'Updated Parent'
        self.deed.save()
        self.deed.refresh_from_db()
        self.assertEqual(self.deed.participationDeedText, original_text)
        self.assertEqual(self.deed.parentName, 'Updated Parent')

    def test_bleachedParticipationDeedText(self):
        bleached = self.deed.bleachedParticipationDeedText()
        self.assertIn('<b>agree</b>', bleached)
        self.assertNotIn('<script>', bleached)

    def test_stateCoordinatorPermissions(self):
        self.assertEqual(
            ParticipationDeed.stateCoordinatorPermissions('full'),
            eventCoordinatorEditPermissions('full'),
        )
