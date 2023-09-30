from common.baseTests import Base_Test_NotStaff, Base_Test_SuperUser, Base_Test_FullCoordinator, Base_Test_ViewCoordinator, ADDDELETE_PAGE_DENIED_VIEWONLY, POST_DENIED, GET_SUCCESS, POST_SUCCESS, POST_VALIDATION_FAILURE

from django.test import TestCase
from django.urls import reverse

from regions.models import State
from coordination.models import Coordinator

# State

class State_Base:
    modelName = 'State'
    modelURLName = 'regions_state'
    state1Obj = 'state1'
    state2Obj = 'state2'
    validPayload = {
        'name': 'New State',
        'abbreviation': 'new',
        'coordinator_set-TOTAL_FORMS': 0,
        'coordinator_set-INITIAL_FORMS': 0,
        'coordinator_set-MIN_NUM_FORMS': 0,
        'coordinator_set-MAX_NUM_FORMS': 1000,
    }

class Test_State_NotStaff(State_Base, Base_Test_NotStaff, TestCase):
    pass

class Test_State_SuperUser(State_Base, Base_Test_SuperUser, TestCase):
    expectedListItems = 2
    expectedStrings = [
        'State 1',
        'State 2',
    ]
    expectedMissingStrings = []

    # Inlines

    expectedAddInlines = []
    expectedMissingAddInlines = [
        'Coordinators',
    ]
    expectedChangeInlines = [
        'Coordinators',
    ]
    expectedMissingChangeInlines = []

    # Readonly fields

    expectedAddEditableFields = [
        ('typeCompetition', 'Competition'),
        ('typeUserRegistration', 'User registration'),
        ('typeGlobal', 'Global'),
        ('typeWebsite', 'Website'),
    ]
    expectedAddReadonlyFields = []
    expectedChangeEditableFields = [
        ('typeGlobal', 'Global'),
        ('typeWebsite', 'Website'),
    ]
    expectedChangeReadonlyFields = [
        ('typeCompetition', 'Competition'), # Existing states are typeCompetition=True and typeUserRegistration=True
        ('typeUserRegistration', 'User registration'),
    ]

    # Additional readonly field tests

    def testCorrectReadonlyFields_changeNotUserRegistration_NotCompetition(self):
        self.state3 = State.objects.create(name='State 3', abbreviation='ST3')

        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state3.id,)))

        self.checkEditable(response, [
            ('typeCompetition', 'Competition'),
            ('typeUserRegistration', 'User registration'),
            ('typeGlobal', 'Global'),
            ('typeWebsite', 'Website'),
        ])

    def testCorrectReadonlyFields_changeNotUserRegistration_Competition(self):
        self.state3 = State.objects.create(name='State 3', abbreviation='ST3', typeCompetition=True)

        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state3.id,)))

        self.checkEditable(response, [
            ('typeUserRegistration', 'User registration'),
            ('typeGlobal', 'Global'),
            ('typeWebsite', 'Website'),
        ])
        self.checkReadonly(response, [
            ('typeCompetition', 'Competition'),
        ])

    def testCorrectReadonlyFields_changeUserRegistration_NotCompetition(self):
        self.state3 = State.objects.create(name='State 3', abbreviation='ST3', typeUserRegistration=True)

        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state3.id,)))

        self.checkEditable(response, [
            ('typeCompetition', 'Competition'),
            ('typeGlobal', 'Global'),
            ('typeWebsite', 'Website'),
        ])
        self.checkReadonly(response, [
            ('typeUserRegistration', 'User registration'),
        ])

    def testCorrectReadonlyFields_changeGlobal(self):
        self.state3 = State.objects.create(name='State 3', abbreviation='ST3', typeGlobal=True)

        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state3.id,)))

        self.checkReadonly(response, [
        ])
        self.checkEditable(response, [
            ('typeCompetition', 'Competition'),
            ('typeUserRegistration', 'User registration'),
            ('typeGlobal', 'Global'),
            ('typeWebsite', 'Website'),
        ])

    def testCorrectReadonlyFields_changeOtherGlobal(self):
        self.state3 = State.objects.create(name='State 3', abbreviation='ST3')
        self.state4 = State.objects.create(name='State 4', abbreviation='ST4', typeGlobal=True)

        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state3.id,)))

        self.checkReadonly(response, [
            ('typeGlobal', 'Global'),
        ])
        self.checkEditable(response, [
            ('typeCompetition', 'Competition'),
            ('typeUserRegistration', 'User registration'),
            ('typeWebsite', 'Website'),
        ])

class State_Coordinators_Base(State_Base):
    expectedListItems = 1
    expectedStrings = [
        'State 1',
    ]
    expectedMissingStrings = [
        'State 2',
    ]

