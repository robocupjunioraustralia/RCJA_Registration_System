from django.test import TestCase
from django.urls import reverse
from django.http import HttpRequest
from django.core.exceptions import ValidationError

from users.models import User
from regions.models import State, Region
from association.models import AssociationMember

import datetime

def commonSetUp(self):
    self.state1 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='Victoria', abbreviation='VIC')
    self.region1 = Region.objects.create(name='Test Region', description='test desc')

    self.user1 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email1, password=self.password, homeState=self.state1, homeRegion=self.region1, first_name='Fake', last_name='Name', mobileNumber='0412 345 678')

    self.associationMember1 = AssociationMember.objects.create(user=self.user1, birthday=(datetime.datetime.now() + datetime.timedelta(days=-10)).date())

    self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

class TestAssociationMemberPage(TestCase):
    email1 = 'user1@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)

    def test_pageLoads_inactiveExistingMembership(self):
        response = self.client.get(reverse('association:membership'))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Membership status: Not a member')
        self.assertContains(response, 'To become a member of the Association please fill out the details below and click Join.')

    def test_pageLoads_activeExistingMembership(self):
        self.associationMember1.approvalStatus = 'approved'
        self.associationMember1.membershipStartDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date()
        self.associationMember1.save()
        response = self.client.get(reverse('association:membership'))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Membership status: Active')
        self.assertContains(response, 'You are currently a member.')
        self.assertContains(response, 'Update')

    def test_pageLoads_pendingExistingMembership(self):
        self.associationMember1.membershipStartDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date()
        self.associationMember1.save()
        response = self.client.get(reverse('association:membership'))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Membership status: Pending approval')
        self.assertContains(response, 'Your membership is pending approval.')
        self.assertContains(response, 'Update')

    def test_pageLoads_noExistingMembership(self):
        self.associationMember1.delete()
        response = self.client.get(reverse('association:membership'))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Membership status: Not a member')
        self.assertContains(response, 'To become a member of the Association please fill out the details below and click Join.')

    def test_pageLoads_expiredMembership(self):
        self.associationMember1.membershipStartDate = (datetime.datetime.now() + datetime.timedelta(days=-2)).date()
        self.associationMember1.membershipEndDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date()
        self.associationMember1.approvalStatus = 'approved'
        self.associationMember1.save()
        response = self.client.get(reverse('association:membership'))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Membership status: Expired')
        self.assertContains(response, 'Your membership is expired.')
        self.assertNotContains(response, 'Update')

    def test_postSuccess_noExistingMembership(self):
        self.associationMember1.delete()
        response = self.client.post(reverse('association:membership'), {
            'birthday': (datetime.datetime.now() + datetime.timedelta(days=-365*19)).date(),
            'address': 'Test address',
            'rulesAccepted': True,
        })
        self.assertEqual(302, response.status_code)
        self.assertEqual(AssociationMember.objects.count(), 1)
        self.assertEqual(AssociationMember.objects.first().user, self.user1)
        self.assertEqual(AssociationMember.objects.first().birthday, (datetime.datetime.now() + datetime.timedelta(days=-365*19)).date())
        self.assertEqual(AssociationMember.objects.first().address, 'Test address')
        self.assertEqual(AssociationMember.objects.first().membershipStartDate, datetime.datetime.now().date())

    def test_postSuccess_inactiveExistingMembership(self):
        self.assertIsNone(self.associationMember1.membershipStartDate)
        response = self.client.post(reverse('association:membership'), {
            'birthday': (datetime.datetime.now() + datetime.timedelta(days=-365*19)).date(),
            'address': 'Test address',
            'rulesAccepted': True,
        })
        self.assertEqual(302, response.status_code)
        self.assertEqual(AssociationMember.objects.count(), 1)
        self.associationMember1.refresh_from_db()
        self.assertEqual(self.associationMember1.membershipStartDate, datetime.datetime.now().date())

    def test_postSuccess_pendingExistingMembership(self):
        self.associationMember1.membershipStartDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date()
        self.associationMember1.save()
        response = self.client.post(reverse('association:membership'), {
            'birthday': (datetime.datetime.now() + datetime.timedelta(days=-365*19)).date(),
            'address': 'Test address',
            'rulesAccepted': True,
        })
        self.assertEqual(302, response.status_code)
        self.assertEqual(AssociationMember.objects.count(), 1)
        self.associationMember1.refresh_from_db()
        self.assertEqual(self.associationMember1.membershipStartDate, (datetime.datetime.now() + datetime.timedelta(days=-5)).date())
        self.assertEqual(self.associationMember1.birthday, (datetime.datetime.now() + datetime.timedelta(days=-365*19)).date())

    def test_postFail_noBirthday(self):
        response = self.client.post(reverse('association:membership'), {
            'address': 'Test address',
        })
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'This field is required.')

    def test_postFail_noAddress(self):
        response = self.client.post(reverse('association:membership'), {
            'birthday': (datetime.datetime.now() + datetime.timedelta(days=-365*19)).date(),
        })
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Address must not be blank for members 18 and over.')

    def test_postFail_under18Address(self):
        response = self.client.post(reverse('association:membership'), {
            'birthday': (datetime.datetime.now() + datetime.timedelta(days=-365*17)).date(),
            'address': 'Test address',
        })
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Address must be blank for members under 18.')

