from django.test import TestCase
from unittest.mock import patch
from common.baseTests import createStates, createUsers
from coordination.permissions import checkCoordinatorPermission, checkCoordinatorPermissionLevel, getFilteringPermissionLevels

from users.models import User
from coordination.models import Coordinator

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

    def testAllowedSuperuser(self):
        self.request.user = self.user_state1_super1

        self.assertTrue(checkCoordinatorPermission(self.request, ModelTestState, self.stateObj, 'change'))

    def testDeniedInactiveSuperuser(self):
        self.user_state1_super1.is_active = False
        self.user_state1_super1.save()
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
    def testAllowedStateCoordinator_noStateObjView(self, mock_codename, mock_has_perms):
        self.request.user = self.user_state1_fullcoordinator

        @classmethod
        def statePerms(cls, level):
            return []
        
        ModelTestState.stateCoordinatorPermissions = statePerms
        self.stateObj.state = None

        self.assertTrue(checkCoordinatorPermission(self.request, ModelTestState, self.stateObj, 'view'))

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
    def testAllowedStateCoordinator_globalObjView(self, mock_codename, mock_has_perms):
        self.request.user = self.user_state1_fullcoordinator

        @classmethod
        def statePerms(cls, level):
            return []
        
        ModelTestGlobal.stateCoordinatorPermissions = statePerms
        self.stateObj.state = None

        self.assertTrue(checkCoordinatorPermission(self.request, ModelTestGlobal, self.globalObj, 'view'))

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

    def testAllowedSuperuser(self):
        self.request.user = self.user_state1_super1

        self.assertTrue(checkCoordinatorPermissionLevel(self.request, self.stateObj, ['full']))

    def testDeniedInactiveSuperuser(self):
        self.user_state1_super1.is_active = False
        self.user_state1_super1.save()
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
