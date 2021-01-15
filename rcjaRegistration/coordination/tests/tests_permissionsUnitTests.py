from django.test import TestCase
from unittest.mock import patch
from common.baseTests import createStates, createUsers
from coordination.permissions import checkCoordinatorPermission

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

class Test_checkCoordinatorPermission(TestCase):
    def setUp(self):
        createStates(self)
        createUsers(self)

        self.request = RequestObj()
        self.stateObj = ModelTestState(self.state1)
        self.stateGlobalPermsObj = ModelTestStateGlobalPermissions(self.state1)
        self.globalObj = ModelTestGlobal()

        self.email_user_globalCoordinator = 'user11@user.com'

        self.user_globalCoordinator = User.objects.create_user(email=self.email_user_globalCoordinator, password=self.password, homeState=self.state1)
        self.globalCoordinator = Coordinator.objects.create(user=self.user_globalCoordinator, state=None, permissionLevel='full')
    
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
        self.request.user = self.user_state1_fullcoordinator
        self.coord_state1_fullcoordinator.state = self.state2
        self.coord_state1_fullcoordinator.save()

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
