from common.baseTests.populateDatabase import createStates, createUsers, createEvents

from django.test import TestCase
from django.urls import reverse

from .views import StateViewSet
from regions.models import State

# Unit tests

class TestEventsBaseQueryset(TestCase):
    def setUp(self):
        createStates(self)
        createUsers(self)
        createEvents(self)

    def testPublishedEventIncluded(self):
        qs = StateViewSet.eventsBaseQueryset(self, 'ST1')
        self.assertIn(self.state1_openCompetition, qs)

    def testPublishedEventIncludedLowercase(self):
        qs = StateViewSet.eventsBaseQueryset(self, 'st1')
        self.assertIn(self.state1_openCompetition, qs)

    def testDraftEventNotIncluded(self):
        self.state1_openCompetition.status = 'draft'
        self.state1_openCompetition.save()

        qs = StateViewSet.eventsBaseQueryset(self, 'ST1')
        self.assertNotIn(self.state1_openCompetition, qs)

    def testDisplayWebsiteFalseNotIncluded(self):
        self.year.displayEventsOnWebsite = False
        self.year.save()

        qs = StateViewSet.eventsBaseQueryset(self, 'ST1')
        self.assertNotIn(self.state1_openCompetition, qs)

    def testGlobalEventIncluded(self):
        self.stateNational = State.objects.create(typeGlobal=True, name='National', abbreviation='NAT', typeWebsite=True)
        self.state1_openCompetition.globalEvent = True
        self.state1_openCompetition.save()

        qs = StateViewSet.eventsBaseQueryset(self, 'NAT')
        self.assertIn(self.state1_openCompetition, qs)

    def testGlobalEventNotIncluded(self):
        self.state1_openCompetition.globalEvent = True
        self.state1_openCompetition.save()

        qs = StateViewSet.eventsBaseQueryset(self, 'ST1')
        self.assertNotIn(self.state1_openCompetition, qs)

    def testGlobalEventIncluded_includeGlobal(self):
        self.state1_openCompetition.globalEvent = True
        self.state1_openCompetition.save()

        qs = StateViewSet.eventsBaseQueryset(self, 'ST1', includeGlobal=True)
        self.assertIn(self.state1_openCompetition, qs)

    def testGlobalEventIncluded_globalState(self):
        self.stateNational = State.objects.create(typeGlobal=True, typeCompetition=True, name='National', abbreviation='NAT', typeWebsite=True)
        self.state1_openCompetition.state = self.stateNational
        self.state1_openCompetition.save()

        qs = StateViewSet.eventsBaseQueryset(self, 'NAT')
        self.assertIn(self.state1_openCompetition, qs)

# View tests

class TestStates(TestCase):
    def setUp(self):
        createStates(self)
        createUsers(self)
        createEvents(self)

    # List view

    def testListViewLoads(self):
        response = self.client.get('/api/v1/public/states/')
        self.assertEqual(response.status_code, 200)

    def testCorrectListContent(self):
        response = self.client.get('/api/v1/public/states/')
        self.assertJSONEqual(response.content, [{"id":self.state1.id,"name":"State 1","abbreviation":"ST1"},{"id":self.state2.id,"name":"State 2","abbreviation":"ST2"}])

    def testCorrectListContentNotWebsite(self):
        self.state1.typeWebsite = False
        self.state1.save()

        response = self.client.get('/api/v1/public/states/')
        self.assertJSONEqual(response.content, [{"id":self.state2.id,"name":"State 2","abbreviation":"ST2"}])

    def testPaginationOnePageNoLink(self):
        response = self.client.get('/api/v1/public/states/')
        self.assertFalse('Link' in response.headers)

    def testPaginationTwoPagesLink(self):
        for i in range(50):
            self.state1 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name=f'New State {i}', abbreviation=f'N{i}', typeWebsite=True)

        response = self.client.get('/api/v1/public/states/')
        self.assertTrue('Link' in response.headers)
        self.assertEqual(
            response.headers['Link'],
            '<http://testserver/api/v1/public/states/?page=2>; rel="next", <http://testserver/api/v1/public/states/?page=2>; rel="last"'
        )

    def testPaginationPageTwoLoads(self):
        for i in range(50):
            self.state1 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name=f'New State {i}', abbreviation=f'N{i}', typeWebsite=True)

        response = self.client.get('/api/v1/public/states/?page=2')
        self.assertEqual(response.status_code, 200)

    # Details view

    def testDetailViewLoads(self):
        response = self.client.get('/api/v1/public/states/ST1/')
        self.assertEqual(response.status_code, 200)

    def testDetailViewLoadsLowercase(self):
        response = self.client.get('/api/v1/public/states/st1/')
        self.assertEqual(response.status_code, 200)

    def testCorrectDetailContent(self):
        response = self.client.get('/api/v1/public/states/ST1/')
        self.assertJSONEqual(response.content, {"id":self.state1.id,"name":"State 1","abbreviation":"ST1"})

    def testNotWebsiteState404(self):
        self.state1.typeWebsite = False
        self.state1.save()

        response = self.client.get('/api/v1/public/states/ST1/')
        self.assertEqual(response.status_code, 404)

    def testPostDenied(self):
        response = self.client.post('/api/v1/public/states/ST1/', data={})
        self.assertEqual(response.status_code, 403)

