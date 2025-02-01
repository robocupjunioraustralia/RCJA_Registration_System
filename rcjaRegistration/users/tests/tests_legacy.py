from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, modify_settings
from django.urls import reverse
from django.test import Client
from django.http import HttpRequest
from django.core.exceptions import ValidationError
from unittest.mock import patch, Mock

import datetime

from users.models import User
from schools.models import School, SchoolAdministrator
from regions.models import State, Region
from coordination.models import Coordinator
from association.models import AssociationMember

@modify_settings(MIDDLEWARE={
    'remove': 'common.redirectsMiddleware.RedirectMiddleware',
})
class AuthViewTests(TestCase):
    email = 'user@user.com'
    password = 'chdj48958DJFHJGKDFNM'
    validPayload = {
        'email':email,
        'password':password,
        'passwordConfirm':password,
        'first_name':'test',
        'last_name':'test',
        'mobileNumber':'123123123',
        'homeState': 1,
        'homeRegion': 1,
        }

    def setUp(self):
        self.user = user = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email='admin@test.com', password='admin')
        self.newState = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='Victoria',abbreviation='VIC')
        self.newRegion = Region.objects.create(name='Test Region',description='test desc')
        self.newSchool = School.objects.create(name='Melbourne High',state=self.newState,region=self.newRegion)
        self.validPayload["homeState"] = self.newState.id
        self.validPayload["homeRegion"] = self.newRegion.id

    def testSignupByUrl(self):
        response = self.client.get('/accounts/signup')
        self.assertEqual(response.status_code, 200)

    def testSignupByName(self):
        response = self.client.get(reverse('users:signup'))
        self.assertEqual(response.status_code, 200)

    def testSignupUsesCorrectTemplate(self):
        response = self.client.get(reverse('users:signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/signup.html')

    def testUserValidSignup(self):
        prevUsers = get_user_model().objects.count()
        self.assertRaises(User.DoesNotExist, lambda: User.objects.get(email=self.email))

        payloadData = self.validPayload
        response = self.client.post(path=reverse('users:signup'),data = payloadData)
        self.assertEqual(response.status_code,302) #ensure user is redirected on signup
        self.assertEqual(get_user_model().objects.count(), prevUsers + 1)
        # this checks the user created has the right username
        User.objects.get(email=self.email)

    def testUserInvalidSignup(self):
        payloadData = {'username':self.email}
        response = self.client.post(path=reverse('users:signup'),data = payloadData)
        self.assertEqual(response.status_code,200) #ensure user is not redirected
        self.assertEqual(get_user_model().objects.count(), 1)
    
    def testUserExistingSignup(self):
        payloadData = self.validPayload
        self.client.post(path=reverse('users:signup'),data = payloadData)
        response = self.client.post(path=reverse('users:signup'), data = payloadData)
        self.assertEqual(response.status_code,200) #ensure failed signup
        self.assertContains(response, 'Email address: User with this email address already exists.')

    def testUserExistingSignupCaseInsensitive(self):
        payloadData = self.validPayload
        self.client.post(path=reverse('users:signup'),data = payloadData)
        payloadData['email'] = 'UsEr@user.com'
        response = self.client.post(path=reverse('users:signup'), data = payloadData)
        self.assertEqual(response.status_code,200) #ensure failed signup
        self.assertContains(response, 'Email address: User with this email address already exists.')
        payloadData['email'] = self.email # reset email for other tests

    def testUserInvalidPasswordConfirmSignup(self):
        payloadData = self.validPayload.copy()
        payloadData["passwordConfirm"] = 'asasdaasasa'
        response = self.client.post(path=reverse('users:signup'), data = payloadData)
        self.assertEqual(response.status_code,200) #ensure failed signup
        self.assertContains(response, 'Passwords do not match')

    def testLoginByUrl(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

    def testLoginByName(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def testLoginUsesCorrectTemplate(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def testUserCreatedLogsIn(self):
        payloadData = self.validPayload
        self.client.post(path=reverse('users:signup'),data = payloadData)
        loginPayload = {'username':self.email,'password':self.password}
        response = self.client.post(path=reverse('login'),data = loginPayload)
        self.assertEqual(response.status_code,302) #ensure a successful login works and redirects

    def testLogoutByUrl(self):
        response = self.client.post('/accounts/logout/')
        self.assertEqual(response.status_code, 200)

    def testLogoutByName(self):
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 200)

    def testLogoutUsesCorrectTemplate(self):
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/logged_out.html')

    def testUserCreatedLogsOut(self):
        user = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, 
            email=self.email,
            password=self.password
        )
        user.save()
        self.client.login(request=HttpRequest(), username=self.email, password=self.password)
        self.client.post(reverse('logout'))
        # Try an unauthorized page
        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 302)

class TestEditDetails(TestCase):
    email = 'user@user.com'
    password = 'chdj48958DJFHJGKDFNM'
    
    def setUp(self):
        self.validPayload = {
            'email':self.email,
            'password':self.password,
            'passwordConfirm':self.password,
            'first_name':'test',
            'last_name':'test',
            'mobileNumber':'123123123',
            'homeState': 1,
            'homeRegion': 1,
        }

        self.newState = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='Victoria',abbreviation='VIC')
        self.newRegion = Region.objects.create(name='Test Region',description='test desc')
        self.newSchool = School.objects.create(name='Melbourne High',state=self.newState,region=self.newRegion)
        self.validPayload["homeState"] = self.newState.id
        self.validPayload["homeRegion"] = self.newRegion.id

        self.user1 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email, password=self.password)

        self.client.login(request=HttpRequest(), username=self.email, password=self.password)

    def testPageLoads(self):
        response = self.client.get(path=reverse('users:details'))
        self.assertEqual(200,response.status_code)

    def testEditWorks(self):
        payload = {
            'questionresponse_set-TOTAL_FORMS':0,
            "questionresponse_set-INITIAL_FORMS":0,
            "questionresponse_set-MIN_NUM_FORMS":0,
            "questionresponse_set-MAX_NUM_FORMS":0,
            "first_name":"Admin",
            "last_name":"User",
            "mobileNumber":123,
            "email":"admon@admon.com",
            'homeState': self.newState.id,
            'homeRegion': self.newRegion.id,
        }
        response = self.client.post(path=reverse('users:details'),data=payload)
        self.assertEqual(302,response.status_code)
        self.assertEqual(response.url, reverse('events:dashboard'))
        self.assertEqual(User.objects.get(first_name="Admin").email,'admon@admon.com')

    def testEditWorks_continueEditing(self):
        payload = {
            'questionresponse_set-TOTAL_FORMS':0,
            "questionresponse_set-INITIAL_FORMS":0,
            "questionresponse_set-MIN_NUM_FORMS":0,
            "questionresponse_set-MAX_NUM_FORMS":0,
            "first_name":"Admin",
            "last_name":"User",
            "mobileNumber":123,
            "email":"admon@admon.com",
            'homeState': self.newState.id,
            'homeRegion': self.newRegion.id,
            'continue_editing': 'y',
        }
        response = self.client.post(path=reverse('users:details'),data=payload)
        self.assertEqual(302,response.status_code)
        self.assertEqual(response.url, reverse('users:details'))
        self.assertEqual(User.objects.get(first_name="Admin").email,'admon@admon.com')

    def testEditWorks_displayAgain(self):
        self.user1.forceDetailsUpdate = True
        self.user1.save()

        payload = {
            'questionresponse_set-TOTAL_FORMS':0,
            "questionresponse_set-INITIAL_FORMS":0,
            "questionresponse_set-MIN_NUM_FORMS":0,
            "questionresponse_set-MAX_NUM_FORMS":0,
            "first_name":"Admin",
            "last_name":"User",
            "mobileNumber":123,
            "email":"admon@admon.com",
            'homeState': self.newState.id,
            'homeRegion': self.newRegion.id,
        }
        response = self.client.post(path=reverse('users:details'),data=payload)
        self.assertEqual(302,response.status_code)
        self.assertEqual(response.url, reverse('users:details'))
        self.assertEqual(User.objects.get(first_name="Admin").email,'admon@admon.com')

    def testMissingManagementFormData(self):
        payload = {
            "first_name":"Admin",
            "last_name":"User",
            "mobileNumber":123,
            "email":"admon@admon.com",
            'homeState': self.newState.id,
            'homeRegion': self.newRegion.id,
        }
        response = self.client.post(path=reverse('users:details'),data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ManagementForm data is missing or has been tampered with')

    def testMissingManagementFormData_invalidForm(self):
        payload = {
            "first_name":"Admin",
            "last_name":"User",
            "mobileNumber":123,
            "email":"invalid",
            'homeState': self.newState.id,
            'homeRegion': self.newRegion.id,
        }
        response = self.client.post(path=reverse('users:details'),data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ManagementForm data is missing or has been tampered with')

    def testInvalidEditFails(self):
        payload = {
            'questionresponse_set-TOTAL_FORMS':0,
            "questionresponse_set-INITIAL_FORMS":0,
            "questionresponse_set-MIN_NUM_FORMS":0,
            "questionresponse_set-MAX_NUM_FORMS":0,
            "first_name":"Admin",
            "last_name":"User",
            "mobileNumber":123,
            "email":"adminNope",
        }
        response = self.client.post(path=reverse('users:details'),data=payload)
        self.assertEqual(200,response.status_code)

class TestUserSave(TestCase):
    email = 'user@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        self.user = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email, password=self.password)

        self.state1 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='Victoria', abbreviation='VIC')
        self.state2 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='New South Wales', abbreviation='NSW')
        self.region1 = Region.objects.create(name='Region 1')
        self.region2 = Region.objects.create(name='Region 2')

        self.school1 = School.objects.create(name='School 1')
        self.school2 = School.objects.create(name='School 2')

    def testSaveNoSchools(self):
        self.user.save()
    
    def testSaveNoState(self):
        SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)
        self.assertEqual(self.school1.state, None)
        self.assertEqual(self.school1.region, None)

        self.user.save()
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)
        self.assertEqual(self.school1.state, None)
        self.assertEqual(self.school1.region, None)

    def testSaveAddState(self):
        SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)
        self.assertEqual(self.school1.state, None)
        self.assertEqual(self.school1.region, None)

        self.user.homeState = self.state1
        self.user.save()
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)
        self.assertEqual(self.school1.state, self.state1)
        self.assertEqual(self.school1.region, None)

    def testSaveAddRegion(self):
        SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)
        self.assertEqual(self.school1.state, None)
        self.assertEqual(self.school1.region, None)

        self.user.homeRegion = self.region1
        self.user.save()
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)
        self.assertEqual(self.school1.state, None)
        self.assertEqual(self.school1.region, self.region1)

    def testSaveAddStateAndRegion(self):
        SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)
        self.assertEqual(self.school1.state, None)
        self.assertEqual(self.school1.region, None)

        self.user.homeState = self.state1
        self.user.homeRegion = self.region1
        self.user.save()
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)
        self.assertEqual(self.school1.state, self.state1)
        self.assertEqual(self.school1.region, self.region1)

    def testSaveNoState_SchoolExistingState(self):
        self.school1.state = self.state1
        self.school1.region = self.region1
        self.school1.save()

        SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)
        self.assertEqual(self.school1.state, self.state1)
        self.assertEqual(self.school1.region, self.region1)
        self.assertEqual(self.user.homeState, None)
        self.assertEqual(self.user.homeRegion, None)

        self.user.save()
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)
        self.assertEqual(self.school1.state, self.state1)
        self.assertEqual(self.school1.region, self.region1)
        self.assertEqual(self.user.homeState, None)
        self.assertEqual(self.user.homeRegion, None)

    def testSaveChange(self):
        self.school1.state = self.state1
        self.school1.region = self.region1
        self.school1.save()

        SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)
        self.assertEqual(self.school1.state, self.state1)
        self.assertEqual(self.school1.region, self.region1)
        self.assertEqual(self.user.homeState, None)
        self.assertEqual(self.user.homeRegion, None)

        self.user.homeState = self.state2
        self.user.homeRegion = self.region2
        self.user.save()
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)
        self.assertEqual(self.school1.state, self.state1)
        self.assertEqual(self.school1.region, self.region1)
        self.assertEqual(self.user.homeState, self.state2)
        self.assertEqual(self.user.homeRegion, self.region2)

