import unittest
from django.test import TestCase
from django.http import HttpRequest
from django.urls import reverse

from .populateDatabase import createStates, createUsers, createSchools

class Base:
    """Base for admin permissions tests for all user test cases"""
    def setUp(self):
        createStates(self)
        createUsers(self)
        createSchools(self)

        # IDs of objects for admin being tested
        # Should be from state 1, as coordinators from state 1 should have access to this object
        # For superuser and notstaff tests, an id is still required for the string reverse
        self.state1ObjID = getattr(self, self.state1Obj).id

        # Should be from state 2, as coordinators from state 2 should not have access to this object
        # Ignored for superuser and notstaff tests
        self.state2ObjID = getattr(self, self.state2Obj).id

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
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))
        self.assertEqual(response.status_code, self.changeLoadsCode)

    # Delete

    def testDeleteLoads(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_delete', args=(self.state1ObjID,)))
        self.assertEqual(response.status_code, self.deleteLoadsCode)

class Base_Test_NotStaff(Base):
    """Test admin access with a user that has no admin/ staff permissions"""
    listLoadsCode = 302
    changeLoadsCode = 302
    addLoadsCode = 302
    deleteLoadsCode = 302

    def setUp(self):
        super().setUp()
        self.client.login(request=HttpRequest(), username=self.email_user_notstaff, password=self.password)

    def testRedirectToLogin(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_changelist'))
        self.assertIn('/admin/login/', response.url)

class DoesLoadBase(Base):
    """Provides additional tests for users that have admin permisisons"""
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
    """Test admin access with a superuser"""
    listLoadsCode = 200
    changeLoadsCode = 200
    addLoadsCode = 200
    deleteLoadsCode = 200

    def setUp(self):
        super().setUp()
        self.client.login(request=HttpRequest(), username=self.email_user_state1_super1, password=self.password)

class CoordinatorBase(DoesLoadBase):
    """Provides additional tests for coordinators"""
    wrongStateCode = 302
    def testChangeDeniedOtherState(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state2ObjID,)))
        self.assertEqual(response.status_code, self.wrongStateCode)

class Base_Test_FullCoordinator(CoordinatorBase):
    """Test admin access with a coordinator with full permisisons to state 1"""
    listLoadsCode = 200
    changeLoadsCode = 200
    addLoadsCode = 200
    deleteLoadsCode = 200

    def setUp(self):
        super().setUp()
        self.client.login(request=HttpRequest(), username=self.email_user_state1_fullcoordinator, password=self.password)

    def testChangeEditable(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))
        self.assertContains(response, 'Save and continue editing')

class Base_Test_ViewCoordinator(CoordinatorBase):
    """Test admin access with a coordinator with view permisisons to state 1"""
    listLoadsCode = 200
    changeLoadsCode = 200
    addLoadsCode = 403
    deleteLoadsCode = 403

    def setUp(self):
        super().setUp()
        self.client.login(request=HttpRequest(), username=self.email_user_state1_viewcoordinator, password=self.password)

    def testChangeReadOnly(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))
        self.assertNotContains(response, 'Save')
        self.assertNotContains(response, 'Save and continue editing')
        self.assertContains(response, 'Close')

