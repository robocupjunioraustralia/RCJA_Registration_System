from django.contrib.auth.models import User
from . models import School,Mentor
from regions.models import State,Region
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.test import Client

# View Tests
class TestMentorRego(TestCase):
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
        response = self.client.get('/schools/mentorRegistration') #todo change to reversed url
        self.assertEqual(response.status_code, 200)
    
    def testLoggedOutPageLoad(self):
        response = self.client.get('/schools/mentorRegistration')
        self.assertEqual(response.status_code, 302)
    
    def testValidMentorCreation(self):
        self.client.login(username=self.username, password=self.password)
        payload = {"school":1,"mobileNumber":123123123}
        response = self.client.post('/schools/mentorRegistration', data = payload)
        self.assertEqual(response.status_code,302)
    
    def testInvalidMentorCreation(self):
        self.client.login(username=self.username, password=self.password)
        payload = {"school":9999,"mobileNumber":123123123}
        response = self.client.post('/schools/mentorRegistration',data = payload)
        self.assertEqual(response.status_code,200)
        self.assertIn(b'Select a valid choice. That choice is not one of the available choices.',response.content)
    
class TestSchoolCreate(TestCase):
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
        response = self.client.get('/schools/schoolCreation') #todo change to reversed url
        self.assertEqual(response.status_code, 200)    
    
    def testLoggedOutPageLoad(self):
        response = self.client.get('/schools/schoolCreation')
        self.assertEqual(response.status_code, 302)

    def testValidSchoolCreation(self):
        self.client.login(username=self.username, password=self.password)
        payload= {'name':'test','abbreviation':'TSST','state':'1','region':'1'}
        response = self.client.post('/schools/schoolCreation',data=payload)
        self.assertEqual(response.status_code,302)
        self.assertEqual(School.objects.all().count(), 2)
        self.assertEqual(School.objects.all()
                         [1].name, 'test')

    def testInvalidSchoolCreation(self):
        self.client.login(username=self.username, password=self.password)
        payload= {'name':'test','abbreviation':'TSST','state':'1','region':'1'}
        self.client.post('/schools/schoolCreation',data=payload)
        response = self.client.post('/schools/schoolCreation',data=payload)

        self.assertEqual(response.status_code,200)
        self.assertIn(b'School with this Abbreviation already exists.',response.content)
        self.assertIn(b'School with this Name already exists.',response.content)