class TestTermsAndConditionsView(TestCase):
    email = 'user@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        self.user = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email, password=self.password)

    def testPageLoads_loggedOut(self):
        response = self.client.get(path=reverse('users:termsAndConditions'))
        self.assertEqual(200,response.status_code)

    def testPageLoads_loggedIn(self):
        self.client.login(request=HttpRequest(), username=self.email,password=self.password)
        response = self.client.get(path=reverse('users:termsAndConditions'))
        self.assertEqual(200,response.status_code)

    def testCorrectTemplate_loggedOut(self):
        response = self.client.get(reverse('users:termsAndConditions'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'termsAndConditions/termsAndConditionsNoAuth.html')

    def testCorrectTemplate_loggedIn(self):
        self.client.login(request=HttpRequest(), username=self.email,password=self.password)
        response = self.client.get(reverse('users:termsAndConditions'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'termsAndConditions/termsAndConditionsLoggedIn.html')

def adminSetUp(self):
    self.user1 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email1, password=self.password)
    self.user1_association_member = AssociationMember.objects.create(user=self.user1, birthday=(datetime.datetime.now() + datetime.timedelta(days=-20*365)).date(), rulesAcceptedDate=datetime.datetime.now(), membershipStartDate=datetime.datetime.now())

    self.state1 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='Victoria', abbreviation='VIC')
    self.state2 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='South Australia', abbreviation='SA')

    self.user2 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email2, password=self.password, homeState=self.state2)
    self.user2_association_member = AssociationMember.objects.create(user=self.user2, birthday=(datetime.datetime.now() + datetime.timedelta(days=-20*365)).date(), rulesAcceptedDate=datetime.datetime.now(), membershipStartDate=datetime.datetime.now())

    self.user3 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email3, password=self.password, homeState=self.state1)
    self.user3_association_member = AssociationMember.objects.create(user=self.user3, birthday=(datetime.datetime.now() + datetime.timedelta(days=-20*365)).date(), rulesAcceptedDate=datetime.datetime.now(), membershipStartDate=datetime.datetime.now())

    self.usersuper = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.emailsuper, password=self.password, is_staff=True, is_superuser=True)

