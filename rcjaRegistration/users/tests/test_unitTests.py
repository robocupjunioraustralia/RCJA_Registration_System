from django.test import TestCase
from django.core.exceptions import ValidationError
from unittest.mock import patch, Mock

from users.models import User
from schools.models import School, SchoolAdministrator
from regions.models import State, Region
from coordination.models import Coordinator

from users.forms import UserForm, UserSignupForm

class TestUserManager(TestCase):
    def setUp(self):
        # Use create (instead of create_user) here beause not setting password and testing the user object and manager
        self.user1 = User.objects.create(email='test@test.com')

    def test_get_by_natural_key_exact(self):
        self.assertEqual(User.objects.get_by_natural_key('test@test.com'), self.user1)

    def test_get_by_natural_key_differentCase(self):
        self.assertEqual(User.objects.get_by_natural_key('TEST@test.com'), self.user1)

    def test_get_by_natural_key_DoesNotExist(self):
        self.assertRaises(User.DoesNotExist, lambda : User.objects.get_by_natural_key('not@test.com'))

def unitTestsSetup(self):
    self.state1 = State.objects.create(typeRegistration=True, name='Victoria', abbreviation='VIC')
    self.region1 = Region.objects.create(name='Region 1')

    # Use create (instead of create_user) here beause not setting password and testing the user object and manager
    self.user1 = User.objects.create(email='test@test.com', first_name="First", last_name="Last", homeState=self.state1)
    self.school1 = School.objects.create(name='School 1', abbreviation='SCH1', state=self.state1, region=self.region1)

class TestUserModelMethods(TestCase):
    def setUp(self):
        unitTestsSetup(self)

    def test_getState(self):
        self.assertEqual(self.user1.getState(), self.state1)

    def test_clean_differentEmail(self):
        user2 = User(email='not@test.com')
        user2.clean()

    def test_clean_sameEmail(self):
        user2 = User(email='test@test.com')
        self.assertRaises(ValidationError, user2.clean)

    def test_clean_emailDifferentCase(self):
        user2 = User(email='TEST@test.com')
        self.assertRaises(ValidationError, user2.clean)
    
    def test_setPassword(self):
        user2 = User(email='TEST@test.com', forcePasswordChange=True)
        self.assertEqual(user2.forcePasswordChange, True)

        user2.set_password('pass')

        self.assertEqual(user2.forcePasswordChange, False)

    def test_setCurrentlySelectedSchool_schoolAdminExists(self):
        self.assertEqual(self.user1.currentlySelectedSchool, None)
        SchoolAdministrator.objects.create(school=self.school1, user=self.user1)
        self.assertEqual(self.user1.currentlySelectedSchool, self.school1)

    def test_setCurrentlySelectedSchool_schoolAdminDoesNotExist(self):
        self.user1.currentlySelectedSchool = self.school1
        self.assertEqual(self.user1.currentlySelectedSchool, self.school1)

        self.user1.setCurrentlySelectedSchool()
        self.assertEqual(self.user1.currentlySelectedSchool, None)

    def test_fullname_or_email_namePresent(self):
        self.assertEqual(self.user1.fullname_or_email(), "First Last")

    def test_fullname_or_email_nameNotPresent(self):
        user2 = User(email='not@test.com')
        self.assertEqual(user2.fullname_or_email(), "not@test.com")

    def test_str_namePresent(self):
        self.assertEqual(str(self.user1), "First Last (test@test.com)")

    def test_str_nameNotPresent(self):
        user2 = User(email='not@test.com')
        self.assertEqual(str(user2), "not@test.com")

