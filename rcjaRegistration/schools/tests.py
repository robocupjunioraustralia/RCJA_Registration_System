from django.contrib.auth.models import User
from . models import School,Mentor
from regions.models import State,Region
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.test import Client
# View Tests
class TestSchoolCreate(TestCase): #TODO update to use new auth model
    username = 'user'
    password = 'password'
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username=self.username,password=self.password)

        newState = State.objects.create(treasurer=self.user,name='Victoria',abbreviation='VIC')
        newRegion = Region.objects.create(name='Test Region',description='test desc')
        newSchool = School.objects.create(name='Melbourne High',abbreviation='MHS',state=newState,region=newRegion)
    
    def testValidPageLoad(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('schools:createSchool'))
        self.assertEqual(response.status_code, 200)    
    
    def testValidSchoolCreation(self):
        self.client.login(username=self.username, password=self.password)
        payload= {'name':'test','abbreviation':'TSST','state':'1','region':'1'}
        response = self.client.post(reverse('schools:createSchool'),data=payload)
        self.assertEqual(response.status_code,302)
        self.assertEqual(School.objects.all().count(), 2)
        self.assertEqual(School.objects.all()
                         [1].name, 'test')

    def testInvalidSchoolCreation(self):
        self.client.login(username=self.username, password=self.password)
        payload= {'name':'test','abbreviation':'TSST','state':'1','region':'1'}
        self.client.post(reverse('schools:createSchool'),data=payload)
        response = self.client.post(reverse('schools:createSchool'),data=payload)

        self.assertEqual(response.status_code,200)
        self.assertIn(b'School with this Abbreviation already exists.',response.content)
        self.assertIn(b'School with this Name already exists.',response.content)


class AuthViewTests(TestCase):
    email = 'user@user.com'
    password = 'password'
    validPayload = {'email':email,
        'password':password,
        'passwordConfirm':password,
        'firstName':'test',
        'lastName':'test',
        'school':1,
        'mobileNumber':'123123123'
        }
    def setUp(self):
        self.user = user = User.objects.create_user(username='admin',
                                 email='admin@test.com',
                                 password='admin')
        self.newState = State.objects.create(treasurer=self.user,name='Victoria',abbreviation='VIC')
        self.newRegion = Region.objects.create(name='Test Region',description='test desc')
        self.newSchool = School.objects.create(name='Melbourne High',abbreviation='MHS',state=self.newState,region=self.newRegion)

    def testSignupByUrl(self):
        response = self.client.get('/accounts/signup')
        self.assertEqual(response.status_code, 200)

    def testSignupByName(self):
        response = self.client.get(reverse('schools:signup'))
        self.assertEqual(response.status_code, 200)

    def testSignupUsesCorrectTemplate(self):
        response = self.client.get(reverse('schools:signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/signup.html')

    def testUserValidSignup(self):
        prevUsers = get_user_model().objects.all().count()

        payloadData = self.validPayload
        response = self.client.post(path=reverse('schools:signup'),data = payloadData)
        self.assertEqual(response.status_code,302) #ensure user is redirected on signup
        self.assertEqual(get_user_model().objects.all().count(), prevUsers + 1)
        self.assertEqual(get_user_model().objects.all()
                         [1].username, self.email) #this checks the user created has the right username
                                                    #note that this works because transactions aren't saved in django tests

    def testUserInvalidSignup(self):
        payloadData = {'username':self.email}
        response = self.client.post(path=reverse('schools:signup'),data = payloadData)
        self.assertEqual(response.status_code,200) #ensure user is not redirected
        self.assertEqual(get_user_model().objects.all().count(), 1)
    
    def testUserExistingSignup(self):
        payloadData = self.validPayload
        self.client.post(path=reverse('schools:signup'),data = payloadData)
        response = self.client.post(path=reverse('schools:signup'), data = payloadData)
        self.assertEqual(response.status_code,200) #ensure failed signup
        self.assertIn(b'Email: Mentor with this Email already exists.',response.content)


    def testLoginByUrl(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

    def testLoginByName(self):
        response = self.client.get(reverse('login'))
        print(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def testLoginUsesCorrectTemplate(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def testUserCreatedLogsIn(self):
        payloadData = self.validPayload
        self.client.post(path=reverse('schools:signup'),data = payloadData)
        loginPayload = {'username':self.email,'password':self.password}
        response = self.client.post(path=reverse('login'),data = loginPayload)
        self.assertEqual(response.status_code,302) #ensure a successful login works and redirects