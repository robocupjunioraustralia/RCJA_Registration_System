import datetime

from django.test import TestCase

from participationdeeds.participants import match_participant
from participationdeeds.tokens import deeds_available_for_event
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
