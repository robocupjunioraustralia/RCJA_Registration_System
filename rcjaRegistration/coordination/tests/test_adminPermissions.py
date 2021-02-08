from common.baseTests import Base_Test_NotStaff, Base_Test_SuperUser, Base_Test_FullCoordinator, Base_Admin_Test

from django.test import TestCase
from django.urls import reverse
from django.http import HttpRequest

from regions.models import State
from coordination.models import Coordinator

# Coordinator

class Coordinator_Base:
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

class Test_Coordinator_NotStaff(Coordinator_Base, Base_Test_NotStaff, TestCase):
    pass

class Test_Coordinator_SuperUser(Coordinator_Base, Base_Test_SuperUser, TestCase):
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
        self.assertEqual(response.status_code, 302)

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

class Test_Coordinator_FullCoordinator(Coordinator_Coordinators_Base, Base_Test_FullCoordinator, TestCase):
    def testPostAddBlankState(self):
        payload = self.validPayload.copy()
        del payload['state']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'This field is required.')

    def testPostAddWrongState(self):
        payload = self.validPayload.copy()
        payload['state'] = self.state2.id
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

class Test_Coordinator_GlobalFullCoordinator(Test_Coordinator_FullCoordinator):
    wrongStateCode = 200
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
        cls.coord_state1_fullcoordinator.state = None
        cls.coord_state1_fullcoordinator.save()

    def testPostAddWrongState(self):
        payload = self.validPayload.copy()
        payload['state'] = self.state2.id
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, 302)

class Test_Coordinator_ViewCoordinator(Coordinator_Base, Base_Admin_Test, TestCase):
    listLoadsCode = 403
    changeLoadsCode = 403
    addLoadsCode = 403
    deleteLoadsCode = 403

    def setUp(self):
        super().setUp()
        self.client.login(request=HttpRequest(), username=self.email_user_state1_viewcoordinator, password=self.password)