class TestAssociationMemberClean(TestCase):
    email1 = 'user1@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)

    def test_membershipEndDate_startDateNotBlank(self):
        self.associationMember1.membershipStartDate = None
        self.associationMember1.membershipEndDate = datetime.datetime.now().date()
        self.assertRaises(ValidationError, self.associationMember1.clean)

    def test_membershipEndDate_afterStartDate(self):
        self.associationMember1.membershipStartDate = datetime.datetime.now().date()
        self.associationMember1.membershipEndDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date()
        self.assertRaises(ValidationError, self.associationMember1.clean)

    def test_membershipEndDate_sameAsStartDate(self):
        self.associationMember1.membershipStartDate = datetime.datetime.now().date()
        self.associationMember1.membershipEndDate = datetime.datetime.now().date()
        self.assertRaises(ValidationError, self.associationMember1.clean)

    def test_membershipEndDate_valid(self):
        self.associationMember1.membershipStartDate = datetime.datetime.now().date()
        self.associationMember1.membershipEndDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
        self.assertIsNone(self.associationMember1.clean())

    def test_addressBlankIfUnder18(self):
        self.associationMember1.birthday = (datetime.datetime.now() + datetime.timedelta(days=-365*17)).date()
        self.associationMember1.address = 'Test address'
        self.assertRaises(ValidationError, self.associationMember1.clean)

    def test_addressNotBlankIfOver18(self):
        self.associationMember1.birthday = (datetime.datetime.now() + datetime.timedelta(days=-365*19)).date()
        self.associationMember1.address = ''
        self.assertRaises(ValidationError, self.associationMember1.clean)

    def test_approval_rulesAcceptedDate_blank(self):
        self.associationMember1.approvalStatus = 'approved'
        self.associationMember1.rulesAcceptedDate = None
        self.associationMember1.membershipStartDate = datetime.datetime.now().date()
        self.assertRaisesMessage(ValidationError, "Rules must be accepted before approval.", self.associationMember1.clean)

    def test_approval_membershipStartDate_blank(self):
        self.associationMember1.approvalStatus = 'approved'
        self.associationMember1.rulesAcceptedDate = datetime.datetime.now().date()
        self.associationMember1.membershipStartDate = None
        self.assertRaisesMessage(ValidationError, "Membership start date must be set before approval.", self.associationMember1.clean)
    
    def test_approval_both_blank(self):
        self.associationMember1.approvalStatus = 'approved'
        self.associationMember1.rulesAcceptedDate = None
        self.associationMember1.membershipStartDate = None
        self.assertRaisesMessage(ValidationError, "Membership start date must be set before approval. Rules must be accepted before approval.", self.associationMember1.clean)

    def test_approval_both_set(self):
        self.associationMember1.approvalStatus = 'approved'
        self.associationMember1.rulesAcceptedDate = datetime.datetime.now().date()
        self.associationMember1.membershipStartDate = datetime.datetime.now().date()
        self.assertIsNone(self.associationMember1.clean())

