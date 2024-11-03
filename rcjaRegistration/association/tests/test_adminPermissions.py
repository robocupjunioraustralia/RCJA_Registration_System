from common.baseTests import Base_Test_NotStaff, Base_Test_SuperUser, Base_Test_FullCoordinator, Base_Test_ViewCoordinator, createAssociationMemberships, POST_VALIDATION_FAILURE, GET_SUCCESS, POST_SUCCESS, ADDDELETE_PAGE_DENIED_VIEWONLY, POST_DENIED

from django.test import TestCase
from django.urls import reverse

import datetime

# AssociationMember

class AssociationMember_Base:
    modelName = 'Association Member'
    modelURLName = 'association_associationmember'
    state1Obj = 'state1_associationMember1'
    state2Obj = 'state2_associationMember3'
    validPayload = {
        'birthday': (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        'user': 0,
    }

    @classmethod
    def additionalSetup(cls):
        createAssociationMemberships(cls)

    @classmethod
    def updatePayload(cls):
        cls.validPayload['user'] = cls.user_state1_school2_mentor3.id

class Test_AssociationMember_NotStaff(AssociationMember_Base, Base_Test_NotStaff, TestCase):
    pass

class Test_AssociationMember_SuperUser(AssociationMember_Base, Base_Test_SuperUser, TestCase):
    expectedListItems = 3
    expectedStrings = [
        'user6@user.com',
        'user7@user.com',
        'user9@user.com',
    ]
    expectedMissingStrings = []

class AssociationMember_Coordinators_Base(AssociationMember_Base):
    addLoadsCode = ADDDELETE_PAGE_DENIED_VIEWONLY
    deleteLoadsCode = ADDDELETE_PAGE_DENIED_VIEWONLY

    addPostCode = POST_DENIED
    changePostCode = POST_DENIED

    expectedListItems = 2
    expectedStrings = [
        'user6@user.com',
        'user7@user.com',
    ]
    expectedMissingStrings = [
        'user9@user.com',
    ]

class Test_AssociationMember_FullCoordinator(AssociationMember_Coordinators_Base, Base_Test_FullCoordinator, TestCase):
    def testChangeEditable(self):
        pass

    def testChangeReadOnly(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))
        self.assertNotContains(response, 'Save')
        self.assertNotContains(response, 'Save and continue editing')
        self.assertContains(response, 'Close')


class Test_AssociationMember_GlobalFullCoordinator(Test_AssociationMember_FullCoordinator):
    addLoadsCode = GET_SUCCESS
    deleteLoadsCode = GET_SUCCESS

    addPostCode = POST_SUCCESS
    changePostCode = POST_SUCCESS

    wrongStateCode = GET_SUCCESS
    expectedListItems = 3
    expectedStrings = [
        'user6@user.com',
        'user7@user.com',
        'user9@user.com',
    ]
    expectedMissingStrings = []

    @classmethod
    def additionalSetup(cls):
        super().additionalSetup()
        cls.coord_state1_fullcoordinator.state = None
        cls.coord_state1_fullcoordinator.save()

    def testChangeEditable(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))
        self.assertContains(response, 'Save and continue editing')

    def testChangeReadOnly(self):
        pass

class Test_AssociationMember_ViewCoordinator(AssociationMember_Coordinators_Base, Base_Test_ViewCoordinator, TestCase):
    pass
