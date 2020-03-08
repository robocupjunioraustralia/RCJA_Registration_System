from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, modify_settings
from django.urls import reverse
from django.test import Client
from django.http import HttpRequest
from django.core.exceptions import ValidationError

from users.models import User
from .models import School, SchoolAdministrator, Campus
from regions.models import State, Region
from events.models import Year, Division, Event
from invoices.models import Invoice
from coordination.models import Coordinator

import datetime

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

class TestCurrentlySelectedSchool(TestCase):
    email = 'user@user.com'
    email2 = 'user2@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        self.user = User.objects.create_user(email=self.email, password=self.password)
        self.user2 = User.objects.create_user(email=self.email2, password=self.password)

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

        # Test deletion of non current school admin while remaining schools
        admin3.delete()
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)

        # Test deletion of currently set school admin while remaining schools
        admin1.delete()
        self.assertEqual(self.user.currentlySelectedSchool, self.school2)

        # test deletion of last school admin
        admin2.delete()
        self.assertEqual(self.user.currentlySelectedSchool, None)

    def testSchoolAdministratorUserChange(self):
        # Setup
        admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)

        # test changing user field on school administrator
        admin1.user = self.user2
        admin1.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.currentlySelectedSchool, None)
        self.assertEqual(self.user2.currentlySelectedSchool, self.school1)

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

    def testCurrentlySelectedSchoolDelete(self):
        admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        admin2 = SchoolAdministrator.objects.create(school=self.school2, user=self.user)
        self.assertEqual(self.user.currentlySelectedSchool, self.school1)

        self.school1.delete()
        self.user.refresh_from_db()
        self.assertEqual(self.user.currentlySelectedSchool, self.school2)

