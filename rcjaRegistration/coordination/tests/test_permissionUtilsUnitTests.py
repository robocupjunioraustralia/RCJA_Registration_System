from django.test import TestCase
from unittest.mock import patch
from common.baseTests import createStates, createUsers, createEvents
from coordination.permissions import coordinatorFilterQueryset, checkCoordinatorPermission, checkCoordinatorPermissionLevel, getFilteringPermissionLevels
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied

from users.models import User
from coordination.models import Coordinator
from events.models import Event

class RequestObj:
    def __init__(self):
        pass

class BaseModelTest:
    def __init__(self):
        pass

    class _meta:
        model_name = 'testmodelonly'
        app_label = 'testapponly'

class ModelTestState(BaseModelTest):
    def __init__(self, state):
        self.state = state

    def getState(self):
        return self.state

class ModelTestStateGlobalPermissions(BaseModelTest):
    def __init__(self, state):
        self.state = state

    def getState(self):
        return self.state

class ModelTestGlobal(BaseModelTest):
    pass

class ModelTestGlobalStateViewGlobal(BaseModelTest):
    stateCoordinatorViewGlobal = True

def commonSetUp(self):
    createStates(self)
    createUsers(self)

    self.request = RequestObj()
    self.stateObj = ModelTestState(self.state1)
    self.stateGlobalPermsObj = ModelTestStateGlobalPermissions(self.state1)
    self.globalObj = ModelTestGlobal()

    self.email_user_globalCoordinator = 'user11@user.com'

    self.user_globalCoordinator = User.objects.create_user(email=self.email_user_globalCoordinator, password=self.password, homeState=self.state1)
    self.globalCoordinator = Coordinator.objects.create(user=self.user_globalCoordinator, state=None, permissionLevel='full')

