from invoices.models import InvoiceGlobalSettings, Invoice, InvoicePayment
from users.models import User
from regions.models import State, Region
from schools.models import School, SchoolAdministrator, Campus
from events.models import Event, Year, Division, AvailableDivision
from coordination.models import Coordinator
from teams.models import Team, Student, HardwarePlatform, SoftwarePlatform

import datetime

def createStates(self):
    self.state1 = State.objects.create(typeRegistration=True, name='State 1', abbreviation='ST1')
    self.state2 = State.objects.create(typeRegistration=True, name='State 2', abbreviation='ST2')

    self.region1 = Region.objects.create(name='Region 1', description='test desc')

def createUsers(self):
    self.email_user_state1_super1 = 'super1@user.com'
    self.email_user_state2_super2 = 'super2@user.com'
    self.email_user_notstaff = 'user1@user.com'
    self.email_user_state1_fullcoordinator = 'user2@user.com'
    self.email_user_state1_viewcoordinator = 'user3@user.com'
    self.email_user_state2_fullcoordinator = 'user4@user.com'
    self.email_user_state2_viewcoordinator = 'user5@user.com'
    self.email_user_state1_school1_mentor1 = 'user6@user.com'
    self.email_user_state1_school1_mentor2 = 'user7@user.com'
    self.email_user_state1_school2_mentor3 = 'user8@user.com'
    self.email_user_state2_school3_mentor4 = 'user9@user.com'
    self.email_user_state1_independent_mentor5 = 'user10@user.com'
    self.password = 'chdj48958DJFHJGKDFNM' # Complex random password so passes validation tests

    self.user_state1_super1 = User.objects.create_superuser(email=self.email_user_state1_super1, password=self.password, homeState=self.state1)
    self.user_state2_super2 = User.objects.create_superuser(email=self.email_user_state2_super2, password=self.password, homeState=self.state2)
    self.user_notstaff = User.objects.create_user(email=self.email_user_notstaff, password=self.password)
    self.user_state1_fullcoordinator = User.objects.create_user(email=self.email_user_state1_fullcoordinator, password=self.password, homeState=self.state1)
    self.user_state1_viewcoordinator = User.objects.create_user(email=self.email_user_state1_viewcoordinator, password=self.password, homeState=self.state1)
    self.user_state2_fullcoordinator = User.objects.create_user(email=self.email_user_state2_fullcoordinator, password=self.password, homeState=self.state2)
    self.user_state2_viewcoordinator = User.objects.create_user(email=self.email_user_state2_viewcoordinator, password=self.password, homeState=self.state2)
    self.user_state1_school1_mentor1 = User.objects.create_user(email=self.email_user_state1_school1_mentor1, password=self.password, homeState=self.state1)
    self.user_state1_school1_mentor2 = User.objects.create_user(email=self.email_user_state1_school1_mentor2, password=self.password, homeState=self.state1)
    self.user_state1_school2_mentor3 = User.objects.create_user(email=self.email_user_state1_school2_mentor3, password=self.password, homeState=self.state1)
    self.user_state2_school3_mentor4 = User.objects.create_user(email=self.email_user_state2_school3_mentor4, password=self.password, homeState=self.state2)
    self.user_state1_independent_mentor5 = User.objects.create_user(email=self.email_user_state1_independent_mentor5, password=self.password, homeState=self.state1)

    self.coord_state1_fullcoordinator = Coordinator.objects.create(user=self.user_state1_fullcoordinator, state=self.state1, permissions='full', position='Text')
    self.coord_state1_viewcoordinator = Coordinator.objects.create(user=self.user_state1_viewcoordinator, state=self.state1, permissions='viewall', position='Text')
    self.coord_state2_fullcoordinator = Coordinator.objects.create(user=self.user_state2_fullcoordinator, state=self.state2, permissions='full', position='Text')
    self.coord_state2_viewcoordinator = Coordinator.objects.create(user=self.user_state2_viewcoordinator, state=self.state2, permissions='viewall', position='Text')

def createSchools(self):
    self.school1_state1 = School.objects.create(name='School 1', abbreviation='sch1', state=self.state1, region=self.region1)
    self.school2_state1 = School.objects.create(name='School 2', abbreviation='sch2', state=self.state1, region=self.region1)
    self.school3_state2 = School.objects.create(name='School 3', abbreviation='sch3', state=self.state2, region=self.region1)
    self.school4_state2 = School.objects.create(name='School 4', abbreviation='sch4', state=self.state2, region=self.region1)

    self.campus1_school1 = Campus.objects.create(school=self.school1_state1, name='Campus 1')
    self.campus2_school1 = Campus.objects.create(school=self.school1_state1, name='Campus 2')
    self.campus3_school2 = Campus.objects.create(school=self.school2_state1, name='Campus 3')
    self.campus4_school2 = Campus.objects.create(school=self.school2_state1, name='Campus 4')
    self.campus5_school3 = Campus.objects.create(school=self.school3_state2, name='Campus 5')

    self.schooladmin_mentor1 = SchoolAdministrator.objects.create(school=self.school1_state1, campus=self.campus1_school1, user=self.user_state1_school1_mentor1)
    self.schooladmin_mentor2 = SchoolAdministrator.objects.create(school=self.school1_state1, campus=self.campus2_school1, user=self.user_state1_school1_mentor2)
    self.schooladmin_mentor3 = SchoolAdministrator.objects.create(school=self.school2_state1, user=self.user_state1_school2_mentor3)
    self.schooladmin_mentor4 = SchoolAdministrator.objects.create(school=self.school3_state2, user=self.user_state2_school3_mentor4)

def createEvents(self):
    self.year = Year.objects.create(year=2020)
    self.invoiceSettings = InvoiceGlobalSettings.objects.create(
        invoiceFromName='From Name',
        invoiceFromDetails='Test Details Text',
        invoiceFooterMessage='Test Footer Text',
    )

    self.eventOpen_state1 = Event.objects.create(
        year=self.year,
        state=self.state1,
        name='Test event 1',
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        entryFeeIncludesGST=True,
        event_billingType='team',
        event_defaultEntryFee = 50,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date(),
        directEnquiriesTo = self.user1,
    )
    self.division1 = Division.objects.create(name='Division 1')
    self.division2 = Division.objects.create(name='Division 2')
    self.division3 = Division.objects.create(name='Division 3')
    self.division4 = Division.objects.create(name='Division 4', state=self.state2)


