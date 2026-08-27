from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse

from common.baseTests import createEvents, createStates, createUsers
from coordination.models import Coordinator


class AdminSummaryPermissionsBase:
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createEvents(cls)

    def login(self, email):
        self.client.login(request=HttpRequest(), email=email, password=self.password)

    def set_coordinator_permission_level(self, coordinator, level):
        coordinator.permissionLevel = level
        coordinator.save()

    def single_page_url(self, event=None):
        event = event or self.state1_openCompetition
        return reverse('events:eventAdminSummarySpecific', kwargs={'eventID': event.id})

    def event_admin_summary_url(self):
        return reverse('events:eventAdminSummary')

    def event_choice_label(self, event):
        return f'{event.year} - {event.state} - {event.name}'

    def post_event_admin_summary(self, *, competitions=None, workshops=None):
        return self.client.post(self.event_admin_summary_url(), {
            'competitions': competitions or [],
            'workshops': workshops or [],
        })


# ***** singlePageAdminSummary *****

class TestSinglePageAdminSummary_NotLoggedIn(AdminSummaryPermissionsBase, TestCase):
    def test_redirects_to_login(self):
        response = self.client.get(self.single_page_url())
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class TestSinglePageAdminSummary_Mentor(AdminSummaryPermissionsBase, TestCase):
    def test_denied(self):
        self.login(self.email_user_state1_school1_mentor1)
        response = self.client.get(self.single_page_url())
        self.assertEqual(response.status_code, 403)


class TestSinglePageAdminSummary_FullCoordinator(AdminSummaryPermissionsBase, TestCase):
    def setUp(self):
        self.login(self.email_user_state1_fullcoordinator)

    def test_allows_own_state_competition(self):
        response = self.client.get(self.single_page_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.state1_openCompetition.name)
        self.assertContains(response, 'Teams')

    def test_allows_own_state_workshop(self):
        response = self.client.get(self.single_page_url(self.state1_openWorkshop))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.state1_openWorkshop.name)
        self.assertContains(response, 'Teachers')

    def test_denies_other_state_event(self):
        response = self.client.get(self.single_page_url(self.state2_openCompetition))
        self.assertEqual(response.status_code, 403)

    def test_post_not_allowed(self):
        response = self.client.post(self.single_page_url())
        self.assertEqual(response.status_code, 405)


class TestSinglePageAdminSummary_ViewCoordinator(AdminSummaryPermissionsBase, TestCase):
    def test_allows_own_state_event(self):
        self.login(self.email_user_state1_viewcoordinator)
        response = self.client.get(self.single_page_url())
        self.assertEqual(response.status_code, 200)


class TestSinglePageAdminSummary_BillingManager(AdminSummaryPermissionsBase, TestCase):
    def test_allows_own_state_event(self):
        self.set_coordinator_permission_level(self.coord_state1_fullcoordinator, 'billingmanager')
        self.login(self.email_user_state1_fullcoordinator)
        response = self.client.get(self.single_page_url())
        self.assertEqual(response.status_code, 200)


class TestSinglePageAdminSummary_EventManager(AdminSummaryPermissionsBase, TestCase):
    def test_allows_own_state_event(self):
        self.set_coordinator_permission_level(self.coord_state1_fullcoordinator, 'eventmanager')
        self.login(self.email_user_state1_fullcoordinator)
        response = self.client.get(self.single_page_url())
        self.assertEqual(response.status_code, 200)


class TestSinglePageAdminSummary_SchoolManager(AdminSummaryPermissionsBase, TestCase):
    def test_denied(self):
        self.set_coordinator_permission_level(self.coord_state1_fullcoordinator, 'schoolmanager')
        self.login(self.email_user_state1_fullcoordinator)
        response = self.client.get(self.single_page_url())
        self.assertEqual(response.status_code, 403)


class TestSinglePageAdminSummary_Superuser(AdminSummaryPermissionsBase, TestCase):
    def setUp(self):
        self.login(self.email_user_state1_super1)

    def test_allows_own_state_event(self):
        response = self.client.get(self.single_page_url())
        self.assertEqual(response.status_code, 200)

    def test_allows_other_state_event(self):
        response = self.client.get(self.single_page_url(self.state2_openCompetition))
        self.assertEqual(response.status_code, 200)

    def test_unknown_event_returns_404(self):
        response = self.client.get(reverse(
            'events:eventAdminSummarySpecific',
            kwargs={'eventID': 999999},
        ))
        self.assertEqual(response.status_code, 404)


class TestSinglePageAdminSummary_OtherStateCoordinator(AdminSummaryPermissionsBase, TestCase):
    def test_denies_other_state_event(self):
        self.login(self.email_user_state2_fullcoordinator)
        response = self.client.get(self.single_page_url())
        self.assertEqual(response.status_code, 403)


class TestSinglePageAdminSummary_GlobalCoordinator(AdminSummaryPermissionsBase, TestCase):
    def test_allows_event_in_any_state(self):
        self.coord_state1_fullcoordinator.state = None
        self.coord_state1_fullcoordinator.save()
        self.login(self.email_user_state1_fullcoordinator)
        response = self.client.get(self.single_page_url(self.state2_openCompetition))
        self.assertEqual(response.status_code, 200)


class TestSinglePageAdminSummary_MixedStatePermissions(AdminSummaryPermissionsBase, TestCase):
    def test_denied_when_no_event_permission_in_event_state(self):
        self.set_coordinator_permission_level(self.coord_state1_fullcoordinator, 'schoolmanager')
        Coordinator.objects.create(
            user=self.user_state1_fullcoordinator,
            state=self.state2,
            permissionLevel='full',
            position='Text',
        )
        self.login(self.email_user_state1_fullcoordinator)
        response = self.client.get(self.single_page_url())
        self.assertEqual(response.status_code, 403)