class Test_checkCoordinatorPermission(TestCase):
    def setUp(self):
        commonSetUp(self)

    def testDeniedNoUser(self):
        self.request.user = None

        self.assertFalse(checkCoordinatorPermission(self.request, ModelTestState, self.stateObj, 'change'))

    def testDeniedNotAuthenticated(self):
        self.request.user = AnonymousUser()

        self.assertFalse(checkCoordinatorPermission(self.request, ModelTestState, self.stateObj, 'change'))

    def testAllowedSuperuser(self):
        self.request.user = self.user_state1_super1

        self.assertTrue(checkCoordinatorPermission(self.request, ModelTestState, self.stateObj, 'change'))

    def testDeniedInactiveSuperuser(self):
        self.user_state1_super1.is_active = False
        self.request.user = self.user_state1_super1

        self.assertFalse(checkCoordinatorPermission(self.request, ModelTestState, self.stateObj, 'change'))

    def testDeniedNotStaffSuperuser(self):
        self.user_state1_super1.is_staff = False
        self.request.user = self.user_state1_super1

        self.assertFalse(checkCoordinatorPermission(self.request, ModelTestState, self.stateObj, 'change'))

    @patch('django.contrib.auth.get_permission_codename', return_value='')
    @patch('django.contrib.auth.models.PermissionsMixin.has_perm', return_value=True)
    def testAllowedGlobalFullCoordinator_statePermissions(self, mock_codename, mock_has_perms):
        self.request.user = self.user_globalCoordinator

        @classmethod
        def statePerms(cls, level):
            return ['change']
        
        ModelTestState.stateCoordinatorPermissions = statePerms

        self.assertTrue(checkCoordinatorPermission(self.request, ModelTestState, self.stateObj, 'change'))

    @patch('django.contrib.auth.get_permission_codename', return_value='')
    @patch('django.contrib.auth.models.PermissionsMixin.has_perm', return_value=True)
    def testDeniedGlobalFullCoordinator_statePermissions(self, mock_codename, mock_has_perms):
        self.request.user = self.user_globalCoordinator

        @classmethod
        def statePerms(cls, level):
            return ['view']
        
        ModelTestState.stateCoordinatorPermissions = statePerms

        self.assertFalse(checkCoordinatorPermission(self.request, ModelTestState, self.stateObj, 'change'))

    @patch('django.contrib.auth.get_permission_codename', return_value='')
    @patch('django.contrib.auth.models.PermissionsMixin.has_perm', return_value=True)
    def testAllowedGlobalFullCoordinator_globalPermissions(self, mock_codename, mock_has_perms):
        self.request.user = self.user_globalCoordinator

        @classmethod
        def statePerms(cls, level):
            return ['view']
        
        ModelTestStateGlobalPermissions.stateCoordinatorPermissions = statePerms

        @classmethod
        def globalPerms(cls, level):
            return ['change']
        
        ModelTestStateGlobalPermissions.globalCoordinatorPermissions = globalPerms

        self.assertTrue(checkCoordinatorPermission(self.request, ModelTestStateGlobalPermissions, self.stateGlobalPermsObj, 'change'))

    @patch('django.contrib.auth.get_permission_codename', return_value='')
    @patch('django.contrib.auth.models.PermissionsMixin.has_perm', return_value=True)
    def testDeniedGlobalFullCoordinator_globalPermissions(self, mock_codename, mock_has_perms):
        self.request.user = self.user_globalCoordinator

        @classmethod
        def statePerms(cls, level):
            return ['view']
        
        ModelTestStateGlobalPermissions.stateCoordinatorPermissions = statePerms

        @classmethod
        def globalPerms(cls, level):
            return ['view']
        
        ModelTestStateGlobalPermissions.globalCoordinatorPermissions = globalPerms

        self.assertFalse(checkCoordinatorPermission(self.request, ModelTestStateGlobalPermissions, self.stateGlobalPermsObj, 'change'))

    @patch('django.contrib.auth.get_permission_codename', return_value='')
    @patch('django.contrib.auth.models.PermissionsMixin.has_perm', return_value=True)
    def testAllowedStateCoordinator(self, mock_codename, mock_has_perms):
        self.request.user = self.user_state1_fullcoordinator

        @classmethod
        def statePerms(cls, level):
            return ['change']
        
        ModelTestState.stateCoordinatorPermissions = statePerms

        self.assertTrue(checkCoordinatorPermission(self.request, ModelTestState, self.stateObj, 'change'))

    @patch('django.contrib.auth.get_permission_codename', return_value='')
    @patch('django.contrib.auth.models.PermissionsMixin.has_perm', return_value=True)
    def testDeniedStateCoordinator_wrongPerm(self, mock_codename, mock_has_perms):
        self.request.user = self.user_state1_fullcoordinator

        @classmethod
        def statePerms(cls, level):
            return ['view']
        
        ModelTestState.stateCoordinatorPermissions = statePerms

        self.assertFalse(checkCoordinatorPermission(self.request, ModelTestState, self.stateObj, 'change'))

    @patch('django.contrib.auth.get_permission_codename', return_value='')
    @patch('django.contrib.auth.models.PermissionsMixin.has_perm', return_value=True)
    def testDeniedStateCoordinator_wrongState(self, mock_codename, mock_has_perms):
        self.request.user = self.user_state2_fullcoordinator

        @classmethod
        def statePerms(cls, level):
            return ['change']
        
        ModelTestState.stateCoordinatorPermissions = statePerms

        self.assertFalse(checkCoordinatorPermission(self.request, ModelTestState, self.stateObj, 'change'))

    @patch('django.contrib.auth.get_permission_codename', return_value='')
    @patch('django.contrib.auth.models.PermissionsMixin.has_perm', return_value=True)
    def testAllowedStateCoordinator_NoneObj(self, mock_codename, mock_has_perms):
        self.request.user = self.user_state1_fullcoordinator

        @classmethod
        def statePerms(cls, level):
            return []
        
        ModelTestState.stateCoordinatorPermissions = statePerms

        self.assertTrue(checkCoordinatorPermission(self.request, ModelTestState, None, 'change'))

    @patch('django.contrib.auth.get_permission_codename', return_value='')
    @patch('django.contrib.auth.models.PermissionsMixin.has_perm', return_value=True)
    def testDeniedStateCoordinator_noStateObjView(self, mock_codename, mock_has_perms):
        self.request.user = self.user_state1_fullcoordinator

        @classmethod
        def statePerms(cls, level):
            return []

        ModelTestState.stateCoordinatorPermissions = statePerms
        self.stateObj.state = None

        self.assertFalse(checkCoordinatorPermission(self.request, ModelTestState, self.stateObj, 'view'))

    @patch('django.contrib.auth.get_permission_codename', return_value='')
    @patch('django.contrib.auth.models.PermissionsMixin.has_perm', return_value=True)
    def testAllowedStateCoordinator_noStateObjViewStateViewGlobal(self, mock_codename, mock_has_perms):
        self.request.user = self.user_state1_fullcoordinator

        @classmethod
        def statePerms(cls, level):
            return []

        ModelTestGlobalStateViewGlobal.stateCoordinatorPermissions = statePerms
        self.stateObj.state = None

        self.assertTrue(checkCoordinatorPermission(self.request, ModelTestGlobalStateViewGlobal, self.stateObj, 'view'))

    @patch('django.contrib.auth.get_permission_codename', return_value='')
    @patch('django.contrib.auth.models.PermissionsMixin.has_perm', return_value=True)
    def testDeniedStateCoordinator_noStateObjChange(self, mock_codename, mock_has_perms):
        self.request.user = self.user_state1_fullcoordinator

        @classmethod
        def statePerms(cls, level):
            return []
        
        ModelTestState.stateCoordinatorPermissions = statePerms
        self.stateObj.state = None

        self.assertFalse(checkCoordinatorPermission(self.request, ModelTestState, self.stateObj, 'change'))

    @patch('django.contrib.auth.get_permission_codename', return_value='')
    @patch('django.contrib.auth.models.PermissionsMixin.has_perm', return_value=True)
    def testDeniedStateCoordinator_globalObjView(self, mock_codename, mock_has_perms):
        self.request.user = self.user_state1_fullcoordinator

        @classmethod
        def statePerms(cls, level):
            return []

        ModelTestGlobal.stateCoordinatorPermissions = statePerms

        self.assertFalse(checkCoordinatorPermission(self.request, ModelTestGlobal, self.globalObj, 'view'))

    @patch('django.contrib.auth.get_permission_codename', return_value='')
    @patch('django.contrib.auth.models.PermissionsMixin.has_perm', return_value=True)
    def testAllowedStateCoordinator_globalObjViewStateViewGlobal(self, mock_codename, mock_has_perms):
        self.request.user = self.user_state1_fullcoordinator

        @classmethod
        def statePerms(cls, level):
            return []

        ModelTestGlobalStateViewGlobal.stateCoordinatorPermissions = statePerms

        self.assertTrue(checkCoordinatorPermission(self.request, ModelTestGlobalStateViewGlobal, self.globalObj, 'view'))

    @patch('django.contrib.auth.get_permission_codename', return_value='')
    @patch('django.contrib.auth.models.PermissionsMixin.has_perm', return_value=True)
    def testDeniedStateCoordinator_globalObjChange(self, mock_codename, mock_has_perms):
        self.request.user = self.user_state1_fullcoordinator

        @classmethod
        def statePerms(cls, level):
            return []
        
        ModelTestGlobal.stateCoordinatorPermissions = statePerms
        self.stateObj.state = None

        self.assertFalse(checkCoordinatorPermission(self.request, ModelTestGlobal, self.globalObj, 'change'))