class TestEvents(TestCase):
    def setUp(self):
        createStates(self)
        createUsers(self)
        createEvents(self)

    # All events

    def testAllEventsLoads(self):
        response = self.client.get('/api/v1/public/states/ST1/allEvents/')
        self.assertEqual(response.status_code, 200)

    def testAllEventsInAllEvents(self):
        response = self.client.get('/api/v1/public/states/ST1/allEvents/')
        self.assertContains(response, 'State 1 Open Competition')
        self.assertContains(response, 'State 1 Closed Competition 1')
        self.assertContains(response, 'State 1 Closed Competition 2')
        self.assertContains(response, 'State 1 Open Workshop')
        self.assertContains(response, 'State 1 Past Competition')

    def testAllEventsDetailedLoads(self):
        response = self.client.get('/api/v1/public/states/ST1/allEventsDetailed/')
        self.assertEqual(response.status_code, 200)

    def testAllEventsInAllEventsDetailed(self):
        response = self.client.get('/api/v1/public/states/ST1/allEventsDetailed/')
        self.assertContains(response, 'State 1 Open Competition')
        self.assertContains(response, 'State 1 Closed Competition 1')
        self.assertContains(response, 'State 1 Closed Competition 2')
        self.assertContains(response, 'State 1 Open Workshop')
        self.assertContains(response, 'State 1 Past Competition')

    # Upcoming events

    def testUpcomingEventsLoads(self):
        response = self.client.get('/api/v1/public/states/ST1/upcomingEvents/')
        self.assertEqual(response.status_code, 200)

    def testUpcomingEventsLoadsLowercase(self):
        response = self.client.get('/api/v1/public/states/st1/upcomingEvents/')
        self.assertEqual(response.status_code, 200)

    def testAllUpcomingEventsInUpcomingEvents(self):
        response = self.client.get('/api/v1/public/states/ST1/upcomingEvents/')
        self.assertContains(response, 'State 1 Open Competition')
        self.assertContains(response, 'State 1 Closed Competition 1')
        self.assertContains(response, 'State 1 Closed Competition 2')
        self.assertContains(response, 'State 1 Open Workshop')

    def testPastEventNotInUpcomingEvents(self):
        response = self.client.get('/api/v1/public/states/ST1/upcomingEvents/')
        self.assertNotContains(response, 'State 1 Past Competition')

    def testUpcomingEventsNotWebsiteState404(self):
        self.state1.typeWebsite = False
        self.state1.save()

        response = self.client.get('/api/v1/public/states/ST1/upcomingEvents/')
        self.assertEqual(response.status_code, 404)

    def testUpcomingCompetitionsLoads(self):
        response = self.client.get('/api/v1/public/states/ST1/upcomingCompetitions/')
        self.assertEqual(response.status_code, 200)

    def testUpcomingCompetitionsInUpcomingCompetitions(self):
        response = self.client.get('/api/v1/public/states/ST1/upcomingCompetitions/')
        self.assertContains(response, 'State 1 Open Competition')
        self.assertContains(response, 'State 1 Closed Competition 1')
        self.assertContains(response, 'State 1 Closed Competition 2')

    def testOtherStateEventNotInUpcomingCompetitions(self):
        response = self.client.get('/api/v1/public/states/ST1/upcomingCompetitions/')
        self.assertNotContains(response, 'State 2 Open Competition')

    def testPastEventNotInUpcomingCompetitions(self):
        response = self.client.get('/api/v1/public/states/ST1/upcomingCompetitions/')
        self.assertNotContains(response, 'State 1 Past Competition')

    def testWorkshopNotInUpcomingCompetitions(self):
        response = self.client.get('/api/v1/public/states/ST1/upcomingCompetitions/')
        self.assertNotContains(response, 'State 1 Open Workshop')

    def testUpcomingWorkshopsLoads(self):
        response = self.client.get('/api/v1/public/states/ST1/upcomingWorkshops/')
        self.assertEqual(response.status_code, 200)

    def testWorkshopInUpcomingWorkshops(self):
        response = self.client.get('/api/v1/public/states/ST1/upcomingWorkshops/')
        self.assertContains(response, 'State 1 Open Workshop')

    # Past events

    def testPastEventsLoads(self):
        response = self.client.get('/api/v1/public/states/ST1/pastEvents/')
        self.assertEqual(response.status_code, 200)

    def testPastCompetitionsLoads(self):
        response = self.client.get('/api/v1/public/states/ST1/pastCompetitions/')
        self.assertEqual(response.status_code, 200)

    def testPastEventInPastCompetitions(self):
        response = self.client.get('/api/v1/public/states/ST1/pastCompetitions/')
        self.assertContains(response, 'State 1 Past Competition')

    def testUpcomingCompetitionNotInPastCompetitions(self):
        response = self.client.get('/api/v1/public/states/ST1/pastCompetitions/')
        self.assertNotContains(response, 'State 1 Open Competition')

    def testPastWorkshopsLoads(self):
        response = self.client.get('/api/v1/public/states/ST1/pastWorkshops/')
        self.assertEqual(response.status_code, 200)

class TestCMSIntegration(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createEvents(cls)

        cls.url = "/api/v1/public/cms/linkEvent/"
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