class TestUserAdmin(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    emailsuper = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        adminSetUp(self)
        self.coord1 = Coordinator.objects.create(user=self.user1, state=self.state1, permissionLevel='full', position='Thing')
        self.coord2 = Coordinator.objects.create(user=self.user2, state=self.state2, permissionLevel='full', position='Thing')

    def testUserListLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:users_user_changelist'))
        self.assertEqual(response.status_code, 200)

    def testUserChangeLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.user1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save')

    def testUserListContent_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:users_user_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.email3)
        self.assertContains(response, self.email2)

    def testUserDeleteLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:users_user_delete', args=(self.user1.id,)))
        self.assertEqual(response.status_code, 200)

    def testUserListNonStaff_denied(self):
        self.client.login(request=HttpRequest(), username=self.email3, password=self.password)
        response = self.client.get(reverse('admin:users_user_changelist'))
        self.assertEqual(response.status_code, 302)

    def testUserListLoads_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_changelist'))
        self.assertEqual(response.status_code, 200)

    def testUserListContent_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.email3)
        self.assertNotContains(response, self.email2)
        self.assertNotContains(response, self.emailsuper)

    def testUserChangeLoads_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.user3.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save')

    def testUserChangeDenied_wrongState_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.user2.id,)))
        self.assertEqual(response.status_code, 302)

    def testUserViewLoads_viewPermission_coordinator(self):
        self.coord1.permissionLevel = 'viewall'
        self.coord1.save()

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.user3.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Save')

    def testCoordinatorDeleteDenied_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_delete', args=(self.user3.id,)))
        self.assertEqual(response.status_code, 403)

    # Change Post

    def testChangePostAllowed_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'email': self.user3.email,
            'homeState': self.user3.homeState.id,
            'questionresponse_set-TOTAL_FORMS': 0,
            'questionresponse_set-INITIAL_FORMS': 0,
            'questionresponse_set-MIN_NUM_FORMS': 0,
            'questionresponse_set-MAX_NUM_FORMS': 0,
            'schooladministrator_set-TOTAL_FORMS': 0,
            'schooladministrator_set-INITIAL_FORMS': 0,
            'schooladministrator_set-MIN_NUM_FORMS': 0,
            'schooladministrator_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:users_user_change', args=(self.user3.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('admin:users_user_change', args=(self.user3.id,)), data=payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'was changed successfully')

    def testChangePostDenied_wrongState_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'email': self.user2.email,
            'homeState': self.user2.homeState.id,
            'questionresponse_set-TOTAL_FORMS': 0,
            'questionresponse_set-INITIAL_FORMS': 0,
            'questionresponse_set-MIN_NUM_FORMS': 0,
            'questionresponse_set-MAX_NUM_FORMS': 0,
            'schooladministrator_set-TOTAL_FORMS': 0,
            'schooladministrator_set-INITIAL_FORMS': 0,
            'schooladministrator_set-MIN_NUM_FORMS': 0,
            'schooladministrator_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:users_user_change', args=(self.user2.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('admin:users_user_change', args=(self.user2.id,)), data=payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'doesn’t exist. Perhaps it was deleted?')

    def testChangePostDenied_viewPermission_coordinator(self):
        self.coord1.permissionLevel = 'viewall'
        self.coord1.save()

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'email': self.user3.email,
            'homeState': self.user3.homeState.id,
            'questionresponse_set-TOTAL_FORMS': 0,
            'questionresponse_set-INITIAL_FORMS': 0,
            'questionresponse_set-MIN_NUM_FORMS': 0,
            'questionresponse_set-MAX_NUM_FORMS': 0,
            'schooladministrator_set-TOTAL_FORMS': 0,
            'schooladministrator_set-INITIAL_FORMS': 0,
            'schooladministrator_set-MIN_NUM_FORMS': 0,
            'schooladministrator_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:users_user_change', args=(self.user3.id,)), data=payload)
        self.assertEqual(response.status_code, 403)

    # Add post

    def testAddPostAllowed_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'email': 'new@new.com',
            'password1': 'sldjghfsdkjfbn38',
            'password2': 'sldjghfsdkjfbn38',
            'homeState': self.state1.id,
        }
        response = self.client.post(reverse('admin:users_user_add'), data=payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email='new@new.com').exists(), True)
        self.assertContains(response, 'was added successfully. You may edit it again below.')

    def testAddPostDenied_viewPermission_coordinator(self):
        self.coord1.permissionLevel = 'viewall'
        self.coord1.save()

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'email': 'new@new.com',
            'password1': 'sldjghfsdkjfbn38',
            'password2': 'sldjghfsdkjfbn38',
            'homeState': self.state1.id,
        }
        response = self.client.post(reverse('admin:users_user_add'), data=payload, follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(User.objects.filter(email='new@new.com').exists(), False)

    # User FK filtering

    # homeState field
    def testHomeStateFieldSuccess_change_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'email': self.user3.email,
            'homeState': self.state1.id,
            'questionresponse_set-TOTAL_FORMS': 0,
            'questionresponse_set-INITIAL_FORMS': 0,
            'questionresponse_set-MIN_NUM_FORMS': 0,
            'questionresponse_set-MAX_NUM_FORMS': 0,
            'schooladministrator_set-TOTAL_FORMS': 0,
            'schooladministrator_set-INITIAL_FORMS': 0,
            'schooladministrator_set-MIN_NUM_FORMS': 0,
            'schooladministrator_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:users_user_change', args=(self.user3.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

    def testHomeStateFieldDenied_change_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'email': self.user3.email,
            'homeState': self.state2.id,
            'questionresponse_set-TOTAL_FORMS': 0,
            'questionresponse_set-INITIAL_FORMS': 0,
            'questionresponse_set-MIN_NUM_FORMS': 0,
            'questionresponse_set-MAX_NUM_FORMS': 0,
            'schooladministrator_set-TOTAL_FORMS': 0,
            'schooladministrator_set-INITIAL_FORMS': 0,
            'schooladministrator_set-MIN_NUM_FORMS': 0,
            'schooladministrator_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:users_user_change', args=(self.user3.id,)), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

    def testHomeStateFieldBlankDenied_change_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'email': self.user3.email,
            'homeState': '',
            'questionresponse_set-TOTAL_FORMS': 0,
            'questionresponse_set-INITIAL_FORMS': 0,
            'questionresponse_set-MIN_NUM_FORMS': 0,
            'questionresponse_set-MAX_NUM_FORMS': 0,
            'schooladministrator_set-TOTAL_FORMS': 0,
            'schooladministrator_set-INITIAL_FORMS': 0,
            'schooladministrator_set-MIN_NUM_FORMS': 0,
            'schooladministrator_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:users_user_change', args=(self.user3.id,)), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'This field is required.')

    def testHomeStateFieldDenied_add_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'email': 'new@new.com',
            'password1': 'sldjghfsdkjfbn38',
            'password2': 'sldjghfsdkjfbn38',
            'homeState': self.state2.id,
        }
        response = self.client.post(reverse('admin:users_user_add'), data=payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

class TestUserAdminInlinesAndFields(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    emailsuper = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        adminSetUp(self)
        self.coord1 = Coordinator.objects.create(user=self.user1, state=self.state1, permissionLevel='full', position='Thing')
        self.coord2 = Coordinator.objects.create(user=self.user2, state=self.state2, permissionLevel='full', position='Thing')

        self.region1 = Region.objects.create(name='Test Region', description='test desc')
        self.school1 = School.objects.create(name='School 1', state=self.state1, region=self.region1)
        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user3)

    def testCorrectInlines_change_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.user3.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "School administrator of")
        self.assertContains(response, "Coordinator of")
        self.assertContains(response, "Question Responses")

    def testCorrectInlines_add_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:users_user_add'))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, "School administrator of")
        self.assertNotContains(response, "Coordinator of")
        self.assertNotContains(response, "Question Responses")

    def testCorrectInlines_change_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.user3.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "School administrator of")
        self.assertNotContains(response, "Coordinator of")
        self.assertContains(response, "Question Responses")

    def testCorrectInlines_add_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_add'))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, "School administrator of")
        self.assertNotContains(response, "Coordinator of")
        self.assertNotContains(response, "Question Responses")

    def testSchoolAdministratorInlineReadonly_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.user3.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "schooladministrator_set-0")
        self.assertNotContains(response, "Change selected School")
        self.assertNotContains(response, "schooladministrator_set-0-school-container")
        self.assertNotContains(response, '<a href="#">Add another School administrator of</a>')
        self.assertNotContains(response, "schooladministrator_set-0-DELETE")

    def testSchoolAdministratorInlineReadonly_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.user3.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "schooladministrator_set-0")
        self.assertNotContains(response, "Change selected School")
        self.assertNotContains(response, "schooladministrator_set-0-school-container")
        self.assertNotContains(response, '<a href="#">Add another School administrator of</a>')
        self.assertNotContains(response, "schooladministrator_set-0-DELETE")

    # Test readonly fields on change page

    def testCorrectReadonlyFields_change_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.user3.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, '<input type="checkbox" name="is_active"')
        self.assertNotContains(response, '<input type="checkbox" name="is_staff"')
        self.assertContains(response, '<input type="checkbox" name="is_superuser"')

    def testCorrectReadonlyFields_change_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.user3.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, '<input type="checkbox" name="is_active"')
        self.assertNotContains(response, '<input type="checkbox" name="is_staff"')
        self.assertNotContains(response, '<input type="checkbox" name="is_superuser"')

