from common.baseTests.populateDatabase import createStates, createUsers, createEvents

from django.test import TestCase
from django.urls import reverse

from .views import StateViewSet
from regions.models import State
from events.models import Event

def createNoDateEvent(self):
    self.state1_noDatesCompetition = Event.objects.create(
        year = self.year,
        state = self.state1,
        name = 'State 1 No Dates Competition',
        eventType = 'competition',
        status = 'published',
        event_defaultEntryFee = 50,
        startDate = None,
        endDate = None,
        registrationsOpenDate = None,
        registrationsCloseDate = None,
        directEnquiriesTo = self.user_state1_super1,
        venue=self.venue2_state1,
    )

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

    # No Date Events
    def testNoDatesLoads(self):
        createNoDateEvent(self)
        response = self.client.get('/api/v1/public/states/ST1/allEventsDetailed/')
        self.assertContains(response, 'State 1 No Dates Competition')

    def testNoDatesAllDatesAreTBC(self):
        createNoDateEvent(self)
        response = self.client.get('/api/v1/public/states/ST1/allEventsDetailed/')
        noDatesEvent = response.json()[5]
        for field in ['startDate', 'endDate', 'registrationsOpenDate', 'registrationsCloseDate']:
            self.assertEqual(noDatesEvent[field],'TBC')