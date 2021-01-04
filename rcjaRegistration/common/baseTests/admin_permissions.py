import unittest
from django.test import TestCase
from django.http import HttpRequest
from django.urls import reverse

from .populateDatabase import createStates, createUsers, createSchools

class Base:
    def setUp(self):
        createStates(self)
        createUsers(self)
        createSchools(self)
        self.correctStateObjID = getattr(self, self.correctStateObjName).id
        self.wrongStateObjID = getattr(self, self.wrongStateObjName).id

    # Change list

    def testListLoads(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_changelist'))
        self.assertEqual(response.status_code, self.listLoadsCode)

    # Add

    def testAddLoads(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_add'))
        self.assertEqual(response.status_code, self.addLoadsCode)

    # Change

    def testChangeLoads(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.correctStateObjID,)))
        self.assertEqual(response.status_code, self.changeLoadsCode)

    # Delete

    def testDeleteLoads(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_delete', args=(self.correctStateObjID,)))
        self.assertEqual(response.status_code, self.deleteLoadsCode)

class Base_Test_NotStaff(Base):
    listLoadsCode = 302
    changeLoadsCode = 302
    addLoadsCode = 302
    deleteLoadsCode = 302

    def setUp(self):
        super().setUp()
        self.client.login(request=HttpRequest(), username=self.email_user_notstaff, password=self.password)

    def testRedirectToLogin(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_changelist'))
        self.assertIn(response.url, '/accounts/login/')

class DoesLoadBase(Base):
    def testListCorrectNumber(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_changelist'))
        self.assertContains(response, f'0 of {self.expectedListItems} selected')

    def testListCorrectContent(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_changelist'))
        for expectedString in self.expectedStrings:
            self.assertContains(response, expectedString)

        for expectedMissingString in self.expectedMissingStrings:
            self.assertNotContains(response, expectedMissingString)

class Base_Test_SuperUser(DoesLoadBase):
    listLoadsCode = 200
    changeLoadsCode = 200
    addLoadsCode = 200
    deleteLoadsCode = 200

    def setUp(self):
        super().setUp()
        self.client.login(request=HttpRequest(), username=self.email_user_state1_super1, password=self.password)

class CoordinatorBase(DoesLoadBase):
    wrongStateCode = 302
    def testChangeDeniedOtherState(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.wrongStateObjID,)))
        self.assertEqual(response.status_code, self.wrongStateCode)

class Base_Test_FullCoordinator(CoordinatorBase):
    listLoadsCode = 200
    changeLoadsCode = 200
    addLoadsCode = 200
    deleteLoadsCode = 200

    def setUp(self):
        super().setUp()
        self.client.login(request=HttpRequest(), username=self.email_user_state1_fullcoordinator, password=self.password)

    def testChangeEditable(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.correctStateObjID,)))
        self.assertContains(response, 'Save and continue editing')

class Base_Test_ViewCoordinator(CoordinatorBase):
    listLoadsCode = 200
    changeLoadsCode = 200
    addLoadsCode = 403
    deleteLoadsCode = 403

    def setUp(self):
        super().setUp()
        self.client.login(request=HttpRequest(), username=self.email_user_state1_viewcoordinator, password=self.password)

    def testChangeReadOnly(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.correctStateObjID,)))
        self.assertNotContains(response, 'Save')
        self.assertNotContains(response, 'Save and continue editing')
        self.assertContains(response, 'Close')