class TestEditSchoolDetails(TestCase):
    email = 'user@user.com'
    email2 = 'user2@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        self.user = User.objects.create_user(email=self.email, password=self.password)
        self.user2 = User.objects.create_user(email=self.email2, password=self.password)

        self.state1 = State.objects.create(treasurer=self.user, name='Victoria', abbreviation='VIC')
        self.region1 = Region.objects.create(name='Test Region', description='test desc')

        self.school1 = School.objects.create(name='School 1', abbreviation='sch1', state=self.state1, region=self.region1)
        self.school2 = School.objects.create(name='School 2', abbreviation='sch2', state=self.state1, region=self.region1)
        self.school3 = School.objects.create(name='School 3', abbreviation='sch3', state=self.state1, region=self.region1)

        self.year = Year.objects.create(year=2020)
        self.event = Event.objects.create(
            year=self.year,
            state=self.state1,
            name='Test event 1',
            maxMembersPerTeam=5,
            entryFeeIncludesGST=True,
            event_billingType='team',
            event_defaultEntryFee = 50,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=5)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date(),
            directEnquiriesTo = self.user,
        )

    def testLoginRequired(self):
        url = reverse('schools:details')
    
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Login")
    
        response = self.client.get(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/schools/profile")
        self.assertEqual(response.status_code, 302)

    def testLoads(self):
        self.admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.client.login(request=HttpRequest(), username=self.email, password=self.password)
        url = reverse('schools:details')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def testDenied_noSchool(self):
        self.client.login(request=HttpRequest(), username=self.email, password=self.password)
        url = reverse('schools:details')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this school", status_code=403)

    def testChangeName_success(self):
        self.admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.client.login(request=HttpRequest(), username=self.email, password=self.password)
        url = reverse('schools:details')

        payload = {
            'campus_set-TOTAL_FORMS':2,
            "campus_set-INITIAL_FORMS":0,
            "campus_set-MIN_NUM_FORMS":0,
            "campus_set-MAX_NUM_FORMS":1000,
            'schooladministrator_set-TOTAL_FORMS':1,
            "schooladministrator_set-INITIAL_FORMS":0,
            "schooladministrator_set-MIN_NUM_FORMS":0,
            "schooladministrator_set-MAX_NUM_FORMS":1000,
            "name":"New name",
            "abbreviation": 'sch1',
            'state': self.state1.id,
            'region': self.region1.id,
        }

        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)
        School.objects.get(name='New name')

    def testChangeName_failure(self):
        self.admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.client.login(request=HttpRequest(), username=self.email, password=self.password)
        url = reverse('schools:details')

        payload = {
            'campus_set-TOTAL_FORMS':2,
            "campus_set-INITIAL_FORMS":0,
            "campus_set-MIN_NUM_FORMS":0,
            "campus_set-MAX_NUM_FORMS":1000,
            'schooladministrator_set-TOTAL_FORMS':1,
            "schooladministrator_set-INITIAL_FORMS":0,
            "schooladministrator_set-MIN_NUM_FORMS":0,
            "schooladministrator_set-MAX_NUM_FORMS":1000,
            "name":"SchoOl 2",
            "abbreviation": 'sch1',
            'state': self.state1.id,
            'region': self.region1.id,
        }

        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'School with this name exists. Please ask your school administrator to add you.')

    def testMissingState_failure(self):
        self.admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.client.login(request=HttpRequest(), username=self.email, password=self.password)
        url = reverse('schools:details')

        payload = {
            'campus_set-TOTAL_FORMS':2,
            "campus_set-INITIAL_FORMS":0,
            "campus_set-MIN_NUM_FORMS":0,
            "campus_set-MAX_NUM_FORMS":1000,
            'schooladministrator_set-TOTAL_FORMS':1,
            "schooladministrator_set-INITIAL_FORMS":0,
            "schooladministrator_set-MIN_NUM_FORMS":0,
            "schooladministrator_set-MAX_NUM_FORMS":1000,
            "name":"other name",
            "abbreviation": 'sch1',
            'region': self.region1.id,
        }

        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 200)

    def testAddCampus_success(self):
        self.admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.client.login(request=HttpRequest(), username=self.email, password=self.password)
        url = reverse('schools:details')

        payload = {
            'campus_set-TOTAL_FORMS':2,
            "campus_set-INITIAL_FORMS":0,
            "campus_set-MIN_NUM_FORMS":0,
            "campus_set-MAX_NUM_FORMS":1000,
            'schooladministrator_set-TOTAL_FORMS':1,
            "schooladministrator_set-INITIAL_FORMS":0,
            "schooladministrator_set-MIN_NUM_FORMS":0,
            "schooladministrator_set-MAX_NUM_FORMS":1000,
            "name":"other name",
            "abbreviation": 'sch1',
            'state': self.state1.id,
            'region': self.region1.id,
            'campus_set-0-name': 'First campus',
            'campus_set-1-name': 'Second campus',
        }

        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)
        Campus.objects.get(name='First campus')
        Campus.objects.get(name='Second campus')

    def testDeleteCampus_success(self):
        self.campus1 = Campus.objects.create(school=self.school1, name='test 1')
        Campus.objects.get(name='test 1')
        self.admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.client.login(request=HttpRequest(), username=self.email, password=self.password)
        url = reverse('schools:details')
        numberExistingCampuses = Campus.objects.count()

        payload = {
            'campus_set-TOTAL_FORMS':3,
            "campus_set-INITIAL_FORMS":1,
            "campus_set-MIN_NUM_FORMS":0,
            "campus_set-MAX_NUM_FORMS":1000,
            'schooladministrator_set-TOTAL_FORMS':1,
            "schooladministrator_set-INITIAL_FORMS":0,
            "schooladministrator_set-MIN_NUM_FORMS":0,
            "schooladministrator_set-MAX_NUM_FORMS":1000,
            "name":"other name",
            "abbreviation": 'sch1',
            'state': self.state1.id,
            'region': self.region1.id,
            'campus_set-0-id': self.campus1.id,
            'campus_set-0-name': 'test 1',
            'campus_set-0-DELETE': 'on',
        }

        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)
        self.assertRaises(Campus.DoesNotExist, lambda: Campus.objects.get(name='test 1'))
        self.assertEqual(Campus.objects.count(), numberExistingCampuses-1)

    def testDeleteCampus_protected(self):
        self.campus1 = Campus.objects.create(school=self.school1, name='test 1')
        Invoice.objects.create(event=self.event, invoiceToUser=self.user, school=self.school1, campus=self.campus1)
        Campus.objects.get(name='test 1')
        self.admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.client.login(request=HttpRequest(), username=self.email, password=self.password)
        url = reverse('schools:details')

        payload = {
            'campus_set-TOTAL_FORMS':3,
            "campus_set-INITIAL_FORMS":1,
            "campus_set-MIN_NUM_FORMS":0,
            "campus_set-MAX_NUM_FORMS":1000,
            'schooladministrator_set-TOTAL_FORMS':1,
            "schooladministrator_set-INITIAL_FORMS":0,
            "schooladministrator_set-MIN_NUM_FORMS":0,
            "schooladministrator_set-MAX_NUM_FORMS":1000,
            "name":"other name",
            "abbreviation": 'sch1',
            'state': self.state1.id,
            'region': self.region1.id,
            'campus_set-0-id': self.campus1.id,
            'campus_set-0-name': 'test 1',
            'campus_set-0-DELETE': 'on',
        }

        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)
        Campus.objects.get(name='test 1')

    def testAdministratorList(self):
        self.admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.admin2 = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)
        self.client.login(request=HttpRequest(), username=self.email, password=self.password)
        url = reverse('schools:details')

        payload = {
            'campus_set-TOTAL_FORMS':2,
            "campus_set-INITIAL_FORMS":2,
            "campus_set-MIN_NUM_FORMS":0,
            "campus_set-MAX_NUM_FORMS":1000,
            'schooladministrator_set-TOTAL_FORMS':2,
            "schooladministrator_set-INITIAL_FORMS":2,
            "schooladministrator_set-MIN_NUM_FORMS":0,
            "schooladministrator_set-MAX_NUM_FORMS":1000,
            "name":"other name",
            "abbreviation": 'sch1',
            'state': self.state1.id,
            'region': self.region1.id,
        }

        response = self.client.get(url, data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.email2)

    def testAdministratorDelete_success(self):
        self.admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.admin2 = SchoolAdministrator.objects.create(school=self.school1, user=self.user2)
        self.client.login(request=HttpRequest(), username=self.email, password=self.password)
        url = reverse('schools:details')
        SchoolAdministrator.objects.get(pk=self.admin2.pk)
        numberExistingAdmins = SchoolAdministrator.objects.count()

        payload = {
            'campus_set-TOTAL_FORMS':2,
            "campus_set-INITIAL_FORMS":0,
            "campus_set-MIN_NUM_FORMS":0,
            "campus_set-MAX_NUM_FORMS":1000,
            'schooladministrator_set-TOTAL_FORMS':2,
            "schooladministrator_set-INITIAL_FORMS":2,
            "schooladministrator_set-MIN_NUM_FORMS":0,
            "schooladministrator_set-MAX_NUM_FORMS":1000,
            "name":"other name",
            "abbreviation": 'sch1',
            'state': self.state1.id,
            'region': self.region1.id,
            'schooladministrator_set-0-id': self.admin1.id,
            'schooladministrator_set-1-id': self.admin2.id,
            'schooladministrator_set-1-DELETE': 'on',
        }

        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)
        self.assertRaises(SchoolAdministrator.DoesNotExist, lambda: SchoolAdministrator.objects.get(pk=self.admin2.pk))
        self.assertEqual(SchoolAdministrator.objects.count(), numberExistingAdmins-1)

    def testAdministratorAdd_existing(self):
        self.admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.client.login(request=HttpRequest(), username=self.email, password=self.password)
        url = reverse('schools:details')
        numberExistingAdmins = SchoolAdministrator.objects.count()
        numberExistingUsers = User.objects.count()

        payload = {
            'campus_set-TOTAL_FORMS':2,
            "campus_set-INITIAL_FORMS":0,
            "campus_set-MIN_NUM_FORMS":0,
            "campus_set-MAX_NUM_FORMS":1000,
            'schooladministrator_set-TOTAL_FORMS':0,
            "schooladministrator_set-INITIAL_FORMS":0,
            "schooladministrator_set-MIN_NUM_FORMS":0,
            "schooladministrator_set-MAX_NUM_FORMS":1000,
            "name":"other name",
            "abbreviation": 'sch1',
            'state': self.state1.id,
            'region': self.region1.id,
            'addAdministratorEmail': self.email2.upper(),
        }

        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SchoolAdministrator.objects.count(), numberExistingAdmins+1)
        self.assertEqual(User.objects.count(), numberExistingUsers)
        SchoolAdministrator.objects.get(school=self.school1, user=self.user2)

    def testAdministratorAdd_new(self):
        self.admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.client.login(request=HttpRequest(), username=self.email, password=self.password)
        url = reverse('schools:details')
        numberExistingAdmins = SchoolAdministrator.objects.count()
        numberExistingUsers = User.objects.count()

        payload = {
            'campus_set-TOTAL_FORMS':2,
            "campus_set-INITIAL_FORMS":0,
            "campus_set-MIN_NUM_FORMS":0,
            "campus_set-MAX_NUM_FORMS":1000,
            'schooladministrator_set-TOTAL_FORMS':0,
            "schooladministrator_set-INITIAL_FORMS":0,
            "schooladministrator_set-MIN_NUM_FORMS":0,
            "schooladministrator_set-MAX_NUM_FORMS":1000,
            "name":"other name",
            "abbreviation": 'sch1',
            'state': self.state1.id,
            'region': self.region1.id,
            'addAdministratorEmail': 'new@new.com',
        }

        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SchoolAdministrator.objects.count(), numberExistingAdmins+1)
        self.assertEqual(User.objects.count(), numberExistingUsers+1)
        SchoolAdministrator.objects.get(school=self.school1, user__email='new@new.com')

    def testAdministratorAdd_invalidEMail(self):
        self.admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user)
        self.client.login(request=HttpRequest(), username=self.email, password=self.password)
        url = reverse('schools:details')
        numberExistingAdmins = SchoolAdministrator.objects.count()
        numberExistingUsers = User.objects.count()

        payload = {
            'campus_set-TOTAL_FORMS':2,
            "campus_set-INITIAL_FORMS":0,
            "campus_set-MIN_NUM_FORMS":0,
            "campus_set-MAX_NUM_FORMS":1000,
            'schooladministrator_set-TOTAL_FORMS':0,
            "schooladministrator_set-INITIAL_FORMS":0,
            "schooladministrator_set-MIN_NUM_FORMS":0,
            "schooladministrator_set-MAX_NUM_FORMS":1000,
            "name":"other name",
            "abbreviation": 'sch1',
            'state': self.state1.id,
            'region': self.region1.id,
            'addAdministratorEmail': 'new',
        }

        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SchoolAdministrator.objects.count(), numberExistingAdmins)
        self.assertEqual(User.objects.count(), numberExistingUsers)

