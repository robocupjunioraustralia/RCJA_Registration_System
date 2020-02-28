from users.models import User
from . models import School, SchoolAdministrator
from regions.models import State,Region
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, modify_settings
from django.urls import reverse
from django.test import Client
from users.models import User
from django.http import HttpRequest

# View Tests
class TestSchoolCreate(TestCase): #TODO update to use new auth model
    reverseString = 'schools:create'
    email = 'user@user.com'
    username = email
    password = 'chdj48958DJFHJGKDFNM'
    validPayload = {'email':email,
        'password':password,
        'passwordConfirm':password,
        'first_name':'test',
        'lastName':'test',
        'school':1,
        'mobileNumber':'123123123'
        }

    validLoadCode = 200
    validSubmitCode = 302
    inValidCreateCode = 200

    def setUp(self):
        self.user = User.objects.create_user(email=self.username, password=self.password)
        self.newState = State.objects.create(treasurer=self.user,name='Victoria',abbreviation='VIC')
        self.newRegion = Region.objects.create(name='Test Region',description='test desc')
        self.newSchool = School.objects.create(name='Melbourne High',abbreviation='MHS',state=self.newState,region=self.newRegion)
        self.validPayload["school"] = self.newSchool.id
        # self.client.login(request=HttpRequest(), username=self.email, password=self.password)

    def testValidPageLoad(self):
        self.client.login(request=HttpRequest(), username=self.username, password=self.password)
        response = self.client.get(reverse(self.reverseString))
        self.assertEqual(response.status_code, self.validLoadCode)    
    
    def testValidSchoolCreation(self):
        self.client.login(request=HttpRequest(), username=self.username, password=self.password)
        payload= {'name':'test','abbreviation':'TSST','state':self.newState.id,'region':self.newRegion.id}
        response = self.client.post(reverse(self.reverseString),data=payload)
        self.assertEqual(response.status_code,self.validSubmitCode)
        self.assertEqual(School.objects.all().count(), 2)
        self.assertEqual(School.objects.all()
                         [1].name, 'test')

    def testInvalidSchoolCreation(self):
        self.client.login(request=HttpRequest(), username=self.username, password=self.password)
        payload= {'name':'test','abbreviation':'TSST','state':self.newState.id,'region':self.newRegion.id}
        self.client.post(reverse(self.reverseString),data=payload)
        response = self.client.post(reverse(self.reverseString),data=payload)

        self.assertEqual(response.status_code,self.inValidCreateCode)
        self.assertIn(b'School with this Abbreviation already exists.',response.content)
        self.assertIn(b'School with this Name already exists.',response.content)

# class TestSchoolAJAXCreate(TestSchoolCreate):
#     reverseString = 'schools:createAJAX'
#     validLoadCode = 403 #no get requests to this url
#     validSubmitCode = 200
#     inValidCreateCode = 400

@modify_settings(MIDDLEWARE={
    'remove': 'common.redirectsMiddleware.RedirectMiddleware',
})
class AuthViewTests(TestCase):
    email = 'user@user.com'
    password = 'chdj48958DJFHJGKDFNM'
    validPayload = {'email':email,
        'password':password,
        'passwordConfirm':password,
        'first_name':'test',
        'last_name':'test',
        'school':1,
        'mobileNumber':'123123123',
        'homeState': 1,
        'homeRegion': 1,
        }

    def setUp(self):
        self.user = user = User.objects.create_user(email='admin@test.com', password='admin')
        self.newState = State.objects.create(treasurer=self.user,name='Victoria',abbreviation='VIC')
        self.newRegion = Region.objects.create(name='Test Region',description='test desc')
        self.newSchool = School.objects.create(name='Melbourne High',abbreviation='MHS',state=self.newState,region=self.newRegion)
        self.validPayload["school"] = self.newSchool.id
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
        prevUsers = get_user_model().objects.all().count()

        payloadData = self.validPayload
        response = self.client.post(path=reverse('users:signup'),data = payloadData)
        self.assertEqual(response.status_code,302) #ensure user is redirected on signup
        self.assertEqual(get_user_model().objects.all().count(), prevUsers + 1)
        self.assertEqual(get_user_model().objects.all()[1].email, self.email) #this checks the user created has the right username
                                                    #note that this works because transactions aren't saved in django tests

    def testUserInvalidSignup(self):
        payloadData = {'username':self.email}
        response = self.client.post(path=reverse('users:signup'),data = payloadData)
        self.assertEqual(response.status_code,200) #ensure user is not redirected
        self.assertEqual(get_user_model().objects.all().count(), 1)
    
    def testUserExistingSignup(self):
        payloadData = self.validPayload
        self.client.post(path=reverse('users:signup'),data = payloadData)
        response = self.client.post(path=reverse('users:signup'), data = payloadData)
        self.assertEqual(response.status_code,200) #ensure failed signup
        self.assertIn(b'Email address: User with this Email address already exists.',response.content)

    def testUserExistingSignupCaseInsensitive(self):
        payloadData = self.validPayload
        self.client.post(path=reverse('users:signup'),data = payloadData)
        payloadData['email'] = 'UsEr@user.com'
        response = self.client.post(path=reverse('users:signup'), data = payloadData)
        self.assertEqual(response.status_code,200) #ensure failed signup
        self.assertIn(b'Email address: User with this Email address already exists.',response.content)
        payloadData['email'] = self.email # reset email for other tests

    def testUserInvalidPasswordConfirmSignup(self):
        payloadData = self.validPayload.copy()
        payloadData["passwordConfirm"] = 'asasdaasasa'
        response = self.client.post(path=reverse('users:signup'), data = payloadData)
        self.assertEqual(response.status_code,200) #ensure failed signup
        self.assertIn(b'Passwords do not match',response.content)

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
        response = self.client.get('/accounts/logout/')
        self.assertEqual(response.status_code, 200)

    def testLogoutByName(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 200)

    def testLogoutUsesCorrectTemplate(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/logged_out.html')

    def testUserCreatedLogsOut(self):
        user = User.objects.create_user(
            email=self.email,
            password=self.password
        )
        user.save()
        self.client.login(request=HttpRequest(), username=self.email, password=self.password)
        self.client.get(reverse('logout'))
        # Try an unauthorized page
        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 302)