class Test_checkCoordinatorPermissionLevel(TestCase):
    def setUp(self):
        commonSetUp(self)

    def testDeniedNoUser(self):
        self.request.user = None

        self.assertFalse(checkCoordinatorPermissionLevel(self.request, self.stateObj, ['full']))

    def testDeniedNotAuthenticated(self):
        self.request.user = AnonymousUser()

        self.assertFalse(checkCoordinatorPermissionLevel(self.request, self.stateObj, ['full']))

    def testAllowedSuperuser(self):
        self.request.user = self.user_state1_super1

        self.assertTrue(checkCoordinatorPermissionLevel(self.request, self.stateObj, ['full']))

    def testDeniedInactiveSuperuser(self):
        self.user_state1_super1.is_active = False
        self.request.user = self.user_state1_super1

        self.assertFalse(checkCoordinatorPermissionLevel(self.request, self.stateObj, ['full']))

    def testDeniedNotStaffSuperuser(self):
        self.user_state1_super1.is_staff = False
        self.request.user = self.user_state1_super1

        self.assertFalse(checkCoordinatorPermissionLevel(self.request, self.stateObj, ['full']))

    def testDeniedNoneObj(self):
        self.request.user = self.user_state1_fullcoordinator

        self.assertFalse(checkCoordinatorPermissionLevel(self.request, None, ['full']))

    def testDeniedNoGetState(self):
        self.request.user = self.user_state1_fullcoordinator

        self.assertFalse(checkCoordinatorPermissionLevel(self.request, self.globalObj, ['full']))

    def testAllowedStateCoordinator(self):
        self.request.user = self.user_state1_fullcoordinator

        self.assertTrue(checkCoordinatorPermissionLevel(self.request, self.stateObj, ['full']))

    def testDeniedStateCoordinator_wrongLevel(self):
        self.request.user = self.user_state1_fullcoordinator

        self.assertFalse(checkCoordinatorPermissionLevel(self.request, self.stateObj, ['other']))

    def testDeniedStateCoordinator_wrongState(self):
        self.request.user = self.user_state2_fullcoordinator

        self.assertFalse(checkCoordinatorPermissionLevel(self.request, self.stateObj, ['full']))

    def testDeniedStateCoordinator_globalObj(self):
        self.request.user = self.user_state1_fullcoordinator

        self.stateObj.state = None

        self.assertFalse(checkCoordinatorPermissionLevel(self.request, self.stateObj, ['full']))

    def testAllowedGlobalCoordinator(self):
        self.request.user = self.user_globalCoordinator

        self.assertTrue(checkCoordinatorPermissionLevel(self.request, self.stateObj, ['full']))

    def testDeniedGlobalCoordinator_wrongLevel(self):
        self.request.user = self.user_globalCoordinator

        self.assertFalse(checkCoordinatorPermissionLevel(self.request, self.stateObj, ['other']))

    def testAllowedGlobalCoordinator_globalObj(self):
        self.request.user = self.user_globalCoordinator

        self.stateObj.state = None

        self.assertTrue(checkCoordinatorPermissionLevel(self.request, self.stateObj, ['full']))