def adminPermissionsSetUp(self):
    self.state1 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='Victoria', abbreviation='VIC')
    self.state2 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='South Australia', abbreviation='SA')

    self.usersuper = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.emailsuper, password=self.password, homeState=self.state1, is_staff=True, is_superuser=True)
    self.usersuper2 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.emaulsuper2, password=self.password, homeState=self.state2, is_staff=True, is_superuser=True)
    
    self.user1 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email1, password=self.password, homeState=self.state1)
    self.user1_association_member = AssociationMember.objects.create(user=self.user1, birthday=(datetime.datetime.now() + datetime.timedelta(days=-20*365)).date(), rulesAcceptedDate=datetime.datetime.now(), membershipStartDate=datetime.datetime.now())

    self.user2 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email2, password=self.password, homeState=self.state2)
    self.user2_association_member = AssociationMember.objects.create(user=self.user2, birthday=(datetime.datetime.now() + datetime.timedelta(days=-20*365)).date(), rulesAcceptedDate=datetime.datetime.now(), membershipStartDate=datetime.datetime.now())

    self.coord1 = Coordinator.objects.create(user=self.user1, permissionLevel='full', position='Thing')

class TestUserAdminPermissions(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    emailsuper = 'user4@user.com'
    emaulsuper2 = 'user3@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        adminPermissionsSetUp(self)

    # Change load - same state

    def testSuperuserChangeLoads_sameState_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.usersuper.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, 'View user')
        self.assertContains(response, 'Change user')

        self.assertContains(response, 'Save')
        self.assertContains(response, 'Delete')

    def testNonsuperuserChangeLoads_sameState_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.user1.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, 'View user')
        self.assertContains(response, 'Change user')

        self.assertContains(response, 'Save')
        self.assertContains(response, 'Delete')

    def testSuperuserChangeLoads_readonly_sameState_fullcoordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.usersuper.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'View user')
        self.assertNotContains(response, 'Change user')

        self.assertNotContains(response, 'Save')
        self.assertNotContains(response, 'Delete')

    def testNonsuperuserChangeLoads_sameState_fullcoordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.user1.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, 'View user')
        self.assertContains(response, 'Change user')

        self.assertContains(response, 'Save')
        self.assertNotContains(response, 'Delete')

    # Change load - different state

    def testSuperuserChangeLoads_differentState_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.usersuper2.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, 'View user')
        self.assertContains(response, 'Change user')

        self.assertContains(response, 'Save')
        self.assertContains(response, 'Delete')

    def testNonsuperuserChangeLoads_differentState_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.user2.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, 'View user')
        self.assertContains(response, 'Change user')

        self.assertContains(response, 'Save')
        self.assertContains(response, 'Delete')

    def testSuperuserChangeLoads_denied_differentState_statecoordinator(self):
        self.coord1.state = self.state1
        self.coord1.save()

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.usersuper2.id,)))
        self.assertEqual(response.status_code, 302)

    def testNonsuperuserChangeLoads_denied_differentState_statecoordinator(self):
        self.coord1.state = self.state1
        self.coord1.save()

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.user2.id,)))
        self.assertEqual(response.status_code, 302)

    def testSuperuserChangeLoads_denied_differentState_fullcoordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.usersuper2.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'View user')
        self.assertNotContains(response, 'Change user')

        self.assertNotContains(response, 'Save')
        self.assertNotContains(response, 'Delete')

    def testNonsuperuserChangeLoads_denied_differentState_fullcoordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.user2.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, 'View user')
        self.assertContains(response, 'Change user')

        self.assertContains(response, 'Save')
        self.assertNotContains(response, 'Delete')

    # Change load - no state

    def testSuperuserChangeLoads_noState_superuser(self):
        self.usersuper2.homeState = None
        self.usersuper2.save()

        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.usersuper2.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, 'View user')
        self.assertContains(response, 'Change user')

        self.assertContains(response, 'Save')
        self.assertContains(response, 'Delete')

    def testNonsuperuserChangeLoads_noState_superuser(self):
        self.user2.homeState = None
        self.user2.save()

        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.user2.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, 'View user')
        self.assertContains(response, 'Change user')

        self.assertContains(response, 'Save')
        self.assertContains(response, 'Delete')

    def testSuperuserChangeLoads_readonly_noState_fullcoordinator(self):
        self.usersuper2.homeState = None
        self.usersuper2.save()

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.usersuper2.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'View user')
        self.assertNotContains(response, 'Change user')

        self.assertNotContains(response, 'Save')
        self.assertNotContains(response, 'Delete')

    def testNonsuperuserChangeLoads_noState_fullcoordinator(self):
        self.user2.homeState = None
        self.user2.save()

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:users_user_change', args=(self.user2.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, 'View user')
        self.assertContains(response, 'Change user')

        self.assertContains(response, 'Save')
        self.assertNotContains(response, 'Delete')

    # Password change load

    def testSuperuserPasswordchangeLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:auth_user_password_change', args=(self.usersuper.id,)))
        self.assertEqual(response.status_code, 200)

    def testNonsuperuserPasswordchangeLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:auth_user_password_change', args=(self.user1.id,)))
        self.assertEqual(response.status_code, 200)

    def testSuperuserPasswordchangeLoads_readonly_fullcoordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:auth_user_password_change', args=(self.usersuper.id,)))
        self.assertEqual(response.status_code, 403)

    def testNonsuperuserPasswordchangeLoads_fullcoordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:auth_user_password_change', args=(self.user1.id,)))
        self.assertEqual(response.status_code, 200)
