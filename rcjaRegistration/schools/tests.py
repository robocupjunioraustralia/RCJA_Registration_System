from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, modify_settings
from django.urls import reverse
from django.test import Client
from django.http import HttpRequest

from users.models import User
from .models import School, SchoolAdministrator
from regions.models import State, Region

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