# ***** eventAdminSummary *****

class TestEventAdminSummary_NotLoggedIn(AdminSummaryPermissionsBase, TestCase):
    def test_get_redirects_to_login(self):
        response = self.client.get(self.event_admin_summary_url())
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_post_redirects_to_login(self):
        response = self.post_event_admin_summary(competitions=[self.state1_openCompetition.id])
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class TestEventAdminSummary_Mentor(AdminSummaryPermissionsBase, TestCase):
    def setUp(self):
        self.login(self.email_user_state1_school1_mentor1)

    def test_get_denied(self):
        response = self.client.get(self.event_admin_summary_url())
        self.assertEqual(response.status_code, 403)

    def test_post_denied(self):
        response = self.post_event_admin_summary(competitions=[self.state1_openCompetition.id])
        self.assertEqual(response.status_code, 403)


class TestEventAdminSummary_FullCoordinator(AdminSummaryPermissionsBase, TestCase):
    def setUp(self):
        self.login(self.email_user_state1_fullcoordinator)

    def test_get_allows_and_lists_own_state_events(self):
        response = self.client.get(self.event_admin_summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event_choice_label(self.state1_openCompetition))
        self.assertContains(response, self.event_choice_label(self.state1_openWorkshop))
        self.assertNotContains(response, self.event_choice_label(self.state2_openCompetition))
        self.assertNotContains(response, self.event_choice_label(self.state2_openWorkshop))

    def test_post_allows_own_state_competition(self):
        response = self.post_event_admin_summary(competitions=[self.state1_openCompetition.id])
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/adminDetails.html')
        self.assertContains(response, self.state1_openCompetition.name)

    def test_post_allows_own_state_workshop(self):
        response = self.post_event_admin_summary(workshops=[self.state1_openWorkshop.id])
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/adminDetails.html')
        self.assertContains(response, self.state1_openWorkshop.name)

    def test_post_rejects_other_state_event(self):
        response = self.post_event_admin_summary(competitions=[self.state2_openCompetition.id])
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/adminBlank.html')
        self.assertContains(response, 'Choose at least one event')
        self.assertNotContains(response, f'{self.state2_openCompetition.name} Registrations')


class TestEventAdminSummary_ViewCoordinator(AdminSummaryPermissionsBase, TestCase):
    def test_get_allowed(self):
        self.login(self.email_user_state1_viewcoordinator)
        response = self.client.get(self.event_admin_summary_url())
        self.assertEqual(response.status_code, 200)


class TestEventAdminSummary_BillingManager(AdminSummaryPermissionsBase, TestCase):
    def test_get_allowed(self):
        self.set_coordinator_permission_level(self.coord_state1_fullcoordinator, 'billingmanager')
        self.login(self.email_user_state1_fullcoordinator)
        response = self.client.get(self.event_admin_summary_url())
        self.assertEqual(response.status_code, 200)


class TestEventAdminSummary_EventManager(AdminSummaryPermissionsBase, TestCase):
    def test_get_allowed(self):
        self.set_coordinator_permission_level(self.coord_state1_fullcoordinator, 'eventmanager')
        self.login(self.email_user_state1_fullcoordinator)
        response = self.client.get(self.event_admin_summary_url())
        self.assertEqual(response.status_code, 200)


class TestEventAdminSummary_SchoolManager(AdminSummaryPermissionsBase, TestCase):
    def test_get_allowed(self):
        self.set_coordinator_permission_level(self.coord_state1_fullcoordinator, 'schoolmanager')
        self.login(self.email_user_state1_fullcoordinator)
        response = self.client.get(self.event_admin_summary_url())
        self.assertEqual(response.status_code, 200)


class TestEventAdminSummary_Superuser(AdminSummaryPermissionsBase, TestCase):
    def setUp(self):
        self.login(self.email_user_state1_super1)

    def test_get_lists_events_from_all_states(self):
        response = self.client.get(self.event_admin_summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event_choice_label(self.state1_openCompetition))
        self.assertContains(response, self.event_choice_label(self.state2_openCompetition))

    def test_post_allows_other_state_event(self):
        response = self.post_event_admin_summary(competitions=[self.state2_openCompetition.id])
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/adminDetails.html')
        self.assertContains(response, self.state2_openCompetition.name)


class TestEventAdminSummary_OtherStateCoordinator(AdminSummaryPermissionsBase, TestCase):
    def setUp(self):
        self.login(self.email_user_state2_fullcoordinator)

    def test_get_lists_own_state_events_only(self):
        response = self.client.get(self.event_admin_summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event_choice_label(self.state2_openCompetition))
        self.assertNotContains(response, self.event_choice_label(self.state1_openCompetition))

    def test_post_allows_own_state_event(self):
        response = self.post_event_admin_summary(competitions=[self.state2_openCompetition.id])
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/adminDetails.html')

    def test_post_rejects_other_state_event(self):
        response = self.post_event_admin_summary(competitions=[self.state1_openCompetition.id])
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/adminBlank.html')
        self.assertContains(response, 'Choose at least one event')
        self.assertNotContains(response, f'{self.state1_openCompetition.name} Registrations')


class TestEventAdminSummary_GlobalCoordinator(AdminSummaryPermissionsBase, TestCase):
    def test_get_lists_events_from_all_states(self):
        self.coord_state1_fullcoordinator.state = None
        self.coord_state1_fullcoordinator.save()
        self.login(self.email_user_state1_fullcoordinator)
        response = self.client.get(self.event_admin_summary_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event_choice_label(self.state1_openCompetition))
        self.assertContains(response, self.event_choice_label(self.state2_openCompetition))