class TestUpdateUserPermissions(TestCase):
    def setUp(self):
        unitTestsSetup(self)

    def testNotStaff(self):
        self.user1.is_staff = True
        self.assertTrue(self.user1.is_staff)

        self.user1.updateUserPermissions()

        self.assertFalse(self.user1.is_staff)

    def testStaffSuperuser(self):
        self.user1.is_superuser = True
        self.assertFalse(self.user1.is_staff)

        self.user1.updateUserPermissions()

        self.assertTrue(self.user1.is_staff)

    def testStaffCoordinator(self):
        self.assertFalse(self.user1.is_staff)
        Coordinator.objects.create(user=self.user1, state=self.state1, permissionLevel='full', position='Position') # Calls update user permissions

        self.assertTrue(self.user1.is_staff)

    def testNotCoordiantorNoPermissions(self):
        self.assertFalse(self.user1.user_permissions.exists())
        self.user1.updateUserPermissions()

        self.assertFalse(self.user1.user_permissions.exists())

    def testCoordiantorPermissions(self):
        self.assertFalse(self.user1.user_permissions.exists())
        Coordinator.objects.create(user=self.user1, state=self.state1, permissionLevel='full', position='Position') # Calls update user permissions

        self.assertTrue(self.user1.user_permissions.exists())

    def testCoordinatorRemovedClearsPermisisons(self):
        self.coord1 = Coordinator.objects.create(user=self.user1, state=self.state1, permissionLevel='full', position='Position') # Calls update user permissions

        self.assertTrue(self.user1.user_permissions.exists())
        self.assertTrue(self.user1.is_staff)

        self.coord1.delete()

        self.assertFalse(self.user1.user_permissions.exists())
        self.assertFalse(self.user1.is_staff)

    def testCorrectPermissionsAddedFullState(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissionLevel='full', position='Position') # Calls update user permissions

        self.assertTrue(self.user1.user_permissions.filter(codename__contains='view').exists())
        self.assertTrue(self.user1.user_permissions.filter(codename__contains='add').exists())
        self.assertTrue(self.user1.user_permissions.filter(codename__contains='change').exists())
        self.assertTrue(self.user1.user_permissions.filter(codename__contains='delete').exists())

    def testCorrectPermissionsAddedViewallState(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissionLevel='viewall', position='Position') # Calls update user permissions

        self.assertTrue(self.user1.user_permissions.filter(codename__contains='view').exists())
        self.assertFalse(self.user1.user_permissions.filter(codename__contains='add').exists())
        self.assertFalse(self.user1.user_permissions.filter(codename__contains='change').exists())
        self.assertFalse(self.user1.user_permissions.filter(codename__contains='delete').exists())

    def testCorrectPermissionsAddedFullGlobal(self):
        Coordinator.objects.create(user=self.user1, state=None, permissionLevel='full', position='Position') # Calls update user permissions

        self.assertTrue(self.user1.user_permissions.filter(codename__contains='view').exists())
        self.assertTrue(self.user1.user_permissions.filter(codename__contains='add').exists())
        self.assertTrue(self.user1.user_permissions.filter(codename__contains='change').exists())
        self.assertTrue(self.user1.user_permissions.filter(codename__contains='delete').exists())

    def testCorrectPermissionsAddedViewallGlobal(self):
        Coordinator.objects.create(user=self.user1, state=None, permissionLevel='viewall', position='Position') # Calls update user permissions

        self.assertTrue(self.user1.user_permissions.filter(codename__contains='view').exists())
        self.assertFalse(self.user1.user_permissions.filter(codename__contains='add').exists())
        self.assertFalse(self.user1.user_permissions.filter(codename__contains='change').exists())
        self.assertFalse(self.user1.user_permissions.filter(codename__contains='delete').exists())

    def testCorrectPermissionsAddedBillingmanager(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissionLevel='billingmanager', position='Position') # Calls update user permissions

        self.assertTrue(self.user1.user_permissions.filter(codename__contains='school').exists())
        self.assertTrue(self.user1.user_permissions.filter(codename__contains='schooladministrator').exists())
        self.assertTrue(self.user1.user_permissions.filter(codename__contains='campus').exists())
        self.assertTrue(self.user1.user_permissions.filter(codename__contains='invoice').exists())
        self.assertTrue(self.user1.user_permissions.filter(codename__contains='event').exists())

    def testCorrectPermissionsAddedSchoolmanager(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissionLevel='schoolmanager', position='Position') # Calls update user permissions

        self.assertTrue(self.user1.user_permissions.filter(codename__contains='school').exists())
        self.assertTrue(self.user1.user_permissions.filter(codename__contains='schooladministrator').exists())
        self.assertTrue(self.user1.user_permissions.filter(codename__contains='campus').exists())
        self.assertFalse(self.user1.user_permissions.filter(codename__contains='invoice').exists())
        self.assertFalse(self.user1.user_permissions.filter(codename__contains='event').exists())

class TestUserForm(TestCase):
    validPayload = {
        'first_name': 'First',
        'last_name': 'Last',
        'email': 'not@test.com',
        'mobileNumber': '12345',
        'homeState': 0,
        'homeRegion': 0,
    }

    def setUp(self):
        unitTestsSetup(self)
        self.validPayload['homeState'] = self.state1.id
        self.validPayload['homeRegion'] = self.region1.id

    def createForm(self, data):
        return UserForm(data=data)

    def testValid(self):
        form = self.createForm(self.validPayload)

        self.assertTrue(form.is_valid())

    def testFieldsRequired(self):
        form = self.createForm({})

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["first_name"], ["This field is required."])
        self.assertEqual(form.errors["last_name"], ["This field is required."])
        self.assertEqual(form.errors["email"], ["This field is required."])
        self.assertEqual(form.errors["mobileNumber"], ["This field is required."])
        self.assertEqual(form.errors["homeState"], ["This field is required."])
        self.assertEqual(form.errors["homeRegion"], ["This field is required."])

    def testEmailExists(self):
        payload = self.validPayload.copy()
        payload['email'] = 'test@test.com'
        form = self.createForm(payload)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["email"], ["User with this email address already exists."])

    def testEmailDifferentCaseExists(self):
        payload = self.validPayload.copy()
        payload['email'] = 'TEST@test.com'
        form = self.createForm(payload)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["email"], ["User with this email address already exists."])

class TestUserSignupForm(TestUserForm):
    validPayload = {
        'first_name': 'First',
        'last_name': 'Last',
        'email': 'not@test.com',
        'mobileNumber': '12345',
        'homeState': 0,
        'homeRegion': 0,
        'password': 'pass',
        'passwordConfirm': 'pass',
    }

    def createForm(self, data):
        return UserSignupForm(data=data)

    def testPasswordRequired(self):
        payload = self.validPayload.copy()
        del payload['password']
        del payload['passwordConfirm']
        form = self.createForm(payload)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.non_field_errors(), ["Password must not be blank"])

    def testPasswordNotSame(self):
        payload = self.validPayload.copy()
        payload['passwordConfirm'] = 'pass2'
        form = self.createForm(payload)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.non_field_errors(), ["Passwords do not match"])

    @patch('users.forms.validate_password', side_effect = Mock(side_effect=ValidationError('Password too short')))
    def testPasswordNotValid(self, mocked_validate_password):
        form = self.createForm(self.validPayload)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.non_field_errors(), ["Password too short"])
