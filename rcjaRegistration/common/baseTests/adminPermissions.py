from django.http import HttpRequest
from django.urls import reverse

from .populateDatabase import createStates, createUsers, createSchools

""" Status codes
Get
200 Success
302 Access denied - redirect to login page or home page
403 Access denied - don't have any permissions for object

POST
302 Success - redirect to list page or back to edit page if continue editing
200 Validation failure - page redisplayed, will contain error message
403 Access denied

GET: Add and delete pages
200 Success
302 Access denied - redirect to login page or home page
403 Access denied - have permission to view object but not add or delete
"""

GET_SUCCESS = 200
GET_DENIED = 302
GET_DENIED_ALL = 403
ADDDELETE_PAGE_DENIED_VIEWONLY = 403

POST_SUCCESS = 302
POST_VALIDATION_FAILURE = 200
POST_DENIED = 403

class Base:
    """Base for admin permissions tests for all user test cases"""

    @classmethod
    def additionalSetup(cls):
        """Hook for doing additional database setup"""
        pass

    @classmethod
    def updatePayload(cls):
        """Hook for updating valid payload with foreign foreign key ids"""
        pass

    # Runs once (per class) and uses transactions to refresh database between tests
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createSchools(cls)
        cls.additionalSetup()

        # IDs of objects for admin being tested
        # Should be from state 1, as coordinators from state 1 should have access to this object
        # For superuser and notstaff tests, an id is still required for the string reverse
        cls.state1ObjID = getattr(cls, cls.state1Obj).id

        # Should be from state 2, as coordinators from state 2 should not have access to this object
        # Ignored for superuser and notstaff tests
        cls.state2ObjID = getattr(cls, cls.state2Obj).id

        # Set the global object id if it is specified or None if not applicable - applicable tests only run if not none
        cls.globalObjID = getattr(cls, cls.globalObj).id if hasattr(cls, 'globalObj') else None

        cls.updatePayload()

    objectsToRefresh = []

    # Runs per test
    def setUp(self):
        for item in self.objectsToRefresh:
            getattr(self, item).refresh_from_db()

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

    def testGlobalChangeLoads(self):
        if self.globalObjID is not None:
            response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.globalObjID,)))
            self.assertEqual(response.status_code, self.globalChangeLoadsCode)

    # Delete

    def testDeleteLoads(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_delete', args=(self.state1ObjID,)))
        self.assertEqual(response.status_code, self.deleteLoadsCode)

class Base_Test_NotStaff(Base):
    """Test admin access with a user that has no admin/ staff permissions"""
    listLoadsCode = GET_DENIED
    changeLoadsCode = GET_DENIED
    globalChangeLoadsCode = GET_DENIED

    addLoadsCode = GET_DENIED
    deleteLoadsCode = GET_DENIED

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
        self.assertContains(response, f'{self.expectedListItems} {self.modelName}')

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
            self.assertContains(response, f'class="inline-heading">\n  \n    {expectedInline}\n  \n  </h2>')

    def testCorrectMissingAddInlines(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_add'))

        for expectedMissingInline in self.expectedMissingAddInlines:
            self.assertNotContains(response, expectedMissingInline)

    def testCorrectChangeInlines(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))

        for expectedInline in self.expectedChangeInlines:
            self.assertContains(response, f'class="inline-heading">\n  \n    {expectedInline}\n  \n  </h2>')

    def testCorrectMissingChangeInlines(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))

        for expectedMissingInline in self.expectedMissingChangeInlines:
            self.assertNotContains(response, expectedMissingInline)

    # Readonly fields
    expectedAddEditableFields = []
    expectedAddReadonlyFields = []
    expectedChangeEditableFields = []
    expectedChangeReadonlyFields = []
    expectedChangeMissingFields = []

    def checkReadonly(self, response, fields):
        for expectedField in fields:
            self.assertNotContains(response, f'id="id_{expectedField[0]}"')
            self.assertNotContains(response, f'name="{expectedField[0]}"')
            self.assertContains(response, f'<label>{expectedField[1]}:</label>')

    def checkEditable(self, response, fields):
        for expectedField in fields:
            self.assertContains(response, f'id="id_{expectedField[0]}"')
            self.assertContains(response, f'name="{expectedField[0]}"')
    
    def checkMissingFields(self, response, fields):
        for expectedField in fields:
            self.assertNotContains(response, f'id="id_{expectedField[0]}"')
            self.assertNotContains(response, f'name="{expectedField[0]}"')
            self.assertNotContains(response, f'<label>{expectedField[1]}:</label>')
            self.assertNotContains(response, f'id="id_{expectedField[0]}"')
            self.assertNotContains(response, f'name="{expectedField[0]}"')

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

    def testCorrectChangeMissingFields(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))
        self.checkMissingFields(response, self.expectedChangeMissingFields)

    # Post tests
    def testPostAdd(self):
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=self.validPayload)
        self.assertEqual(response.status_code, self.addPostCode)

    def testPostChange(self):
        response = self.client.post(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)), data=self.validPayload)
        self.assertEqual(response.status_code, self.changePostCode)

