from invoices.models import InvoiceGlobalSettings, Invoice, InvoicePayment
from users.models import User
from regions.models import State, Region
from schools.models import School, SchoolAdministrator, Campus
from events.models import Event, Year, Division, AvailableDivision, Venue
from coordination.models import Coordinator
from teams.models import Team, Student, HardwarePlatform, SoftwarePlatform
from userquestions.models import Question, QuestionResponse
from association.models import AssociationMember
from workshops.models import WorkshopAttendee

import datetime

def createStates(self):
    self.state1 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='State 1', abbreviation='ST1', typeWebsite=True)
    self.state2 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='State 2', abbreviation='ST2', typeWebsite=True)

    self.region1 = Region.objects.create(name='Region 1')
    self.region2_state1 = Region.objects.create(name='Region 2', state=self.state1)
    self.region3_state2 = Region.objects.create(name='Region 3', state=self.state2)

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

    self.user_state1_super1 = User.objects.create_superuser(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email_user_state1_super1, password=self.password, homeState=self.state1)
    self.user_state1_super1_association_member = AssociationMember.objects.create(user=self.user_state1_super1, birthday=(datetime.datetime.now() + datetime.timedelta(days=-20*365)).date(), rulesAcceptedDate=datetime.datetime.now(), membershipStartDate=datetime.datetime.now())
    
    self.user_state2_super2 = User.objects.create_superuser(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email_user_state2_super2, password=self.password, homeState=self.state2)
    
    self.user_notstaff = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email_user_notstaff, password=self.password)
    self.user_notstaff_association_member = AssociationMember.objects.create(user=self.user_notstaff, birthday=(datetime.datetime.now() + datetime.timedelta(days=-20*365)).date(), rulesAcceptedDate=datetime.datetime.now(), membershipStartDate=datetime.datetime.now())
    
    self.user_state1_fullcoordinator = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email_user_state1_fullcoordinator, password=self.password, homeState=self.state1)
    self.user_state1_fullcoordinator_association_member = AssociationMember.objects.create(user=self.user_state1_fullcoordinator, birthday=(datetime.datetime.now() + datetime.timedelta(days=-20*365)).date(), rulesAcceptedDate=datetime.datetime.now(), membershipStartDate=datetime.datetime.now())
    
    self.user_state1_viewcoordinator = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email_user_state1_viewcoordinator, password=self.password, homeState=self.state1)
    self.user_state1_viewcoordinator_association_member = AssociationMember.objects.create(user=self.user_state1_viewcoordinator, birthday=(datetime.datetime.now() + datetime.timedelta(days=-20*365)).date(), rulesAcceptedDate=datetime.datetime.now(), membershipStartDate=datetime.datetime.now())
    
    self.user_state2_fullcoordinator = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email_user_state2_fullcoordinator, password=self.password, homeState=self.state2)
    self.user_state2_fullcoordinator_association_member = AssociationMember.objects.create(user=self.user_state2_fullcoordinator, birthday=(datetime.datetime.now() + datetime.timedelta(days=-20*365)).date(), rulesAcceptedDate=datetime.datetime.now(), membershipStartDate=datetime.datetime.now())

    self.user_state2_viewcoordinator = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email_user_state2_viewcoordinator, password=self.password, homeState=self.state2)
    self.user_state1_school1_mentor1 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email_user_state1_school1_mentor1, password=self.password, homeState=self.state1)
    self.user_state1_school1_mentor2 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email_user_state1_school1_mentor2, password=self.password, homeState=self.state1)
    self.user_state1_school2_mentor3 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email_user_state1_school2_mentor3, password=self.password, homeState=self.state1)
    self.user_state2_school3_mentor4 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email_user_state2_school3_mentor4, password=self.password, homeState=self.state2)
    self.user_state1_independent_mentor5 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email_user_state1_independent_mentor5, password=self.password, homeState=self.state1)

    self.coord_state1_fullcoordinator = Coordinator.objects.create(user=self.user_state1_fullcoordinator, state=self.state1, permissionLevel='full', position='Text')
    self.coord_state1_viewcoordinator = Coordinator.objects.create(user=self.user_state1_viewcoordinator, state=self.state1, permissionLevel='viewall', position='Text')
    self.coord_state2_fullcoordinator = Coordinator.objects.create(user=self.user_state2_fullcoordinator, state=self.state2, permissionLevel='full', position='Text')
    self.coord_state2_viewcoordinator = Coordinator.objects.create(user=self.user_state2_viewcoordinator, state=self.state2, permissionLevel='viewall', position='Text')

