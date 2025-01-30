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
        'approvalStatus':'pending',
        'membershipStartDate': datetime.date.today(),
    }

    @classmethod
    def additionalSetup(cls):
        createAssociationMemberships(cls)

    @classmethod
    def updatePayload(cls):
        cls.validPayload['user'] = cls.user_state1_school2_mentor3.id

class Test_AssociationMember_NotStaff(AssociationMember_Base, Base_Test_NotStaff, TestCase):
    pass

class AdditionalAssociationMemberTestsMixin:
    expectedAddEditableFields = [
        ('approvalStatus', 'Approval status'),
    ]
    expectedAddReadonlyFields = [
        ('approvalRejectionBy', 'Approved/ rejected by'),
        ('approvalRejectionDate', 'Approval/ rejection date'),
        ('rulesAcceptedDate', 'Rules accepted date'),
    ]
    expectedChangeEditableFields = [
        ('approvalStatus', 'Approval status'),
    ]
    expectedChangeReadonlyFields = [
        ('approvalRejectionBy', 'Approved/ rejected by'),
        ('approvalRejectionDate', 'Approval/ rejection date'),
        ('rulesAcceptedDate', 'Rules accepted date'),
    ]

    def test_approvalStatus_approved_readonly(self):
        self.state1_associationMember1.approvalStatus = 'approved'
        self.state1_associationMember1.approvalRejectionDate = datetime.date.today()
        self.state1_associationMember1.save()
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))

        self.checkReadonly(response, [('approvalStatus', 'Approval status'),])

    def test_save_sets_approvalRejectionBy_not_already_set(self):
        payload = self.validPayload.copy()
        payload['approvalStatus'] = 'approved'

        self.assertIsNone(self.state1_associationMember1.approvalRejectionBy)

        response = self.client.post(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)), data=payload)
        self.assertEqual(response.status_code, POST_SUCCESS)
        self.state1_associationMember1.refresh_from_db()
        self.assertEqual(self.state1_associationMember1.approvalRejectionBy, self.loggedInUser)

    def test_save_does_not_set_approvalRejectionBy_already_set(self):
        payload = self.validPayload.copy()
        payload['approvalStatus'] = 'approved'
        self.state1_associationMember1.approvalRejectionBy = self.user_state2_super2
        self.state1_associationMember1.save()

        response = self.client.post(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)), data=payload)
        self.assertEqual(response.status_code, POST_SUCCESS)
        self.state1_associationMember1.refresh_from_db()
        self.assertEqual(self.state1_associationMember1.approvalRejectionBy, self.user_state2_super2)

    def test_save_does_not_set_approvalRejectionBy_not_approved(self):
        response = self.client.post(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)), data=self.validPayload)
        self.assertEqual(response.status_code, POST_SUCCESS)
        self.state1_associationMember1.refresh_from_db()
        self.assertIsNone(self.state1_associationMember1.approvalRejectionBy)
    
    def test_save_sets_approvalRejectionDate_not_already_set(self):
        payload = self.validPayload.copy()
        payload['approvalStatus'] = 'approved'

        self.assertIsNone(self.state1_associationMember1.approvalRejectionDate)

        response = self.client.post(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)), data=payload)
        self.assertEqual(response.status_code, POST_SUCCESS)
        self.state1_associationMember1.refresh_from_db()
        self.assertEqual(self.state1_associationMember1.approvalRejectionDate, datetime.date.today())

    def test_save_does_not_set_approvalRejectionDate_already_set(self):
        payload = self.validPayload.copy()
        payload['approvalStatus'] = 'approved'
        self.state1_associationMember1.approvalRejectionDate = datetime.date.today() + datetime.timedelta(days=-1)
        self.state1_associationMember1.save()

        response = self.client.post(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)), data=payload)
        self.assertEqual(response.status_code, POST_SUCCESS)
        self.state1_associationMember1.refresh_from_db()
        self.assertEqual(self.state1_associationMember1.approvalRejectionDate, datetime.date.today() + datetime.timedelta(days=-1))

    def test_save_does_not_set_approvalRejectionDate_not_approved(self):
        response = self.client.post(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)), data=self.validPayload)
        self.assertEqual(response.status_code, POST_SUCCESS)
        self.state1_associationMember1.refresh_from_db()
        self.assertIsNone(self.state1_associationMember1.approvalRejectionDate)

class Test_AssociationMember_SuperUser(AdditionalAssociationMemberTestsMixin, AssociationMember_Base, Base_Test_SuperUser, TestCase):
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
    def testChangeReadOnly(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))
        self.assertNotContains(response, 'Save')
        self.assertNotContains(response, 'Save and continue editing')
        self.assertContains(response, 'Close')

class Test_AssociationMember_GlobalFullCoordinator(AdditionalAssociationMemberTestsMixin, Test_AssociationMember_FullCoordinator):
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

    def testChangeReadOnly(self):
        pass

class Test_AssociationMember_ViewCoordinator(AssociationMember_Coordinators_Base, Base_Test_ViewCoordinator, TestCase):
    pass