class Base_Test_SuperUser(DoesLoadBase):
    """Test admin access with a superuser"""
    listLoadsCode = GET_SUCCESS
    changeLoadsCode = GET_SUCCESS
    globalChangeLoadsCode = GET_SUCCESS

    addLoadsCode = GET_SUCCESS
    deleteLoadsCode = GET_SUCCESS

    addPostCode = POST_SUCCESS
    changePostCode = POST_SUCCESS

    def setUp(self):
        super().setUp()
        self.client.login(request=HttpRequest(), username=self.email_user_state1_super1, password=self.password)
        self.loggedInUser = self.user_state1_super1

class CoordinatorBase(DoesLoadBase):
    """Provides additional tests for coordinators"""
    wrongStateCode = GET_DENIED

    def testChangeDeniedOtherState(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state2ObjID,)))
        self.assertEqual(response.status_code, self.wrongStateCode)

    def testGlobalChangeEditable(self):
        if self.globalObjID is not None:
            response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.globalObjID,)))
            self.assertNotContains(response, 'Save')
            self.assertNotContains(response, 'Save and continue editing')
            self.assertContains(response, 'Close')

class Base_Test_FullCoordinator(CoordinatorBase):
    """Test admin access with a coordinator with full permisisons to state 1"""
    listLoadsCode = GET_SUCCESS
    changeLoadsCode = GET_SUCCESS
    globalChangeLoadsCode = GET_DENIED # Default to denied so access must be explicitly specified on tests for global objects

    addLoadsCode = GET_SUCCESS
    deleteLoadsCode = GET_SUCCESS

    addPostCode = POST_SUCCESS
    changePostCode = POST_SUCCESS

    def setUp(self):
        super().setUp()
        self.client.login(request=HttpRequest(), username=self.email_user_state1_fullcoordinator, password=self.password)
        self.loggedInUser = self.user_state1_fullcoordinator

    def testChangeEditable(self):
        if self.changePostCode == POST_SUCCESS:
            response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))
            self.assertContains(response, 'Save and continue editing')

class Base_Test_ViewCoordinator(CoordinatorBase):
    """Test admin access with a coordinator with view permisisons to state 1"""
    listLoadsCode = GET_SUCCESS
    changeLoadsCode = GET_SUCCESS
    globalChangeLoadsCode = GET_DENIED # Default to denied so access must be explicitly specified on tests for global objects

    addLoadsCode = ADDDELETE_PAGE_DENIED_VIEWONLY
    deleteLoadsCode = ADDDELETE_PAGE_DENIED_VIEWONLY

    addPostCode = POST_DENIED
    changePostCode = POST_DENIED

    def setUp(self):
        super().setUp()
        self.client.login(request=HttpRequest(), username=self.email_user_state1_viewcoordinator, password=self.password)
        self.loggedInUser = self.user_state1_viewcoordinator

    def testChangeReadOnly(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))
        self.assertNotContains(response, 'Save')
        self.assertNotContains(response, 'Save and continue editing')
        self.assertContains(response, 'Close')