def createSchools(self):
    self.school1_state1 = School.objects.create(name='School 1', state=self.state1, region=self.region1)
    self.school2_state1 = School.objects.create(name='School 2', state=self.state1, region=self.region1)
    self.school3_state2 = School.objects.create(name='School 3', state=self.state2, region=self.region1)
    self.school4_state2 = School.objects.create(name='School 4', state=self.state2, region=self.region1)

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
    self.year = Year.objects.create(year=2021, displayEventsOnWebsite=True)
    self.invoiceSettings = InvoiceGlobalSettings.objects.create(
        invoiceFromName='From Name',
        invoiceFromDetails='Test Details Text',
        invoiceFooterMessage='Test Footer Text',
    )

    # Venues

    self.venue1_state1 = Venue.objects.create(name='Venue 1', state=self.state1)
    self.venue2_state1 = Venue.objects.create(name='Venue 2', state=self.state1)
    self.venue3_state2 = Venue.objects.create(name='Venue 3', state=self.state2)

    # Events

    self.state1_openCompetition = Event.objects.create(
        year = self.year,
        state = self.state1,
        name = 'State 1 Open Competition',
        eventType = 'competition',
        status = 'published',
        competition_defaultEntryFee = 50,
        startDate = (datetime.datetime.now() + datetime.timedelta(days=15)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=15)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date(),
        directEnquiriesTo = self.user_state1_super1,
        venue=self.venue1_state1,
    )

    self.state1_openWorkshop = Event.objects.create(
        year = self.year,
        state = self.state1,
        name = 'State 1 Open Workshop',
        eventType = 'workshop',
        status = 'published',
        competition_defaultEntryFee = 50,
        startDate = (datetime.datetime.now() + datetime.timedelta(days=3)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=3)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date(),
        directEnquiriesTo = self.user_state1_super1,
        venue=self.venue1_state1,
    )

    self.state1_closedCompetition1 = Event.objects.create(
        year = self.year,
        state = self.state1,
        name = 'State 1 Closed Competition 1',
        eventType = 'competition',
        status = 'published',
        competition_defaultEntryFee = 50,
        startDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-2)).date(),
        directEnquiriesTo = self.user_state1_super1,
        venue=self.venue1_state1,
    )

    self.state1_closedCompetition2 = Event.objects.create(
        year = self.year,
        state = self.state1,
        name = 'State 1 Closed Competition 2',
        eventType = 'competition',
        status = 'published',
        competition_defaultEntryFee = 50,
        startDate = (datetime.datetime.now() + datetime.timedelta(days=6)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=6)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
        directEnquiriesTo = self.user_state1_super1,
        venue=self.venue2_state1,
    )

    self.state1_pastCompetition = Event.objects.create(
        year = self.year,
        state = self.state1,
        name = 'State 1 Past Competition',
        eventType = 'competition',
        status = 'published',
        competition_defaultEntryFee = 50,
        startDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-9)).date(),
        directEnquiriesTo = self.user_state1_super1,
        venue=self.venue1_state1,
    )

    self.state2_openCompetition = Event.objects.create(
        year = self.year,
        state = self.state2,
        name = 'State 2 Open Competition',
        eventType = 'competition',
        status = 'published',
        competition_defaultEntryFee = 50,
        startDate = (datetime.datetime.now() + datetime.timedelta(days=20)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=20)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=10)).date(),
        directEnquiriesTo = self.user_state2_super2,
        venue=self.venue3_state2,
    )

    self.state2_openWorkshop = Event.objects.create(
        year = self.year,
        state = self.state2,
        name = 'State 2 Open Workshop',
        eventType = 'workshop',
        status = 'published',
        competition_defaultEntryFee = 50,
        startDate = (datetime.datetime.now() + datetime.timedelta(days=3)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=3)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date(),
        directEnquiriesTo = self.user_state1_super1,
        venue=self.venue3_state2,
    )

    # Divisions

    self.division1_state1 = Division.objects.create(name='Division 1', state=self.state1)
    self.division2_state2 = Division.objects.create(name='Division 2', state=self.state2)
    self.division3 = Division.objects.create(name='Division 3')
    self.division4 = Division.objects.create(name='Division 4')
    self.division5 = Division.objects.create(name='Division 5', active=False)

    # Available Divisions

    for event in ['state1_openCompetition', 'state1_openWorkshop', 'state1_closedCompetition1', 'state1_closedCompetition2', 'state1_pastCompetition', 'state2_openCompetition', 'state2_openWorkshop']:
        setattr(self, f'availableDivision3_{event}', AvailableDivision.objects.create(event=getattr(self, event), division=self.division3))
        setattr(self, f'availableDivision4_{event}', AvailableDivision.objects.create(event=getattr(self, event), division=self.division4))

