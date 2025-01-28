from django.test import TestCase, override_settings
from django.urls import reverse
from django.http import HttpRequest
from django.core.exceptions import ValidationError
from django.contrib.admin.sites import site
from users.models import User
from events.admin import EventAdmin
from events.models import Event
from common.baseTests.populateDatabase import createStates, createUsers, createEvents
import jwt

class TestCMSView(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createEvents(cls)

    def setUp(self):
        self.competition = self.state1_openCompetition
        self.workshop    = self.state1_openWorkshop

        self.url_competition = reverse("events:cms", args=[self.competition.id])
        self.url_workshop    = reverse("events:cms", args=[self.workshop.id])

        self.cmsEventId = "25_VI_STATE_427"

    def test_cms_redirect_if_cmsEventId_exists(self):
        """If cmsEventId is already set, it should redirect to CMS_EVENT_URL_VIEW for coordinators"""
        self.client.login(request=HttpRequest(), email=self.email_user_state1_fullcoordinator, password=self.password)

        self.competition.cmsEventId = self.cmsEventId
        self.competition.save()

        response = self.client.get(self.url_competition)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.cmsEventId, response.url)

    def test_cms_redirect_if_cmsEventId_exists_not_coordinator(self):
        """If cmsEventId is already set, it should redirect to CMS_EVENT_URL_VIEW for non-coordinators"""
        self.client.login(request=HttpRequest(), email=self.email_user_notstaff, password=self.password)

        self.competition.cmsEventId = self.cmsEventId
        self.competition.save()

        response = self.client.get(self.url_competition)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.cmsEventId, response.url)

    def test_cms_redirect_if_cmsEventId_exists_not_logged_in(self):
        """If cmsEventId is already set, it should redirect to CMS_EVENT_URL_VIEW for non logged in users"""
        self.competition.cmsEventId = self.cmsEventId
        self.competition.save()

        response = self.client.get(self.url_competition)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.cmsEventId, response.url)

    def test_cms_permission_denied_if_event_not_competition(self):
        """If the event is a workshop, raise PermissionDenied => 403"""
        self.client.login(request=HttpRequest(), email=self.email_user_state1_fullcoordinator, password=self.password)

        response = self.client.get(self.url_workshop)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "The CMS for this event is unavailable", status_code=403)

    def test_cms_permission_denied_if_not_coordinator(self):
        """If user is not a coordinator for the event's state, return 403"""
        self.client.login(request=HttpRequest(), email=self.email_user_notstaff, password=self.password)

        response = self.client.get(self.url_competition)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "The CMS for this event is unavailable", status_code=403)

    @override_settings(
        CMS_JWT_SECRET="TEST_SECRET",
        CMS_EVENT_URL_CREATE="https://rcjcms.local/rcj_cms/event/create?token={TOKEN}"
    )
    def test_cms_generates_jwt_and_redirects(self):
        """If event has no cmsEventId, user is a coordinator, event is competition => redirect with JWT"""
        self.client.login(request=HttpRequest(), email=self.email_user_state1_fullcoordinator, password=self.password)

        self.competition.cmsEventId = None
        self.competition.save()

        response = self.client.get(self.url_competition)
        self.assertEqual(response.status_code, 302)
        self.assertIn("https://rcjcms.local/rcj_cms/event/create", response.url)

        token = response.url.split("token=")[1]
        payload = jwt.decode(token, "TEST_SECRET", algorithms=["HS256"])
        self.assertEqual(payload["event"], self.competition.id)

        user_obj = User.objects.get(email=self.email_user_state1_fullcoordinator)
        self.assertEqual(payload["user"], user_obj.id)

class TestEventCMSEventIdValidation(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createEvents(cls)

    # def test_cmsEventId_only_for_competitions(self):
    #     """Setting cmsEventId on a non-competition event should error"""
    #     event = self.state1_openWorkshop
    #     event.eventType = "workshop"
    #     event.cmsEventId = "SHOULD_FAIL"
    #     event.save()
    #     self.assertRaises(ValidationError, event.clean)

    def test_cmsEventId_ok_for_competition(self):
        """Setting cmsEventId on a competition event should not error"""
        event = self.state1_openCompetition
        event.eventType = "competition"
        event.cmsEventId = "SHOULD_PASS"
        try:
            event.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

class TestEventAdminCMSLink(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createEvents(cls)

    def setUp(self):
        self.admin_site = EventAdmin(Event, site)
        self.competition = self.state1_openCompetition
        self.workshop = self.state1_openWorkshop

    def test_link_view_if_cmsEventId_exists(self):
        """Should return a 'View' link if cmsEventId is set"""
        self.competition.cmsEventId = "25_VI_STATE_427"
        self.competition.save()
        link_html = self.admin_site.cmsLink(self.competition)
        self.assertIn("View", link_html)

    def test_link_create_if_no_cmsEventId_competition(self):
        """Should return a 'Create' link if no cmsEventId and eventType='competition'"""
        self.competition.cmsEventId = None
        link_html = self.admin_site.cmsLink(self.competition)
        self.assertIn("Create", link_html)

    def test_link_none_if_not_competition(self):
        """Should return None if eventType is not a competition"""
        self.workshop.cmsEventId = None
        link_html = self.admin_site.cmsLink(self.workshop)
        self.assertEqual(link_html, "CMS Unavailable")