class Test_getFilteringPermissionLevels(TestCase):
    def testStatePermissionsOneLevel(self):
        @classmethod
        def statePerms(cls, level):
            if level in ['full']:
                return [
                    'add',
                    'view',
                    'change',
                    'delete'
                ]
            elif level in ['viewall', 'billingmanager']:
                return [
                    'view',
                ]
            return []
        
        ModelTestState.stateCoordinatorPermissions = statePerms

        statePermissionLevels, globalPermissionLevels = getFilteringPermissionLevels(ModelTestState, ['change'])
        self.assertEqual(['full'], statePermissionLevels)
        self.assertEqual(['full'], globalPermissionLevels)

    def testStatePermissionsTwoLevels(self):
        @classmethod
        def statePerms(cls, level):
            if level in ['full']:
                return [
                    'add',
                    'view',
                    'change',
                    'delete'
                ]
            elif level in ['viewall', 'billingmanager']:
                return [
                    'view',
                ]
            return []
        
        ModelTestState.stateCoordinatorPermissions = statePerms

        statePermissionLevels, globalPermissionLevels = getFilteringPermissionLevels(ModelTestState, ['view', 'change'])
        self.assertEqual(['viewall', 'billingmanager', 'full', 'full'], statePermissionLevels)
        self.assertEqual(['viewall', 'billingmanager', 'full', 'full'], globalPermissionLevels)

    def testStatePermissionsOverride(self):
        @classmethod
        def statePerms(cls, level):
            if level in ['full']:
                return [
                    'add',
                    'view',
                    'change',
                    'delete'
                ]
            elif level in ['viewall', 'billingmanager']:
                return [
                    'view',
                ]
            return []
        
        ModelTestState.stateCoordinatorPermissions = statePerms

        statePermissionLevels, globalPermissionLevels = getFilteringPermissionLevels(ModelTestState, ['view', 'change'], ['full'])
        self.assertEqual(['full'], statePermissionLevels)
        self.assertEqual(['full'], globalPermissionLevels)

    def testStatePermissionsEmptyOverride(self):
        @classmethod
        def statePerms(cls, level):
            if level in ['full']:
                return [
                    'add',
                    'view',
                    'change',
                    'delete'
                ]
            elif level in ['viewall', 'billingmanager']:
                return [
                    'view',
                ]
            return []
        
        ModelTestState.stateCoordinatorPermissions = statePerms

        statePermissionLevels, globalPermissionLevels = getFilteringPermissionLevels(ModelTestState, ['view', 'change'], [])
        self.assertEqual([], statePermissionLevels)
        self.assertEqual([], globalPermissionLevels)

    def testGlobalPermissions(self):
        @classmethod
        def statePerms(cls, level):
            if level in ['billingmanager']:
                return [
                    'view',
                    'change',
                ]
            return []
        
        ModelTestGlobal.stateCoordinatorPermissions = statePerms

        @classmethod
        def globalPerms(cls, level):
            if level in ['billingmanager']:
                return [
                    'add',
                    'view',
                    'change',
                    'delete'
                ]
            return []
        
        ModelTestGlobal.globalCoordinatorPermissions = globalPerms

        statePermissionLevels, globalPermissionLevels = getFilteringPermissionLevels(ModelTestGlobal, ['add'])
        self.assertEqual([], statePermissionLevels)
        self.assertEqual(['billingmanager'], globalPermissionLevels)

    def testGlobalPermissionsOverride(self):
        @classmethod
        def statePerms(cls, level):
            if level in ['billingmanager']:
                return [
                    'view',
                    'change',
                ]
            return []
        
        ModelTestGlobal.stateCoordinatorPermissions = statePerms

        @classmethod
        def globalPerms(cls, level):
            if level in ['billingmanager']:
                return [
                    'add',
                    'view',
                    'change',
                    'delete'
                ]
            return []
        
        ModelTestGlobal.globalCoordinatorPermissions = globalPerms

        statePermissionLevels, globalPermissionLevels = getFilteringPermissionLevels(ModelTestGlobal, ['add'], ['full', 'level2'])
        self.assertEqual(['full', 'level2'], statePermissionLevels)
        self.assertEqual(['full', 'level2'], globalPermissionLevels)

    def testGlobalPermissionsEmptyOverride(self):
        @classmethod
        def statePerms(cls, level):
            if level in ['billingmanager']:
                return [
                    'view',
                    'change',
                ]
            return []
        
        ModelTestGlobal.stateCoordinatorPermissions = statePerms

        @classmethod
        def globalPerms(cls, level):
            if level in ['billingmanager']:
                return [
                    'add',
                    'view',
                    'change',
                    'delete'
                ]
            return []
        
        ModelTestGlobal.globalCoordinatorPermissions = globalPerms

        statePermissionLevels, globalPermissionLevels = getFilteringPermissionLevels(ModelTestGlobal, ['add'], [])
        self.assertEqual([], statePermissionLevels)
        self.assertEqual([], globalPermissionLevels)