class TestAssociationMemberMethods(TestCase):
    email1 = 'user1@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)

    def test_getState(self):
        self.assertEqual(self.associationMember1.getState(), self.state1)

    def test_email(self):
        self.assertEqual(self.associationMember1.email(), self.email1)

    def test_homeRegion(self):
        self.assertEqual(self.associationMember1.homeRegion(), self.region1)

    def test_mobileNumber(self):
        self.assertEqual(self.associationMember1.mobileNumber(), '0412 345 678')

    def test_str(self):
        self.assertEqual(str(self.associationMember1), str(self.user1))

    def test_membershipExpired_endToday(self):
        self.associationMember1.membershipEndDate = datetime.datetime.now().date()
        self.assertTrue(self.associationMember1.membershipExpired())

    def test_membershipExpired_endTomorrow(self):
        self.associationMember1.membershipEndDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
        self.assertFalse(self.associationMember1.membershipExpired())

    def test_membershipActive_noStartDate(self):
        self.assertFalse(self.associationMember1.membershipActive())

    def test_membershipActive_startYesterday(self):
        self.associationMember1.membershipStartDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date()
        self.assertTrue(self.associationMember1.membershipActive())
    
    def test_membershipActive_startTomorrow(self):
        self.associationMember1.membershipStartDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
        self.assertFalse(self.associationMember1.membershipActive())

    def test_under18_noBirthday(self):
        self.associationMember1.birthday = None
        self.assertIsNone(self.associationMember1.under18())
    
    def test_under18_17(self):
        self.associationMember1.birthday = (datetime.datetime.now() + datetime.timedelta(days=-365*17)).date()
        self.assertTrue(self.associationMember1.under18())
    
    def test_under18_19(self):
        self.associationMember1.birthday = (datetime.datetime.now() + datetime.timedelta(days=-365*19)).date()
        self.assertFalse(self.associationMember1.under18())

    def test_membershipType_noBirthday(self):
        self.associationMember1.birthday = None
        self.assertEqual(self.associationMember1.membershipType(), 'Not a member')

    def test_membershipType_lifeMember(self):
        self.associationMember1.lifeMemberAwardedDate = datetime.datetime.now().date()
        self.assertEqual(self.associationMember1.membershipType(), 'Life member')

    def test_membershipType_17(self):
        self.associationMember1.birthday = (datetime.datetime.now() + datetime.timedelta(days=-365*17)).date()
        self.assertEqual(self.associationMember1.membershipType(), 'Associate')

    def test_membershipType_19(self):
        self.associationMember1.birthday = (datetime.datetime.now() + datetime.timedelta(days=-365*19)).date()
        self.assertEqual(self.associationMember1.membershipType(), 'Ordinary')

    def test_membershipStatus_active_futureEndDate(self):
        self.associationMember1.approvalStatus = 'approved'
        self.associationMember1.membershipStartDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date()
        self.associationMember1.membershipEndDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
        self.assertEqual(self.associationMember1.membershipStatus(), 'Active')

    def test_membershipStatus_active_noEndDate(self):
        self.associationMember1.approvalStatus = 'approved'
        self.associationMember1.membershipStartDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date()
        self.assertIsNone(self.associationMember1.membershipEndDate)
        self.assertEqual(self.associationMember1.membershipStatus(), 'Active')
    
    def test_membershipStatus_expired(self):
        self.associationMember1.approvalStatus = 'approved'
        self.associationMember1.membershipStartDate = (datetime.datetime.now() + datetime.timedelta(days=-2)).date()
        self.associationMember1.membershipEndDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date()
        self.assertEqual(self.associationMember1.membershipStatus(), 'Expired')

    def test_membershipStatus_notMember(self):
        self.assertIsNone(self.associationMember1.membershipStartDate)
        self.assertIsNone(self.associationMember1.membershipEndDate)
        self.assertEqual(self.associationMember1.membershipStatus(), 'Not a member')

    def test_membershipStatus_pending(self):
        self.associationMember1.membershipStartDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date()
        self.assertEqual(self.associationMember1.membershipStatus(), 'Pending approval')