def createTeams(self):
    self.hardwarePlatform = HardwarePlatform.objects.create(name='HW 1')
    self.softwarePlatform = SoftwarePlatform.objects.create(name='HW 1')

    self.state1_event1_team1 = Team.objects.create(
        event=self.state1_openCompetition,
        division=self.division3,
        mentorUser=self.user_state1_school1_mentor1,
        school=self.school1_state1,
        name='Team 1',
        hardwarePlatform=self.hardwarePlatform,
        softwarePlatform=self.softwarePlatform,
    )
    self.state1_event1_team2 = Team.objects.create(
        event=self.state1_openCompetition,
        division=self.division3,
        mentorUser=self.user_state1_school1_mentor1,
        school=self.school1_state1,
        name='Team 2',
        hardwarePlatform=self.hardwarePlatform,
        softwarePlatform=self.softwarePlatform,
    )
    self.state2_event1_team3 = Team.objects.create(
        event=self.state2_openCompetition,
        division=self.division3,
        mentorUser=self.user_state1_school1_mentor1,
        school=self.school1_state1,
        name='Team 3',
        hardwarePlatform=self.hardwarePlatform,
        softwarePlatform=self.softwarePlatform,
    )

def createWorkshopAttendees(self):
    self.state1_event1_workshopAttendee1 = WorkshopAttendee.objects.create(
        event=self.state1_openWorkshop,
        mentorUser=self.user_state1_school1_mentor1,
        school=self.school1_state1,
        division=self.division3,
        firstName='First 1',
        lastName='Last 1',
        yearLevel=10,
        attendeeType='student',
        gender='male,'
    )
    self.state1_event1_workshopAttendee2 = WorkshopAttendee.objects.create(
        event=self.state1_openWorkshop,
        mentorUser=self.user_state1_school1_mentor1,
        school=self.school1_state1,
        division=self.division3,
        firstName='First 2',
        lastName='Last 2',
        yearLevel=11,
        attendeeType='student',
        gender='male',
    )
    self.state2_event1_workshopAttendee3 = WorkshopAttendee.objects.create(
        event=self.state2_openWorkshop,
        mentorUser=self.user_state1_school1_mentor1,
        school=self.school1_state1,
        division=self.division3,
        firstName='First 3',
        lastName='Last 3',
        yearLevel=11,
        attendeeType='student',
        gender='male',
    )

def createInvoices(self):
    self.state1_event1_invoice1 = Invoice.objects.create(
        invoiceToUser=self.user_state1_school1_mentor1,
        school=self.school1_state1,
        event=self.state1_openCompetition
    )
    self.state2_event1_invoice2 = Invoice.objects.create(
        invoiceToUser=self.user_state1_school1_mentor1,
        school=self.school1_state1,
        event=self.state2_openCompetition
    )

    self.state1_workshopEvent1_invoice1 = Invoice.objects.create(
        invoiceToUser=self.user_state1_school1_mentor1,
        school=self.school1_state1,
        event=self.state1_openWorkshop
    )
    self.state2_workshopEvent1_invoice2 = Invoice.objects.create(
        invoiceToUser=self.user_state1_school1_mentor1,
        school=self.school1_state1,
        event=self.state2_openWorkshop
    )

def createQuestionsAndResponses(self):
    self.question1 = Question.objects.create(
        shortTitle='Consent',
        questionText='Do you consent to the terms and conditions?',
        required=False,
    )
    self.questionResponse1 = QuestionResponse.objects.create(
        question=self.question1,
        user=self.user_state1_school1_mentor1,
        response=True,
    )

    self.question2 = Question.objects.create(
        shortTitle='Marketing',
        questionText='Do you consent to receive marketing communications?',
        required=False,
    )
    self.questionResponse1 = QuestionResponse.objects.create(
        question=self.question2,
        user=self.user_state1_school1_mentor1,
        response=False,
    )

def createAssociationMemberships(self):
    self.state1_associationMember1 = AssociationMember.objects.create(
        user=self.user_state1_school1_mentor1,
        birthday=(datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        rulesAcceptedDate=datetime.datetime.now(),
        membershipStartDate=datetime.datetime.now(),
    )

    self.state1_associationMember2 = AssociationMember.objects.create(
        user=self.user_state1_school1_mentor2,
        birthday=(datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        rulesAcceptedDate=datetime.datetime.now(),
        membershipStartDate=datetime.datetime.now(),
    )

    self.state2_associationMember3 = AssociationMember.objects.create(
        user=self.user_state2_school3_mentor4,
        birthday=(datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        rulesAcceptedDate=datetime.datetime.now(),
        membershipStartDate=datetime.datetime.now(),
    )