class Test_State_FullCoordinator(State_Coordinators_Base, Base_Test_FullCoordinator, TestCase):
    addLoadsCode = ADDDELETE_PAGE_DENIED_VIEWONLY
    deleteLoadsCode = ADDDELETE_PAGE_DENIED_VIEWONLY
    addPostCode = POST_DENIED

    # Inlines

    expectedChangeInlines = [
        'Coordinators',
    ]
    expectedMissingChangeInlines = []

    # Readonly fields

    expectedChangeReadonlyFields = [
        ('typeCompetition', 'Competition'),
        ('typeUserRegistration', 'User registration'),
        ('typeGlobal', 'Global'),
        ('typeWebsite', 'Website'),
    ]

    # Additional readonly field tests

    def testCorrectReadonlyFields_changeNotRegistration(self):
        self.state3 = State.objects.create(name='State 3', abbreviation='ST3')
        Coordinator.objects.create(user=self.user_state1_fullcoordinator, state=self.state3, permissionLevel='full', position='Text')

        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state3.id,)))

        self.checkReadonly(response, [
            ('typeCompetition', 'Competition'),
            ('typeUserRegistration', 'User registration'),
            ('typeGlobal', 'Global'),
            ('typeWebsite', 'Website'),
        ])

    def testCorrectReadonlyFields_changeGlobal(self):
        self.state3 = State.objects.create(name='State 3', abbreviation='ST3', typeGlobal=True)
        Coordinator.objects.create(user=self.user_state1_fullcoordinator, state=self.state3, permissionLevel='full', position='Text')

        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state3.id,)))

        self.checkReadonly(response, [
            ('typeCompetition', 'Competition'),
            ('typeUserRegistration', 'User registration'),
            ('typeGlobal', 'Global'),
            ('typeWebsite', 'Website'),
        ])

    def testCorrectReadonlyFields_changeOtherGlobal(self):
        self.state3 = State.objects.create(name='State 3', abbreviation='ST3')
        self.state4 = State.objects.create(name='State 4', abbreviation='ST4', typeGlobal=True)
        Coordinator.objects.create(user=self.user_state1_fullcoordinator, state=self.state3, permissionLevel='full', position='Text')

        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state3.id,)))

        self.checkReadonly(response, [
            ('typeCompetition', 'Competition'),
            ('typeUserRegistration', 'User registration'),
            ('typeGlobal', 'Global'),
            ('typeWebsite', 'Website'),
        ])

class Test_State_ViewCoordinator(State_Coordinators_Base, Base_Test_ViewCoordinator, TestCase):

    # Inlines

    expectedChangeInlines = []
    expectedMissingChangeInlines = [
        'Coordinators',
    ]

    # Readonly fields

    expectedChangeReadonlyFields = [
        ('typeCompetition', 'Competition'),
        ('typeUserRegistration', 'User registration'),
        ('typeGlobal', 'Global'),
        ('typeWebsite', 'Website'),
    ]

# Region

class Region_Base:
    modelName = 'Region'
    modelURLName = 'regions_region'
    state1Obj = 'region2_state1'
    state2Obj = 'region3_state2'
    globalObj = 'region1'
    validPayload = {
        'name': 'New Region',
        'state': 0,
    }

    @classmethod
    def updatePayload(cls):
        cls.validPayload['state'] = cls.state1.id

class Test_Region_NotStaff(Region_Base, Base_Test_NotStaff, TestCase):
    pass

class Test_Region_SuperUser(Region_Base, Base_Test_SuperUser, TestCase):
    expectedListItems = 3
    expectedStrings = [
        'Region 1',
        'Region 2',
        'Region 3',
    ]
    expectedMissingStrings = []

    def testPostAddBlankState(self):
        payload = self.validPayload.copy()
        del payload['state']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, POST_SUCCESS)

class Region_Coordinators_Base(Region_Base):
    globalChangeLoadsCode = GET_SUCCESS
    expectedListItems = 2
    expectedStrings = [
        'Region 1',
        'Region 2',
    ]
    expectedMissingStrings = [
        'Region 3',
    ]

class Test_Region_FullCoordinator(Region_Coordinators_Base, Base_Test_FullCoordinator, TestCase):
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

class Test_Region_GlobalFullCoordinator(Test_Region_FullCoordinator):
    wrongStateCode = GET_SUCCESS
    expectedListItems = 3
    expectedStrings = [
        'Region 1',
        'Region 2',
        'Region 3',
    ]
    expectedMissingStrings = []

    @classmethod
    def additionalSetup(cls):
        super().additionalSetup()
        cls.coord_state1_fullcoordinator.state = None
        cls.coord_state1_fullcoordinator.save()

    def testPostAddBlankState(self):
        payload = self.validPayload.copy()
        del payload['state']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, POST_SUCCESS)

    def testPostAddWrongState(self):
        payload = self.validPayload.copy()
        payload['state'] = self.state2.id
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, POST_SUCCESS)

    def testGlobalChangeEditable(self):
        if self.globalObjID is not None:
            response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.globalObjID,)))
            self.assertContains(response, 'Save and continue editing')

class Test_Region_ViewCoordinator(Region_Coordinators_Base, Base_Test_ViewCoordinator, TestCase):
    pass