def schoolSetUp(self):
    self.user1 = User.objects.create_user(email=self.email1, password=self.password)
    self.state1 = State.objects.create(treasurer=self.user1, name='Victoria', abbreviation='VIC')
    self.region1 = Region.objects.create(name='Test Region', description='test desc')
    self.school1 = School.objects.create(name='School 1', abbreviation='sch1', state=self.state1, region=self.region1)

class TestSchoolClean(TestCase):
    email1 = 'user@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        schoolSetUp(self)

    def testValid(self):
        school2 = School(
            name='School 2',
            abbreviation='sch2',
            state=self.state1,
            region=self.region1
        )

        self.assertEqual(school2.clean(), None)

    def testNameCaseInsensitive(self):
        school2 = School(
            name='SchoOl 1',
            abbreviation='thi',
            state=self.state1,
            region=self.region1
        )
        self.assertRaises(ValidationError, school2.clean)

    def testAbbreviationCaseInsensitive(self):
        school2 = School(
            name='Thing',
            abbreviation='sCh1',
            state=self.state1,
            region=self.region1
        )
        self.assertRaises(ValidationError, school2.clean)

    def testAbbreviationMinLength(self):
        school2 = School(
            name='Thing',
            abbreviation='12',
            state=self.state1,
            region=self.region1
        )
        self.assertRaises(ValidationError, school2.clean)

    def testAbbreviationNotIND(self):
        school2 = School(
            name='Thing',
            abbreviation='ind',
            state=self.state1,
            region=self.region1
        )
        self.assertRaises(ValidationError, school2.clean)     

    def testNameNotIndependent(self):
        school2 = School(
            name='IndePendent',
            abbreviation='thi',
            state=self.state1,
            region=self.region1
        )
        self.assertRaises(ValidationError, school2.clean)    

