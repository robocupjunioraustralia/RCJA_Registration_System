from common.baseTests import createStates, createUsers, createSchools
from django.test import TestCase
from django.urls import reverse

from django.http import HttpRequest

import datetime

from users.models import User
from association.models import AssociationMember

class Base_Tests_redirectsMiddleware:
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createSchools(cls)

    def testNoRedirect(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 200)

    def testPasswordChangeRedirect(self):
        self.user.forcePasswordChange = True
        self.user.forceDetailsUpdate = True
        self.user.save()

        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('password_change'))

    def testNoRedirectTermsAndConditions(self):
        self.user.forcePasswordChange = True
        self.user.forceDetailsUpdate = True
        self.user.save()

        response = self.client.get(reverse('users:termsAndConditions'))
        self.assertEqual(response.status_code, 200)

    def testUserDetailsUpdateRedirect(self):
        self.user.forceDetailsUpdate = True
        self.user.save()

        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('users:details'))

class Test_redirectsMiddleware_notStaff(Base_Tests_redirectsMiddleware, TestCase):
    def setUp(self):
        self.login = self.client.login(request=HttpRequest(), username=self.email_user_state1_school1_mentor1, password=self.password)
        self.user = self.user_state1_school1_mentor1

    def testNoRedirectAdminChangelog(self):
        self.user.adminChangelogVersionShown = 0
        self.user.save()

        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_no_redirect_not_association_member(self):
        self.assertRaises(AssociationMember.DoesNotExist, lambda: self.user.associationmember)

        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_no_redirect_association_member_no_rulesAcceptedDate(self):
        AssociationMember.objects.create(user=self.user, birthday=(datetime.datetime.now() + datetime.timedelta(days=-20*365)).date())

        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 200)

    def testSchoolDetailsUpdateRedirect(self):
        self.user.currentlySelectedSchool.forceSchoolDetailsUpdate = True
        self.user.currentlySelectedSchool.save()

        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('schools:details'))

    def testNoRedirectNoSchool(self):
        self.user.currentlySelectedSchool.forceSchoolDetailsUpdate = True
        self.user.currentlySelectedSchool.save()

        self.user.currentlySelectedSchool = None
        self.user.save()

        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 200)

class Base_Tests_Staff_redirectsMiddleware(Base_Tests_redirectsMiddleware):
    def testRedirectAdminChangelog(self):
        self.user.adminChangelogVersionShown = 0
        self.user.save()

        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('users:adminChangelog'))

    def testUpdate_adminChangelogVersionShown(self):
        self.user.adminChangelogVersionShown = 0
        self.user.save()
        self.assertNotEqual(self.user.adminChangelogVersionShown, self.user.ADMIN_CHANGELOG_CURRENT_VERSION)

        response = self.client.get(reverse('events:dashboard'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.adminChangelogVersionShown, self.user.ADMIN_CHANGELOG_CURRENT_VERSION)

class Test_redirectsMiddleware_coordinator(Base_Tests_Staff_redirectsMiddleware, TestCase):
    def setUp(self):
        self.login = self.client.login(request=HttpRequest(), username=self.email_user_state1_fullcoordinator, password=self.password)
        self.user = self.user_state1_fullcoordinator

    def test_redirect_not_association_member(self):
        self.user_state1_fullcoordinator_association_member.delete()
        self.user.refresh_from_db()
        self.assertRaises(AssociationMember.DoesNotExist, lambda: self.user.associationmember)

        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('association:membership'))

    def test_redirect_association_member_no_rulesAcceptedDate(self):
        self.user_state1_fullcoordinator_association_member.rulesAcceptedDate = None
        self.user_state1_fullcoordinator_association_member.save()

        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('association:membership'))

class Test_redirectsMiddleware_superuser(Base_Tests_Staff_redirectsMiddleware, TestCase):
    def setUp(self):
        self.login = self.client.login(request=HttpRequest(), username=self.email_user_state1_super1, password=self.password)
        self.user = self.user_state1_super1

    def test_no_redirect_not_association_member(self):
        self.user_state1_super1_association_member.delete()
        self.user.refresh_from_db()
        self.assertRaises(AssociationMember.DoesNotExist, lambda: self.user.associationmember)

        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_no_redirect_association_member_no_rulesAcceptedDate(self):
        self.user_state1_super1_association_member.rulesAcceptedDate = None
        self.user_state1_super1_association_member.save()

        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 200)
