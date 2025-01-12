from django.test import TestCase, override_settings
from django.urls import reverse
from django.http import HttpRequest
from users.models import User
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