class Test_coordinatorFilterQueryset(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)

        cls.baseQS = User.objects.all()

    def setUp(self):
        self.request = RequestObj()

    def testSuperuser(self):
        self.user_state1_super1.refresh_from_db()
        self.request.user = self.user_state1_super1
        
        qs = coordinatorFilterQueryset(self.baseQS, self.request, ['full'], ['full'], 'homeState__coordinator', False)

        self.assertEqual(self.baseQS, qs)

    def testGlobalFull(self):
        self.coord_state1_fullcoordinator.state = None
        self.coord_state1_fullcoordinator.save()
        self.request.user = self.user_state1_fullcoordinator
        
        qs = coordinatorFilterQueryset(self.baseQS, self.request, ['full'], ['full'], 'homeState__coordinator', False)

        self.assertEqual(self.baseQS, qs)

    def testGlobalWronglevel(self):
        self.coord_state1_fullcoordinator.state = None
        self.coord_state1_fullcoordinator.save()
        self.request.user = self.user_state1_fullcoordinator
        
        qs = coordinatorFilterQueryset(self.baseQS, self.request, ['wrong'], ['wrong'], 'homeState__coordinator', False)

        self.assertFalse(qs.exists())

    def testNoUser(self):
        self.request.user = None

        self.assertRaises(PermissionDenied, lambda: coordinatorFilterQueryset(self.baseQS, self.request, ['full'], ['full'], 'homeState__coordinator', False))

    def testNotAuthenticated(self):
        self.request.user = AnonymousUser()

        self.assertRaises(PermissionDenied, lambda: coordinatorFilterQueryset(self.baseQS, self.request, ['full'], ['full'], 'homeState__coordinator', False))

    def testNoperms(self):
        self.request.user = self.user_notstaff
        self.user_notstaff.is_active = True
        self.user_notstaff.is_staff = True
        
        qs = coordinatorFilterQueryset(self.baseQS, self.request, ['full'], ['full'], 'homeState__coordinator', False)

        self.assertFalse(qs.exists())

    def testInactiveSuperuser(self):
        self.user_state1_super1.refresh_from_db()
        self.user_state1_super1.is_active = False
        self.request.user = self.user_state1_super1

        self.assertRaises(PermissionDenied, lambda: coordinatorFilterQueryset(self.baseQS, self.request, ['full'], ['full'], 'homeState__coordinator', False))

    def testNotStaffSuperuser(self):
        self.user_state1_super1.refresh_from_db()
        self.user_state1_super1.is_staff = False
        self.request.user = self.user_state1_super1

        self.assertRaises(PermissionDenied, lambda: coordinatorFilterQueryset(self.baseQS, self.request, ['full'], ['full'], 'homeState__coordinator', False))

    def testNoLookups(self):
        self.request.user = self.user_state1_fullcoordinator
        
        qs = coordinatorFilterQueryset(self.baseQS, self.request, ['full'], ['full'], False, False)

        self.assertQuerysetEqual(self.baseQS, qs, ordered=False)

    def testNoStateLookups(self):
        self.request.user = self.user_state1_fullcoordinator
        
        qs = coordinatorFilterQueryset(self.baseQS, self.request, ['full'], ['full'], False, 'homeState')

        self.assertQuerysetEqual(self.baseQS.filter(homeState=None), qs, ordered=False)

    def testCoordinatorNoGlobals(self):
        self.request.user = self.user_state1_fullcoordinator

        self.assertTrue(self.baseQS.filter(homeState=self.state2).exists())
        self.assertTrue(self.baseQS.filter(homeState=None).exists())
        qs = coordinatorFilterQueryset(self.baseQS, self.request, ['full'], ['full'], 'homeState__coordinator', False)

        self.assertEqual(7, qs.count())
        self.assertFalse(qs.filter(homeState=self.state2).exists())
        self.assertFalse(qs.filter(homeState=None).exists())

    def testCoordinatorGlobals(self):
        self.request.user = self.user_state1_fullcoordinator

        self.assertTrue(self.baseQS.filter(homeState=self.state2).exists())
        self.assertTrue(self.baseQS.filter(homeState=None).exists())
        qs = coordinatorFilterQueryset(self.baseQS, self.request, ['full'], ['full'], 'homeState__coordinator', 'homeState')

        self.assertEqual(8, qs.count())
        self.assertFalse(qs.filter(homeState=self.state2).exists())
        self.assertTrue(qs.filter(homeState=None).exists())

    def testCoordinatorMixedPermissions(self):
        createEvents(self)
        self.request.user = self.user_notstaff
        Coordinator.objects.create(user=self.user_notstaff, state=self.state1, permissionLevel='eventmanager', position='Position')
        Coordinator.objects.create(user=self.user_notstaff, state=self.state2, permissionLevel='schoolmanager', position='Position')

        baseqs = Event.objects.all()
        self.assertTrue(baseqs.filter(state=self.state2).exists())

        qs = coordinatorFilterQueryset(baseqs, self.request, ['eventmanager', 'viewall'], ['eventmanager', 'viewall'], 'state__coordinator', False)

        self.assertEqual(5, qs.count())
        self.assertFalse(qs.filter(state=self.state2).exists())