class TestSchoolMethods(TestCase):
    email1 = 'user@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        schoolSetUp(self)

    def testGetState(self):
        self.assertEqual(self.school1.getState(), self.state1)

    def testStr(self):
        self.assertEqual(str(self.school1), 'School 1')

    def testSave(self):
        school2 = School(
            name='School 2',
            abbreviation='sch2',
            state=self.state1,
            region=self.region1
        )

        self.assertEqual(school2.abbreviation, 'sch2')
        school2.save()
        self.assertEqual(school2.abbreviation, 'SCH2')

def setupCampusAndAdministrators(self):
    self.campus1 = Campus.objects.create(school=self.school1, name='Campus 1')
    self.admin1 = SchoolAdministrator.objects.create(school=self.school1, campus=self.campus1, user=self.user1)
    self.school2 = School.objects.create(name='School 2', abbreviation='sch2', state=self.state1, region=self.region1)

class TestCampusMethods(TestCase):
    email1 = 'user@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        schoolSetUp(self)
        self.campus1 = Campus.objects.create(school=self.school1, name='Campus 1')

    def testGetState(self):
        self.assertEqual(self.campus1.getState(), self.state1)

    def testStr(self):
        self.assertEqual(str(self.campus1), 'Campus 1')

class TestSchoolAdministratorClean(TestCase):
    email1 = 'user@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        schoolSetUp(self)
        setupCampusAndAdministrators(self)

    def testValid(self):
        self.assertEqual(self.admin1.clean(), None)

    def testNoCampusValid(self):
        self.admin1.campus = None
        self.assertEqual(self.admin1.clean(), None)
    
    def testWrongSchool(self):
        self.admin1.school = self.school2
        self.assertRaises(ValidationError, self.admin1.clean)

