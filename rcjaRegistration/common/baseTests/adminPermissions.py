from django.http import HttpRequest
from django.urls import reverse

from .populateDatabase import createStates, createUsers, createSchools

""" Status codes
Get
200 Success
302 Access denied - redirect to login page or home page

POST
302 Success - redirect to list page or back to edit page if continue editing
200 Validation failure - page redisplayed, will contain error message
403 Access denied

Add and delete pages
200 Success
302 Access denied - redirect to login page or home page
403 Access denied - have permission to view object but not add or delete
"""

class Base:
    """Base for admin permissions tests for all user test cases"""

    def additionalSetup(self):
        """Hook for doing additional database setup"""
        pass

    def updatePayload(self):
        """Hook for updating valid payload with foreign foreign key ids"""
        pass

    def setUp(self):
        createStates(self)
        createUsers(self)
        createSchools(self)
        self.additionalSetup()

        # IDs of objects for admin being tested
        # Should be from state 1, as coordinators from state 1 should have access to this object
        # For superuser and notstaff tests, an id is still required for the string reverse
        self.state1ObjID = getattr(self, self.state1Obj).id

        # Should be from state 2, as coordinators from state 2 should not have access to this object
        # Ignored for superuser and notstaff tests
        self.state2ObjID = getattr(self, self.state2Obj).id

        self.updatePayload()

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

    # Inlines
    expectedAddInlines = []
    expectedMissingAddInlines = []
    expectedChangeInlines = []
    expectedMissingChangeInlines = []

    def testCorrectAddInlines(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_add'))

        for expectedInline in self.expectedAddInlines:
            self.assertContains(response, f'<h2>{expectedInline}</h2>')

    def testCorrectMissingAddInlines(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_add'))

        for expectedMissingInline in self.expectedMissingAddInlines:
            self.assertNotContains(response, expectedMissingInline)

    def testCorrectChangeInlines(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))

        for expectedInline in self.expectedChangeInlines:
            self.assertContains(response, f'<h2>{expectedInline}</h2>')

    def testCorrectMissingChangeInlines(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))

        for expectedMissingInline in self.expectedMissingChangeInlines:
            self.assertNotContains(response, expectedMissingInline)

    # Readonly fields
    expectedAddEditableFields = []
    expectedAddReadonlyFields = []
    expectedChangeEditableFields = []
    expectedChangeReadonlyFields = []

    def checkReadonly(self, response, fields):
        for expectedField in fields:
            self.assertNotContains(response, f'id="id_{expectedField[0]}"')
            self.assertNotContains(response, f'name="{expectedField[0]}"')
            self.assertContains(response, f'<label>{expectedField[1]}:</label>')

    def checkEditable(self, response, fields):
        for expectedField in fields:
            self.assertContains(response, f'id="id_{expectedField[0]}"')
            self.assertContains(response, f'name="{expectedField[0]}"')

    def testCorrectAddEditableFields(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_add'))
        self.checkEditable(response, self.expectedAddEditableFields)

    def testCorrectAddReadonlyFields(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_add'))
        self.checkReadonly(response, self.expectedAddReadonlyFields)

    def testCorrectChangeEditableFields(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))
        self.checkEditable(response, self.expectedChangeEditableFields)

    def testCorrectChangeReadonlyFields(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))
        self.checkReadonly(response, self.expectedChangeReadonlyFields)

    # Post tests
    def testPostAdd(self):
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=self.validPayload)
        self.assertEqual(response.status_code, self.addPostCode)

    def testPostChange(self):
        response = self.client.post(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)), data=self.validPayload)
        self.assertEqual(response.status_code, self.changePostCode)

class Base_Test_SuperUser(DoesLoadBase):
    """Test admin access with a superuser"""
    listLoadsCode = 200
    changeLoadsCode = 200
    addLoadsCode = 200
    deleteLoadsCode = 200
    addPostCode = 302
    changePostCode = 302

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
    addPostCode = 302
    changePostCode = 302

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
    addPostCode = 403
    changePostCode = 403

    def setUp(self):
        super().setUp()
        self.client.login(request=HttpRequest(), username=self.email_user_state1_viewcoordinator, password=self.password)

    def testChangeReadOnly(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))
        self.assertNotContains(response, 'Save')
        self.assertNotContains(response, 'Save and continue editing')
        self.assertContains(response, 'Close')