class ProfileEditTests(TestCase):
    email = 'user@user.com'
    password = 'chdj48958DJFHJGKDFNM'
    
    def setUp(self):
        self.validPayload = {
            'email':self.email,
            'password':self.password,
            'passwordConfirm':self.password,
            'first_name':'test',
            'last_name':'test',
            'school':1,
            'mobileNumber':'123123123',
            'homeState': 1,
            'homeRegion': 1,
        }
        self.user = user = User.objects.create_user(
            email='admin@test.com',
            password='admin'
        )
        self.newState = State.objects.create(treasurer=self.user,name='Victoria',abbreviation='VIC')
        self.newRegion = Region.objects.create(name='Test Region',description='test desc')
        self.newSchool = School.objects.create(name='Melbourne High',abbreviation='MHS',state=self.newState,region=self.newRegion)
        self.validPayload["school"] = self.newSchool.id
        self.validPayload["homeState"] = self.newState.id
        self.validPayload["homeRegion"] = self.newRegion.id

        response = self.client.post(path=reverse('users:signup'),data = self.validPayload)
        self.client.login(request=HttpRequest(), username=self.email,password=self.password)

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
        self.assertEqual(User.objects.get(first_name="Admin").email,'admon@admon.com')

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

class TestSetCurrentSchool(TestCase):
    email = 'user@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        self.user = User.objects.create_user(email=self.email, password=self.password)
        self.state1 = State.objects.create(treasurer=self.user, name='Victoria', abbreviation='VIC')
        self.region1 = Region.objects.create(name='Test Region', description='test desc')
        self.school1 = School.objects.create(name='School 1', abbreviation='sch1', state=self.state1, region=self.region1)
        self.school2 = School.objects.create(name='School 2', abbreviation='sch2', state=self.state1, region=self.region1)
        self.school3 = School.objects.create(name='School 3', abbreviation='sch3', state=self.state1, region=self.region1)

    def testSchoolAdministratorCreate(self):
        # Test creating first admin sets currentlySelectedSchool
        self.assertEqual(self.user.currentlySelectedSchool, None)
        SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)

        # Test creating second one doesn't
        SchoolAdministrator.objects.create(school=self.school2, user=self.user)
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)

    def testSchoolAdministratorDelete(self):
        # Setup
        admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        admin2 = SchoolAdministrator.objects.create(school=self.school2, user=self.user)
        admin3 = SchoolAdministrator.objects.create(school=self.school3, user=self.user)
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)

        # Test deletion while remaining schools
        admin3.delete()
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)

        # Test deletion of currently set school admin
        admin1.delete()
        self.assertEqual(self.user.currentlySelectedSchool, self.school2)

        # test deletion of last school admin
        admin2.delete()
        self.assertEqual(self.user.currentlySelectedSchool, None)

    def testSuccesful_setCurrentSchool(self):
        # Setup
        admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        admin2 = SchoolAdministrator.objects.create(school=self.school2, user=self.user)
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)

        self.client.login(request=HttpRequest(), username=self.email, password=self.password)

        # Change to school 2
        url = reverse('schools:setCurrentSchool', kwargs= {'schoolID':self.school2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Check school changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.currentlySelectedSchool, self.school2)

    def testDenied_setCurrentSchool(self):
        # Setup
        admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        admin2 = SchoolAdministrator.objects.create(school=self.school2, user=self.user)
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)

        self.client.login(request=HttpRequest(), username=self.email, password=self.password)

        # Attempt change to school 3
        url = reverse('schools:setCurrentSchool', kwargs= {'schoolID':self.school3.id})
        response = self.client.get(url)
        self.assertContains(response, "You do not have permission to view this school", status_code=403)
        self.assertEqual(response.status_code, 403)

        # Check still school 1
        self.user.refresh_from_db()
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)

    def testLoginRequired_setCurrentSchool(self):
        # Setup
        admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        admin2 = SchoolAdministrator.objects.create(school=self.school2, user=self.user)
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)

        # Attempt change to school 3
        url = reverse('schools:setCurrentSchool', kwargs= {'schoolID':self.school3.id})
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Login")
        response = self.client.get(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/schools/setCurrentSchool/{self.school3.id}")
        self.assertEqual(response.status_code, 302)

        # Check still school 1
        self.user.refresh_from_db()
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)