class TestSchoolAdministratorMethods(TestCase):
    email1 = 'user@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        schoolSetUp(self)
        self.admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user1)

    def testGetState(self):
        self.assertEqual(self.admin1.getState(), self.state1)

    def testStr(self):
        self.assertEqual(str(self.admin1), self.email1)

def adminSetUp(self):
    self.user1 = User.objects.create_user(email=self.email1, password=self.password)
    self.usersuper = User.objects.create_user(email=self.emailsuper, password=self.password, is_staff=True, is_superuser=True)

    self.state1 = State.objects.create(treasurer=self.user1, name='Victoria', abbreviation='VIC')
    self.state2 = State.objects.create(treasurer=self.user1, name='South Australia', abbreviation='SA')

    self.region1 = Region.objects.create(name='Metro')

    self.user2 = User.objects.create_user(email=self.email2, password=self.password, homeState=self.state2)
    self.user3 = User.objects.create_user(email=self.email3, password=self.password, homeState=self.state1)

    self.school1 = School.objects.create(name='School 1', abbreviation='SCH1', state=self.state1, region=self.region1)
    self.school2 = School.objects.create(name='School 2', abbreviation='SCH2', state=self.state2, region=self.region1)

class TestSchoolAdmin(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    emailsuper = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        adminSetUp(self)

    # School filtering

    def testSchoolListLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:schools_school_changelist'))
        self.assertEqual(response.status_code, 200)

    def testSchoolChangeLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:schools_school_change', args=(self.school1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save')

    def testSchoolListContent_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:schools_school_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'School 1')
        self.assertContains(response, 'School 2')

    def testSchoolDeleteLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:schools_school_delete', args=(self.school1.id,)))
        self.assertEqual(response.status_code, 200)

    def testSchoolListNonStaff_denied(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_school_changelist'))
        self.assertEqual(response.status_code, 302)

    def testSchoolListLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_school_changelist'))
        self.assertEqual(response.status_code, 200)

    def testSchoolListContent_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_school_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'School 1')
        self.assertNotContains(response, 'School 2')

    def testSchoolChangeLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_school_change', args=(self.school1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save')

    def testSchoolAddLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_school_add'))
        self.assertEqual(response.status_code, 200)

    def testSchoolDeleteLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_school_delete', args=(self.school1.id,)))
        self.assertEqual(response.status_code, 200)

    def testSchoolChangeDenied_wrongState_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_school_change', args=(self.school2.id,)))
        self.assertEqual(response.status_code, 302)

    def testSchoolViewLoads_viewonly_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='viewall', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_school_change', args=(self.school1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Save')

    def testSchoolAddDenied_viewPermission_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='viewall', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_school_add'))
        self.assertEqual(response.status_code, 403)

    def testSchoolDeleteDenied_viewPermission_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='viewall', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_school_delete', args=(self.school1.id,)))
        self.assertEqual(response.status_code, 403)

    # School FK filtering

    def testStateFieldSucces_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        payload = {
            'name': 'School 3',
            'abbreviation': 'SCH3',
            'state': self.state1.id,
            'region': self.region1.id,
            'campus_set-TOTAL_FORMS': 0,
            'campus_set-INITIAL_FORMS': 0,
            'campus_set-MIN_NUM_FORMS': 0,
            'campus_set-MAX_NUM_FORMS': 1000,
            'schooladministrator_set-TOTAL_FORMS': 0,
            'schooladministrator_set-INITIAL_FORMS': 0,
            'schooladministrator_set-MIN_NUM_FORMS': 0,
            'schooladministrator_set-MAX_NUM_FORMS': 1000,
        }
        response = self.client.post(reverse('admin:schools_school_add'), data=payload)
        self.assertEqual(response.status_code, 302)

    def testStateFieldSucces_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'School 3',
            'abbreviation': 'SCH3',
            'state': self.state1.id,
            'region': self.region1.id,
            'campus_set-TOTAL_FORMS': 0,
            'campus_set-INITIAL_FORMS': 0,
            'campus_set-MIN_NUM_FORMS': 0,
            'campus_set-MAX_NUM_FORMS': 1000,
            'schooladministrator_set-TOTAL_FORMS': 0,
            'schooladministrator_set-INITIAL_FORMS': 0,
            'schooladministrator_set-MIN_NUM_FORMS': 0,
            'schooladministrator_set-MAX_NUM_FORMS': 1000,
        }
        response = self.client.post(reverse('admin:schools_school_add'), data=payload)
        self.assertEqual(response.status_code, 302)

    def testStateFieldDenied_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'School 3',
            'abbreviation': 'SCH3',
            'state': self.state2.id,
            'region': self.region1.id,
            'campus_set-TOTAL_FORMS': 0,
            'campus_set-INITIAL_FORMS': 0,
            'campus_set-MIN_NUM_FORMS': 0,
            'campus_set-MAX_NUM_FORMS': 1000,
            'schooladministrator_set-TOTAL_FORMS': 0,
            'schooladministrator_set-INITIAL_FORMS': 0,
            'schooladministrator_set-MIN_NUM_FORMS': 0,
            'schooladministrator_set-MAX_NUM_FORMS': 1000,
        }
        response = self.client.post(reverse('admin:schools_school_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

class TestSchoolAdministratorAdmin(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    emailsuper = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        adminSetUp(self)
        self.admin1 = SchoolAdministrator.objects.create(user=self.user1, school=self.school1)
        self.admin2 = SchoolAdministrator.objects.create(user=self.user2, school=self.school2)

    # School filtering

    def testSchoolAdministratorListLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:schools_schooladministrator_changelist'))
        self.assertEqual(response.status_code, 200)

    def testSchoolAdministratorChangeLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:schools_schooladministrator_change', args=(self.admin1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save')

    def testSchoolAdministratorListContent_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:schools_schooladministrator_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'School 1')
        self.assertContains(response, 'School 2')

    def testSchoolAdministratorDeleteLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:schools_schooladministrator_delete', args=(self.admin1.id,)))
        self.assertEqual(response.status_code, 200)

    def testSchoolAdministratorListNonStaff_denied(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_schooladministrator_changelist'))
        self.assertEqual(response.status_code, 302)

    def testSchoolAdministratorListLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_schooladministrator_changelist'))
        self.assertEqual(response.status_code, 200)

    def testSchoolAdministratorListContent_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_schooladministrator_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'School 1')
        self.assertNotContains(response, 'School 2')

    def testSchoolAdministratorChangeLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_schooladministrator_change', args=(self.admin1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save')

    def testSchoolAdministratorAddLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_schooladministrator_add'))
        self.assertEqual(response.status_code, 200)

    def testSchoolAdministratorDeleteLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_schooladministrator_delete', args=(self.admin1.id,)))
        self.assertEqual(response.status_code, 200)

    def testSchoolAdministratorChangeDenied_wrongState_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_schooladministrator_change', args=(self.admin2.id,)))
        self.assertEqual(response.status_code, 302)

    def testSchoolAdministratorViewLoads_viewonly_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='viewall', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_schooladministrator_change', args=(self.admin1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Save')

    def testSchoolAdministratorAddDenied_viewPermission_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='viewall', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_schooladministrator_add'))
        self.assertEqual(response.status_code, 403)

    def testSchoolAdministratorDeleteDenied_viewPermission_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='viewall', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:schools_schooladministrator_delete', args=(self.admin1.id,)))
        self.assertEqual(response.status_code, 403)

    # Change Post

    def testChangePostAllowed_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'user': self.user3.id,
            'school': self.school1.id,
        }
        response = self.client.post(reverse('admin:schools_schooladministrator_change', args=(self.admin1.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('admin:schools_schooladministrator_change', args=(self.admin1.id,)), data=payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'was changed successfully')

        self.admin1.refresh_from_db()
        self.assertEqual(self.admin1.user, self.user3)

    def testChangePostDenied_wrongState_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'user': self.user2.id,
            'school': self.school2.id,
        }
        response = self.client.post(reverse('admin:schools_schooladministrator_change', args=(self.admin2.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('admin:schools_schooladministrator_change', args=(self.admin2.id,)), data=payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'doesn’t exist. Perhaps it was deleted?')

    def testChangePostDenied_viewPermission_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='viewall', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'user': self.user3.id,
            'school': self.school1.id,
        }
        response = self.client.post(reverse('admin:schools_schooladministrator_change', args=(self.admin1.id,)), data=payload)
        self.assertEqual(response.status_code, 403)

    # School FK filtering

    # User field
    def testUserFieldSuccess_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        payload = {
            'user': self.user3.id,
            'school': self.school1.id,
        }
        response = self.client.post(reverse('admin:schools_schooladministrator_change', args=(self.admin1.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

    def testUserFieldSuccess_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'user': self.user3.id,
            'school': self.school1.id,
        }
        response = self.client.post(reverse('admin:schools_schooladministrator_change', args=(self.admin1.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

    def testUserFieldDenied_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'user': self.user2.id,
            'school': self.school1.id,
        }
        response = self.client.post(reverse('admin:schools_schooladministrator_change', args=(self.admin1.id,)), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

    # State field

    def testStateFieldDenied_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'user': self.user3.id,
            'school': self.school2.id,
        }
        response = self.client.post(reverse('admin:schools_schooladministrator_change', args=(self.admin1.id,)), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

