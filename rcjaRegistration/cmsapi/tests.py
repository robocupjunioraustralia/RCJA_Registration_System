from common.baseTests.populateDatabase import createStates, createUsers, createEvents

from django.test import TestCase

class TestCMSIntegration(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createEvents(cls)

        cls.url = "/api/v1/cms/integration/linkEvent/"
        cls.secret = "TESTONLY_slfgdjheaklfgjb34wuhgb35789gbne97urgblskdg"
        cls.cmsEventId = "25_VI_STATE_427"

    def test_link_event_success(self):
        """
        Correct Bearer token and a valid event => 200 OK and cmsEventId is set
        """
        headers = {
            "HTTP_AUTHORIZATION": f"Bearer {self.secret}",
        }
        data = {
            "eventId": self.state1_openCompetition.id,
            "cmsEventId": self.cmsEventId,
        }
        response = self.client.post(self.url, data, **headers)
        self.assertEqual(response.status_code, 200, response.content)

        # Refresh from DB to check if the event was updated
        self.state1_openCompetition.refresh_from_db()
        self.assertEqual(self.state1_openCompetition.cmsEventId, self.cmsEventId)

    def test_link_event_workshop_fails(self):
        """
        Attempting to set cmsEventId on a workshop event should fail (400)
        """
        headers = {
            "HTTP_AUTHORIZATION": f"Bearer {self.secret}",
        }
        data = {
            "eventId": self.state1_openWorkshop.id,
            "cmsEventId": self.cmsEventId,
        }
        response = self.client.post(self.url, data, **headers)
        self.assertEqual(response.status_code, 400, response.content)

        # Ensure it did not update
        self.state1_openWorkshop.refresh_from_db()
        self.assertIsNone(self.state1_openWorkshop.cmsEventId)

    def test_link_event_missing_event_id(self):
        """
        Missing 'eventId' or 'cmsEventId' => 400 Bad Request
        """
        headers = {
            "HTTP_AUTHORIZATION": f"Bearer {self.secret}",
        }
        data = {
            # "eventId": self.state1_openCompetition.id, # intentionally omitted
            "cmsEventId": self.cmsEventId,
        }
        response = self.client.post(self.url, data, **headers)
        self.assertEqual(response.status_code, 400, response.content)

    def test_link_event_no_auth_header(self):
        """
        No Authorization header => 403 Forbidden (assuming your permission class)
        """
        data = {
            "eventId": self.state1_openCompetition.id,
            "cmsEventId": self.cmsEventId,
        }
        # Note: No Bearer token here
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 403, response.content)

    def test_link_event_wrong_auth_header(self):
        """
        Wrong Bearer token => 403 Forbidden
        """
        headers = {
            "HTTP_AUTHORIZATION": "Bearer WRONG_TOKEN",
        }
        data = {
            "eventId": self.state1_openCompetition.id,
            "cmsEventId": self.cmsEventId,
        }
        response = self.client.post(self.url, data, **headers)
        self.assertEqual(response.status_code, 403, response.content)

