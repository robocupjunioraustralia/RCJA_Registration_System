import datetime

from django.test import TestCase
from django.urls import reverse

from events.models import AvailableDivision, Event
from participationdeeds.models import ParticipationDeed
from participationdeeds.tokens import dumps_school_or_mentor
from teams.models import Student, Team
from workshops.models import WorkshopAttendee

from .common import (
    ParticipationDeedsFixture,
    SchoolMentorLoginMixin,
    IndependentMentorLoginMixin,
    OtherSchoolMentorLoginMixin,
    CoordinatorLoginMixin,
)


# ***** Sign page *****

class SignPageBase(ParticipationDeedsFixture):
    """Shared sign page tests; subclasses set sign_event and token helpers."""

    sign_event = None

    def school_token(self):
        return dumps_school_or_mentor(self.sign_event, school=self.school1_state1)

    def independent_token(self):
        return dumps_school_or_mentor(self.sign_event, mentorUser=self.user_state1_independent_mentor5)

    def test_page_load_ok_school_token(self):
        response = self.client.get(self.sign_url(self.school_token()))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Participation deed')
        self.assertContains(response, self.invoiceSettings.invoiceFromName)
        self.assertContains(response, self.invoiceSettings.invoiceFromDetails)

    def test_page_load_ok_independent_token(self):
        response = self.client.get(self.sign_url(self.independent_token()))
        self.assertEqual(response.status_code, 200)

    def test_rejects_incorrect_url(self):
        response = self.client.get(self.sign_url('not-a-valid-token'))
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'unavailable', status_code=400)

    def test_does_not_load_when_disabled(self):
        self.sign_event.electronicParticipationDeedsEnabled = False
        self.sign_event.save()
        response = self.client.get(self.sign_url(self.school_token()))
        self.assertEqual(response.status_code, 400)

    def test_does_not_load_after_start_date(self):
        self.sign_event.startDate = self.state1_pastCompetition.startDate
        self.sign_event.save()
        response = self.client.get(self.sign_url(self.school_token()))
        self.assertEqual(response.status_code, 400)

    def test_post_silent_unattached_on_miss(self):
        response = self.client.post(self.sign_url(self.school_token()), {
            'firstName': 'Missing',
            'lastName': 'Child',
            'yearLevel': '7',
            'agree': True,
            'parentName': 'Parent Two',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thank you')
        deed = ParticipationDeed.objects.get(parentName='Parent Two', originalEvent=self.sign_event)
        self.assertEqual(deed.submittedFirstName, 'Missing')
        self.assertFalse(deed.isAttached())

    def test_post_invalid_sign_form_redisplays(self):
        student = self.school_sign_student
        response = self.client.post(self.sign_url(self.school_token()), {
            'firstName': student.firstName,
            'lastName': student.lastName,
            'yearLevel': str(student.yearLevel),
            'parentName': '',
            'agree': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'participationdeeds/sign.html')
        self.assertContains(response, student.firstName)
        self.assertFalse(ParticipationDeed.objects.filter(
            submittedFirstName=student.firstName,
            originalEvent=self.sign_event,
        ).exists())


class TestSignPage_Competition(SignPageBase, TestCase):
    def setUp(self):
        super().setUp()
        self.sign_event = self.competition
        self.school_sign_student = self.school_student
        self.independent_sign_student = self.independent_student

    def test_post_lookup_then_sign_auto_attaches_school(self):
        token = self.school_token()
        url = self.sign_url(token)
        student = self.school_sign_student

        lookup = self.client.post(url, {
            'firstName': student.firstName,
            'lastName': student.lastName,
            'yearLevel': str(student.yearLevel),
        })
        self.assertEqual(lookup.status_code, 200)
        self.assertContains(lookup, 'id_parentName')
        self.assertContains(lookup, f'School: <strong>{self.school1_state1}</strong>', html=True)

        response = self.client.post(url, {
            'firstName': student.firstName,
            'lastName': student.lastName,
            'yearLevel': str(student.yearLevel),
            'agree': True,
            'parentName': 'Parent One',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thank you')
        student.refresh_from_db()
        self.assertIsNotNone(student.participationDeed_id)
        self.assertEqual(student.participationDeed.parentName, 'Parent One')

    def test_sign_records_request_metadata_from_forwarded_for(self):
        student = self.school_sign_student
        response = self.client.post(
            self.sign_url(self.school_token()),
            {
                'firstName': student.firstName,
                'lastName': student.lastName,
                'yearLevel': str(student.yearLevel),
                'agree': True,
                'parentName': 'Meta Parent',
            },
            HTTP_X_FORWARDED_FOR='203.0.113.10, 10.0.0.1',
            HTTP_USER_AGENT='DeedTestAgent/1.0',
            REMOTE_ADDR='127.0.0.1',
        )
        self.assertEqual(response.status_code, 200)
        deed = ParticipationDeed.objects.get(parentName='Meta Parent')
        self.assertEqual(deed.ipAddress, '203.0.113.10')
        self.assertEqual(deed.userAgent, 'DeedTestAgent/1.0')
        self.assertIsNone(deed.loggedInUser_id)

    def test_sign_records_logged_in_user(self):
        self.client.force_login(self.user_state1_school1_mentor1)
        student = self.school_sign_student
        response = self.client.post(
            self.sign_url(self.school_token()),
            {
                'firstName': student.firstName,
                'lastName': student.lastName,
                'yearLevel': str(student.yearLevel),
                'agree': True,
                'parentName': 'Logged In Parent',
            },
            HTTP_X_FORWARDED_FOR='198.51.100.20',
            HTTP_USER_AGENT='LoggedInAgent/2.0',
        )
        self.assertEqual(response.status_code, 200)
        deed = ParticipationDeed.objects.get(parentName='Logged In Parent')
        self.assertEqual(deed.ipAddress, '198.51.100.20')
        self.assertEqual(deed.userAgent, 'LoggedInAgent/2.0')
        self.assertEqual(deed.loggedInUser_id, self.user_state1_school1_mentor1.pk)

    def test_post_auto_attaches_independent(self):
        student = self.independent_sign_student
        response = self.client.post(self.sign_url(self.independent_token()), {
            'firstName': student.firstName,
            'lastName': student.lastName,
            'yearLevel': str(student.yearLevel),
            'agree': True,
            'parentName': 'Indie Parent',
        })
        self.assertEqual(response.status_code, 200)
        student.refresh_from_db()
        self.assertEqual(student.participationDeed.parentName, 'Indie Parent')


class TestSignPage_Workshop(SignPageBase, TestCase):
    def setUp(self):
        super().setUp()
        self.sign_event = self.workshop
        self.school_sign_student = self.state1_event1_workshopAttendee1
        self.independent_sign_student = self.independent_workshop_student

    def test_post_lookup_then_sign_auto_attaches_school(self):
        token = self.school_token()
        url = self.sign_url(token)
        student = self.school_sign_student

        lookup = self.client.post(url, {
            'firstName': student.firstName,
            'lastName': student.lastName,
            'yearLevel': str(student.yearLevel),
        })
        self.assertEqual(lookup.status_code, 200)
        self.assertContains(lookup, 'id_parentName')

        response = self.client.post(url, {
            'firstName': student.firstName,
            'lastName': student.lastName,
            'yearLevel': str(student.yearLevel),
            'agree': True,
            'parentName': 'Workshop Parent One',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thank you')
        student.refresh_from_db()
        self.assertIsNotNone(student.participationDeed_id)
        self.assertEqual(student.participationDeed.parentName, 'Workshop Parent One')

    def test_post_auto_attaches_independent(self):
        student = self.independent_sign_student
        response = self.client.post(self.sign_url(self.independent_token()), {
            'firstName': student.firstName,
            'lastName': student.lastName,
            'yearLevel': str(student.yearLevel),
            'agree': True,
            'parentName': 'Workshop Indie Parent',
        })
        self.assertEqual(response.status_code, 200)
        student.refresh_from_db()
        self.assertEqual(student.participationDeed.parentName, 'Workshop Indie Parent')

# ***** Mentor summary *****

class MentorSummaryAccessBase(ParticipationDeedsFixture):
    """Shared access / availability tests for mentor summary; subclasses set login + expected student."""

    summary_event = None
    own_student_attr = None
    other_student_attr = None
    own_school = None
    own_mentor = None

    def mentor_url(self, event=None):
        return self.mentor_summary_url(event or self.summary_event)

    def test_page_load_ok(self):
        response = self.client.get(self.mentor_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Participation deeds')

    def test_filters_to_own_students_and_teams(self):
        response = self.client.get(self.mentor_url())
        self.assertEqual(response.status_code, 200)
        own = getattr(self, self.own_student_attr)
        other = getattr(self, self.other_student_attr)
        self.assertContains(response, own.firstName)
        self.assertNotContains(response, other.firstName)

    def test_unattached_deeds_show_for_own_context(self):
        kwargs = {'school': self.own_school} if self.own_school is not None else {'mentorUser': self.own_mentor}
        deed = self.create_unattached_deed(**kwargs, firstName='OwnUnattached', event=self.summary_event)
        other_kwargs = {'school': self.school2_state1} if self.own_school is not None else {'school': self.school1_state1}
        self.create_unattached_deed(**other_kwargs, firstName='OtherUnattached', event=self.summary_event)

        response = self.client.get(self.mentor_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Unattached deeds')
        self.assertContains(response, 'OwnUnattached')
        self.assertNotContains(response, 'OtherUnattached')
        self.assertContains(response, self.attach_url(deed, self.summary_event))

    def test_attach_button_hidden_when_no_students_without_deed(self):
        from participationdeeds.participants import participants_without_deed
        kwargs = {'school': self.own_school} if self.own_school is not None else {'mentorUser': self.own_mentor}
        deed = self.create_unattached_deed(**kwargs, firstName='NoAttachUnattached', event=self.summary_event)
        for student in participants_without_deed(
            self.summary_event,
            school=self.own_school,
            mentorUser=self.own_mentor,
        ):
            try:
                student_year = int(student.yearLevel)
            except (TypeError, ValueError):
                student_year = 7
            student.participationDeed = ParticipationDeed.objects.create(
                parentName='Fill Parent',
                submittedFirstName=student.firstName,
                submittedLastName=student.lastName,
                submittedYearLevel=student_year,
                school=self.own_school,
                mentorUser=self.own_mentor,
                originalEvent=self.summary_event,
            )
            student.save()

        response = self.client.get(self.mentor_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'NoAttachUnattached')
        self.assertNotContains(response, self.attach_url(deed, self.summary_event))
        self.assertContains(response, 'Delete')

    def test_does_not_load_when_disabled(self):
        self.summary_event.electronicParticipationDeedsEnabled = False
        self.summary_event.save()
        response = self.client.get(self.mentor_url())
        self.assertEqual(response.status_code, 403)

    def test_does_not_load_if_no_registrations(self):
        empty_event = Event.objects.create(
            year=self.year,
            state=self.state1,
            name='Empty Competition For Deeds',
            eventType=self.summary_event.eventType,
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
        response = self.client.get(self.mentor_url(empty_event))
        self.assertEqual(response.status_code, 403)

    def test_does_not_load_when_event_unavailable(self):
        self.summary_event.status = 'draft'
        self.summary_event.save()
        response = self.client.get(self.mentor_url())
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'This event is unavailable', status_code=403)

    def test_mentor_cannot_access_coordinator_page(self):
        response = self.client.get(self.coordinator_summary_url(self.summary_event))
        self.assertEqual(response.status_code, 403)

class TestMentorSummary_SchoolMentor(SchoolMentorLoginMixin, MentorSummaryAccessBase, TestCase):
    own_student_attr = 'school_student'
    other_student_attr = 'independent_student'

    def setUp(self):
        super().setUp()
        self.summary_event = self.competition
        self.own_school = self.school1_state1
        self.own_mentor = None

class TestMentorSummary_IndependentMentor(IndependentMentorLoginMixin, MentorSummaryAccessBase, TestCase):
    own_student_attr = 'independent_student'
    other_student_attr = 'school_student'

    def setUp(self):
        super().setUp()
        self.summary_event = self.competition
        self.own_school = None
        self.own_mentor = self.user_state1_independent_mentor5

class TestMentorSummary_WorkshopSchoolMentor(SchoolMentorLoginMixin, MentorSummaryAccessBase, TestCase):
    own_student_attr = 'state1_event1_workshopAttendee1'
    other_student_attr = 'independent_workshop_student'

    def setUp(self):
        super().setUp()
        self.summary_event = self.workshop
        self.own_school = self.school1_state1
        self.own_mentor = None

    def test_page_load_ok(self):
        response = self.client.get(self.mentor_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Student attendees')
        self.assertContains(response, self.state1_event1_workshopAttendee1.firstName)

class TestMentorSummary_WorkshopIndependentMentor(IndependentMentorLoginMixin, MentorSummaryAccessBase, TestCase):
    own_student_attr = 'independent_workshop_student'
    other_student_attr = 'state1_event1_workshopAttendee1'

    def setUp(self):
        super().setUp()
        self.summary_event = self.workshop
        self.own_school = None
        self.own_mentor = self.user_state1_independent_mentor5

    def test_page_load_ok(self):
        response = self.client.get(self.mentor_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Student attendees')
        self.assertContains(response, self.independent_workshop_student.firstName)

class TestMentorSummary_OtherSchoolCannotAccessOwnFilter(OtherSchoolMentorLoginMixin, ParticipationDeedsFixture, TestCase):
    def test_cannot_see_school1_students(self):
        response = self.client.get(self.mentor_summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.other_school_student.firstName)
        self.assertNotContains(response, self.school_student.firstName)
        self.assertNotContains(response, self.independent_student.firstName)

    def test_cannot_see_school1_workshop_attendees(self):
        WorkshopAttendee.objects.create(
            event=self.workshop,
            mentorUser=self.user_state1_school2_mentor3,
            school=self.school2_state1,
            division=self.division3,
            firstName='OtherSchool',
            lastName='WorkshopKid',
            yearLevel='8',
            attendeeType='student',
            gender='male',
        )
        response = self.client.get(self.mentor_summary_url(self.workshop))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'OtherSchool')
        self.assertNotContains(response, self.state1_event1_workshopAttendee1.firstName)
        self.assertNotContains(response, self.independent_workshop_student.firstName)

# ***** Attach page *****

class AttachPageAccessBase(ParticipationDeedsFixture):
    attach_event = None
    own_student_attr = None
    other_student_attr = None
    own_school = None
    own_mentor = None

    def own_unattached_deed(self):
        kwargs = {'school': self.own_school} if self.own_school is not None else {'mentorUser': self.own_mentor}
        return self.create_unattached_deed(**kwargs, event=self.attach_event)

    def attach_deed_url(self, deed):
        return self.attach_url(deed, self.attach_event)

    def mentor_url(self):
        return self.mentor_summary_url(self.attach_event)

    def test_page_load_ok(self):
        deed = self.own_unattached_deed()
        response = self.client.get(self.attach_deed_url(deed))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Attach participation deed')

    def test_students_filtered_on_attach_page(self):
        deed = self.own_unattached_deed()
        response = self.client.get(self.attach_deed_url(deed))
        self.assertEqual(response.status_code, 200)
        own = getattr(self, self.own_student_attr)
        other = getattr(self, self.other_student_attr)
        self.assertContains(response, str(own))
        self.assertNotContains(response, str(other))

    def test_post_attaches_deed(self):
        deed = self.own_unattached_deed()
        own = getattr(self, self.own_student_attr)
        response = self.client.post(self.attach_deed_url(deed), {'student': own.pk})
        self.assertEqual(response.status_code, 302)
        own.refresh_from_db()
        self.assertEqual(own.participationDeed_id, deed.pk)

    def test_students_listed_alphabetically_by_first_name(self):
        from participationdeeds.participants import participants_without_deed
        deed = self.own_unattached_deed()
        students = list(participants_without_deed(
            self.attach_event,
            school=self.own_school,
            mentorUser=self.own_mentor,
        ))
        self.assertGreaterEqual(len(students), 1)
        response = self.client.get(self.attach_deed_url(deed))
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        ordered = list(form.fields['student'].queryset)
        self.assertEqual(
            [student.firstName for student in ordered],
            sorted(student.firstName for student in ordered),
        )

    def test_post_rejects_student_outside_queryset(self):
        deed = self.own_unattached_deed()
        other = getattr(self, self.other_student_attr)
        response = self.client.post(self.attach_deed_url(deed), {'student': other.pk})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        other.refresh_from_db()
        self.assertIsNone(other.participationDeed_id)

    def test_denied_for_attached_deed(self):
        deed = self.own_unattached_deed()
        own = getattr(self, self.own_student_attr)
        own.participationDeed = deed
        own.save()
        response = self.client.get(self.attach_deed_url(deed))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.mentor_url())

    def test_does_not_load_when_disabled(self):
        deed = self.own_unattached_deed()
        self.attach_event.electronicParticipationDeedsEnabled = False
        self.attach_event.save()
        response = self.client.get(self.attach_deed_url(deed))
        self.assertEqual(response.status_code, 403)

    def test_redirects_when_no_students_without_deed(self):
        deed = self.own_unattached_deed()
        own = getattr(self, self.own_student_attr)
        year_level = own.yearLevel
        try:
            year_level = int(year_level)
        except (TypeError, ValueError):
            year_level = 7
        own.participationDeed = ParticipationDeed.objects.create(
            parentName='Existing Parent',
            submittedFirstName=own.firstName,
            submittedLastName=own.lastName,
            submittedYearLevel=year_level,
            school=self.own_school,
            mentorUser=self.own_mentor,
            originalEvent=self.attach_event,
        )
        own.save()
        from participationdeeds.participants import participants_without_deed
        for student in participants_without_deed(
            self.attach_event,
            school=self.own_school,
            mentorUser=self.own_mentor,
        ):
            try:
                student_year = int(student.yearLevel)
            except (TypeError, ValueError):
                student_year = 7
            student.participationDeed = ParticipationDeed.objects.create(
                parentName='Fill Parent',
                submittedFirstName=student.firstName,
                submittedLastName=student.lastName,
                submittedYearLevel=student_year,
                school=self.own_school,
                mentorUser=self.own_mentor,
                originalEvent=self.attach_event,
            )
            student.save()

        response = self.client.get(self.attach_deed_url(deed))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.mentor_url())

    def test_mentor_cannot_access_coordinator_page(self):
        response = self.client.get(self.coordinator_summary_url(self.attach_event))
        self.assertEqual(response.status_code, 403)

class TestAttachPage_SchoolMentor(SchoolMentorLoginMixin, AttachPageAccessBase, TestCase):
    own_student_attr = 'school_student'
    other_student_attr = 'independent_student'

    def setUp(self):
        super().setUp()
        self.attach_event = self.competition
        self.own_school = self.school1_state1
        self.own_mentor = None

    def test_cannot_access_other_school_deed(self):
        deed = self.create_unattached_deed(school=self.school2_state1)
        response = self.client.get(self.attach_deed_url(deed))
        self.assertEqual(response.status_code, 403)

    def test_cannot_access_independent_deed(self):
        deed = self.create_unattached_deed(mentorUser=self.user_state1_independent_mentor5)
        response = self.client.get(self.attach_deed_url(deed))
        self.assertEqual(response.status_code, 403)

class TestAttachPage_IndependentMentor(IndependentMentorLoginMixin, AttachPageAccessBase, TestCase):
    own_student_attr = 'independent_student'
    other_student_attr = 'school_student'

    def setUp(self):
        super().setUp()
        self.attach_event = self.competition
        self.own_school = None
        self.own_mentor = self.user_state1_independent_mentor5

    def test_cannot_access_school_deed(self):
        deed = self.create_unattached_deed(school=self.school1_state1)
        response = self.client.get(self.attach_deed_url(deed))
        self.assertEqual(response.status_code, 403)

class TestAttachPage_WorkshopSchoolMentor(SchoolMentorLoginMixin, AttachPageAccessBase, TestCase):
    own_student_attr = 'state1_event1_workshopAttendee1'
    other_student_attr = 'independent_workshop_student'

    def setUp(self):
        super().setUp()
        self.attach_event = self.workshop
        self.own_school = self.school1_state1
        self.own_mentor = None

    def test_cannot_access_other_school_deed(self):
        deed = self.create_unattached_deed(school=self.school2_state1, event=self.workshop)
        response = self.client.get(self.attach_deed_url(deed))
        self.assertEqual(response.status_code, 403)

    def test_cannot_access_independent_deed(self):
        deed = self.create_unattached_deed(
            mentorUser=self.user_state1_independent_mentor5,
            event=self.workshop,
        )
        response = self.client.get(self.attach_deed_url(deed))
        self.assertEqual(response.status_code, 403)

class TestAttachPage_WorkshopIndependentMentor(IndependentMentorLoginMixin, AttachPageAccessBase, TestCase):
    own_student_attr = 'independent_workshop_student'
    other_student_attr = 'state1_event1_workshopAttendee1'

    def setUp(self):
        super().setUp()
        self.attach_event = self.workshop
        self.own_school = None
        self.own_mentor = self.user_state1_independent_mentor5

    def test_cannot_access_school_deed(self):
        deed = self.create_unattached_deed(school=self.school1_state1, event=self.workshop)
        response = self.client.get(self.attach_deed_url(deed))
        self.assertEqual(response.status_code, 403)

class TestAttachPage_OtherSchoolMentor(OtherSchoolMentorLoginMixin, ParticipationDeedsFixture, TestCase):
    def test_cannot_access_school1_deed(self):
        deed = self.create_unattached_deed(school=self.school1_state1)
        response = self.client.get(self.attach_url(deed))
        self.assertEqual(response.status_code, 403)

    def test_cannot_access_school1_workshop_deed(self):
        deed = self.create_unattached_deed(school=self.school1_state1, event=self.workshop)
        response = self.client.get(self.attach_url(deed, self.workshop))
        self.assertEqual(response.status_code, 403)

# ***** Coordinator summary *****

class CoordinatorSummaryAccessBase(CoordinatorLoginMixin, ParticipationDeedsFixture):
    """Shared coordinator summary tests; subclasses set summary_event."""

    summary_event = None

    def summary_url(self):
        return self.coordinator_summary_url(self.summary_event)

    def test_page_load_ok(self):
        response = self.client.get(self.summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Participation deeds summary')

    def test_unattached_deeds_show(self):
        self.create_unattached_deed(
            school=self.school1_state1,
            firstName='CoordUnattached',
            event=self.summary_event,
        )
        response = self.client.get(self.summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CoordUnattached')

    def test_unattached_only_group_with_no_participants(self):
        from schools.models import School
        orphan_school = School.objects.create(name='Orphan School', state=self.state1, region=self.region1)
        self.create_unattached_deed(
            school=orphan_school,
            firstName='OrphanUnattached',
            event=self.summary_event,
        )
        response = self.client.get(self.summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Orphan School')
        self.assertContains(response, 'OrphanUnattached')

    def test_unattached_only_independent_group_with_no_participants(self):
        from users.models import User
        orphan_mentor = User.objects.create_user(
            adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION,
            email='orphan.indie@test.com',
            password=self.password,
            homeState=self.state1,
            first_name='Orphan',
            last_name='IndieMentor',
        )
        self.create_unattached_deed(
            mentorUser=orphan_mentor,
            firstName='IndieOrphanUnattached',
            event=self.summary_event,
        )
        response = self.client.get(self.summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Independent:')
        self.assertContains(response, 'IndieOrphanUnattached')
        self.assertContains(response, orphan_mentor.fullname_or_email())

    def test_shows_disabled_message_when_turned_off(self):
        self.summary_event.electronicParticipationDeedsEnabled = False
        self.summary_event.save()
        response = self.client.get(self.summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'not enabled')


class TestCoordinatorSummary(CoordinatorSummaryAccessBase, TestCase):
    def setUp(self):
        super().setUp()
        self.summary_event = self.competition

    def test_filters_to_correct_students_and_teams(self):
        response = self.client.get(self.summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.school1_state1))
        self.assertContains(response, str(self.school2_state1))
        self.assertContains(response, self.school_student.firstName)
        self.assertContains(response, self.other_school_student.firstName)
        self.assertContains(response, self.independent_student.firstName)


class TestCoordinatorSummary_Workshop(CoordinatorSummaryAccessBase, TestCase):
    def setUp(self):
        super().setUp()
        self.summary_event = self.workshop
        self.other_school_workshop_student = WorkshopAttendee.objects.create(
            event=self.workshop,
            mentorUser=self.user_state1_school2_mentor3,
            school=self.school2_state1,
            division=self.division3,
            firstName='OtherSchool',
            lastName='WorkshopKid',
            yearLevel='8',
            attendeeType='student',
            gender='male',
        )

    def test_filters_to_correct_attendees(self):
        response = self.client.get(self.summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.school1_state1))
        self.assertContains(response, str(self.school2_state1))
        self.assertContains(response, self.state1_event1_workshopAttendee1.firstName)
        self.assertContains(response, self.other_school_workshop_student.firstName)
        self.assertContains(response, self.independent_workshop_student.firstName)


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

class TestEventDetails_SchoolMentor(SchoolMentorLoginMixin, EventDetailsDeedsBase, TestCase):
    pass

class TestEventDetails_IndependentMentor(IndependentMentorLoginMixin, EventDetailsDeedsBase, TestCase):
    pass

class TestEventDetails_Workshop(SchoolMentorLoginMixin, ParticipationDeedsFixture, TestCase):
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
