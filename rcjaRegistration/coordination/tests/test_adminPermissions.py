from common.baseTests import Base_Test_NotStaff, Base_Test_SuperUser, Base_Test_FullCoordinator, Base_Admin_Test, POST_VALIDATION_FAILURE, GET_DENIED_ALL, GET_SUCCESS, POST_SUCCESS

from django.test import TestCase
from django.urls import reverse
from django.http import HttpRequest

import datetime

from regions.models import State
from coordination.models import Coordinator
from association.models import AssociationMember

# Coordinator

class Coordinator_Base:
    modelName = 'Coordinator'
    modelURLName = 'coordination_coordinator'
    state1Obj = 'coord_state1_fullcoordinator'
    state2Obj = 'coord_state2_fullcoordinator'
    validPayload = {
        'user': 0,
        'state': 0,
        'permissionLevel': 'full',
        'position': 'Position',
    }

    @classmethod
    def updatePayload(cls):
        cls.validPayload['state'] = cls.state1.id
        cls.validPayload['user'] = cls.user_state1_school1_mentor1.id

    @classmethod
    def additionalSetup(cls):
        cls.user_state1_school1_mentor1_association_member = AssociationMember.objects.create(user=cls.user_state1_school1_mentor1, birthday=(datetime.datetime.now() + datetime.timedelta(days=-20*365)).date(), rulesAcceptedDate=datetime.datetime.now(), membershipStartDate=datetime.datetime.now())

class Test_Coordinator_NotStaff(Coordinator_Base, Base_Test_NotStaff, TestCase):
    pass

class AdditionalCoordinatorTestsMixin:
    def test_add_denied_no_association_membership(self):
        self.user_state1_school1_mentor1_association_member.delete()
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=self.validPayload)
        self.assertEqual(response.status_code, POST_VALIDATION_FAILURE)

    def test_change_allowed_no_association_membership(self):
        self.user_state1_school1_mentor1_association_member.delete()
        response = self.client.post(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)), data=self.validPayload)
        self.assertEqual(response.status_code, POST_SUCCESS)

    def test_add_denied_association_membership_rules_not_accepted(self):
        self.user_state1_school1_mentor1_association_member.rulesAcceptedDate = None
        self.user_state1_school1_mentor1_association_member.save()
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=self.validPayload)
        self.assertEqual(response.status_code, POST_VALIDATION_FAILURE)

    def test_change_allowed_association_membership_rules_not_accepted(self):
        self.user_state1_school1_mentor1_association_member.rulesAcceptedDate = None
        self.user_state1_school1_mentor1_association_member.save()
        response = self.client.post(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)), data=self.validPayload)
        self.assertEqual(response.status_code, POST_SUCCESS)

class Test_Coordinator_SuperUser(AdditionalCoordinatorTestsMixin, Coordinator_Base, Base_Test_SuperUser, TestCase):
    expectedListItems = 4
    expectedStrings = [
        'user2@user.com',
        'user3@user.com',
        'user4@user.com',
        'user5@user.com',
    ]
    expectedMissingStrings = []

    def testPostAddBlankState(self):
        payload = self.validPayload.copy()
        del payload['state']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, POST_SUCCESS)

class Coordinator_Coordinators_Base(Coordinator_Base):
    expectedListItems = 2
    expectedStrings = [
        'user2@user.com',
        'user3@user.com',
    ]
    expectedMissingStrings = [
        'user4@user.com',
        'user5@user.com',
    ]

class Test_Coordinator_FullCoordinator(AdditionalCoordinatorTestsMixin, Coordinator_Coordinators_Base, Base_Test_FullCoordinator, TestCase):
    def testPostAddBlankState(self):
        payload = self.validPayload.copy()
        del payload['state']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, POST_VALIDATION_FAILURE)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'This field is required.')

    def testPostAddWrongState(self):
        payload = self.validPayload.copy()
        payload['state'] = self.state2.id
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, POST_VALIDATION_FAILURE)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

class Test_Coordinator_GlobalFullCoordinator(Test_Coordinator_FullCoordinator):
    wrongStateCode = GET_SUCCESS
    expectedListItems = 4
    expectedStrings = [
        'user2@user.com',
        'user3@user.com',
        'user4@user.com',
        'user5@user.com',
    ]
    expectedMissingStrings = []

    @classmethod
    def additionalSetup(cls):
        super().additionalSetup()
        cls.coord_state1_fullcoordinator.state = None
        cls.coord_state1_fullcoordinator.save()

    def testPostAddWrongState(self):
        payload = self.validPayload.copy()
        payload['state'] = self.state2.id
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, POST_SUCCESS)

class Test_Coordinator_ViewCoordinator(Coordinator_Base, Base_Admin_Test, TestCase):
    listLoadsCode = GET_DENIED_ALL
    changeLoadsCode = GET_DENIED_ALL
    addLoadsCode = GET_DENIED_ALL
    deleteLoadsCode = GET_DENIED_ALL

    def setUp(self):
        super().setUp()
        self.client.login(request=HttpRequest(), username=self.email_user_state1_viewcoordinator, password=self.password)
