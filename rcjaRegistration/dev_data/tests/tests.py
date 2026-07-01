from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.http import HttpRequest

import json

from regions.models import State, Region
from schools.models import School, SchoolAdministrator
from teams.models import Team, Student
from events.models import (
    DivisionCategory,
    Division,
    AvailableDivision,
    Event,
    BaseEventAttendance,
    Year,
    Venue,
)
from users.models import User
from coordination.models import Coordinator
from eventfiles.models import EventAvailableFileType
from workshops.models import WorkshopAttendee
from eventfiles.models import (
    EventAvailableFileType,
    MentorEventFileUpload,
)

from invoices.models import InvoiceGlobalSettings, Invoice, InvoicePayment
from regions.models import State, Region
from teams.models import (
    Team,
    Student,
    PlatformCategory,
    HardwarePlatform,
    SoftwarePlatform,
    Team,
)
from association.models import AssociationMember
from schools.models import Campus, School, SchoolAdministrator
from userquestions.models import Question, QuestionResponse

from django.conf import settings

import datetime


def commonSetUp(obj):
    now = datetime.datetime(2019, 6, 27, 6, 4, 50, 358)
    obj.username = "user@user.com"
    obj.password = "password"
    obj.user = User.objects.create_user(
        adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION,
        email=obj.username,
        password=obj.password,
    )
    obj.super = "admin@user.com"
    obj.superUser = User.objects.create_user(
        adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION,
        email=obj.super,
        password=obj.password,
        is_superuser=True,
        is_staff=True,
    )
    obj.newState = State.objects.create(
        typeCompetition=True,
        typeUserRegistration=True,
        name="Victoria",
        abbreviation="VIC",
    )
    obj.state2 = State.objects.create(
        typeCompetition=True,
        typeUserRegistration=True,
        name="New South Wales",
        abbreviation="NSW",
    )
    obj.globalState = State.objects.create(
        typeCompetition=True,
        typeUserRegistration=True,
        typeGlobal=True,
        name="National",
        abbreviation="NAT",
    )
    obj.newRegion = Region.objects.create(name="Test Region", description="test desc")
    obj.newSchool = School.objects.create(
        name="Melbourne High", state=obj.newState, region=obj.newRegion
    )
    obj.schoolAdministrator = SchoolAdministrator.objects.create(
        school=obj.newSchool, user=obj.user
    )
    obj.year = Year.objects.create(year=2019)
    obj.division_cat = DivisionCategory.objects.create(name="Test")
    obj.division = Division.objects.create(name="test", category=obj.division_cat)
    obj.division2 = Division.objects.create(
        name="second", category=obj.division_cat, state=obj.state2
    )

    obj.oldEvent = Event.objects.create(
        year=obj.year,
        state=obj.newState,
        name="test old not reg",
        eventType="competition",
        status="published",
        maxMembersPerTeam=5,
        competition_defaultEntryFee=4,
        startDate=(now + datetime.timedelta(days=-1)).date(),
        endDate=(now + datetime.timedelta(days=-1)).date(),
        registrationsOpenDate=(now + datetime.timedelta(days=-1)).date(),
        registrationsCloseDate=(now + datetime.timedelta(days=-1)).date(),
        directEnquiriesTo=obj.user,
    )
    obj.oldEvent.divisions.add(obj.division)

    obj.registrationNotOpenYetEvent = Event.objects.create(
        year=obj.year,
        state=obj.newState,
        name="future event",
        eventType="competition",
        status="published",
        maxMembersPerTeam=5,
        competition_defaultEntryFee=4,
        startDate=(now + datetime.timedelta(days=10)).date(),
        endDate=(now + datetime.timedelta(days=10)).date(),
        registrationsOpenDate=(now + datetime.timedelta(days=1)).date(),
        registrationsCloseDate=(now + datetime.timedelta(days=-5)).date(),
        directEnquiriesTo=obj.user,
    )
    obj.registrationNotOpenYetEvent.divisions.add(obj.division)

    obj.newEvent = Event.objects.create(
        year=obj.year,
        state=obj.newState,
        name="test new yes reg",
        eventType="competition",
        status="published",
        maxMembersPerTeam=5,
        competition_defaultEntryFee=4,
        startDate=(now + datetime.timedelta(days=3)).date(),
        endDate=(now + datetime.timedelta(days=4)).date(),
        registrationsOpenDate=(now + datetime.timedelta(days=-2)).date(),
        registrationsCloseDate=(now + datetime.timedelta(days=+2)).date(),
        directEnquiriesTo=obj.user,
    )
    obj.newEvent.divisions.add(obj.division)

    obj.oldEventWithTeams = Event.objects.create(
        year=obj.year,
        state=obj.newState,
        name="test old yes reg",
        eventType="competition",
        status="published",
        maxMembersPerTeam=5,
        competition_defaultEntryFee=4,
        startDate=(now + datetime.timedelta(days=-3)).date(),
        endDate=(now + datetime.timedelta(days=-4)).date(),
        registrationsOpenDate=(now + datetime.timedelta(days=-6)).date(),
        registrationsCloseDate=(now + datetime.timedelta(days=-5)).date(),
        directEnquiriesTo=obj.user,
    )
    obj.oldEventWithTeams.divisions.add(obj.division)
    obj.oldeventTeam = Team.objects.create(
        event=obj.oldEventWithTeams,
        division=obj.division,
        school=obj.newSchool,
        mentorUser=obj.user,
        name="test",
    )
    obj.oldTeamStudent = Student.objects.create(
        team=obj.oldeventTeam,
        firstName="test",
        lastName="old",
        yearLevel=1,
        gender="male",
    )

    obj.newEventTeam = Team.objects.create(
        event=obj.newEvent,
        division=obj.division,
        school=obj.newSchool,
        mentorUser=obj.user,
        name="test new team",
    )
    obj.newTeamStudent = Student.objects.create(
        team=obj.newEventTeam,
        firstName="test",
        lastName="new",
        yearLevel=1,
        gender="male",
    )

    obj.invoiceSettings = InvoiceGlobalSettings.objects.create(
        invoiceFromName="From Name",
        invoiceFromDetails="Test Details Text",
        invoiceFooterMessage="Test Footer Text",
    )


class TestDownload(TestCase):
    def testUnloggedInPermission(self):
        commonSetUp(self)
        response = self.client.get(reverse("data:download"))
        self.assertEqual(response.status_code, 302)

    def testAdminPermission(self):
        commonSetUp(self)
        self.client.login(
            request=HttpRequest(), username=self.super, password=self.password
        )
        response = self.client.get(reverse("data:download"))
        self.assertEqual(response.status_code, 200)

    def testUserPermission(self):
        commonSetUp(self)
        self.client.login(
            request=HttpRequest(), username=self.username, password=self.password
        )
        response = self.client.get(reverse("data:download"))
        self.assertEqual(response.status_code, 403)

    def testCorrectJSON(self):
        commonSetUp(self)
        self.client.login(
            request=HttpRequest(), username=self.super, password=self.password
        )
        response = self.client.get(reverse("data:download"))

        response = self.client.get(reverse("data:download"))
        with open("dev_data/tests/main.txt", "r") as file:
            regex = file.read(-1)
        self.assertRegex(str(response.json()), regex)


class TestUpload(TestCase):
    def setUp(self):
        commonSetUp(self)
        settings.ENVIRONMENT = "development"

    def close(self):
        settings.ENVIRONMENT = "testing"
        settings.DEBUG = False

    def testUnloggedInPermission(self):
        response = self.client.get(reverse("data:upload"))
        self.assertEqual(response.status_code, 302)
        self.close()

    def testAdminPermission(self):
        settings.DEBUG = True
        self.client.login(
            request=HttpRequest(), username=self.super, password=self.password
        )
        response = self.client.get(reverse("data:upload"))
        self.assertEqual(response.status_code, 200)
        self.close()

    def testAdminPermissionNotInDevelopment(self):
        settings.ENVIRONMENT = "production"
        self.client.login(
            request=HttpRequest(), username=self.super, password=self.password
        )
        response = self.client.get(reverse("data:upload"))
        self.assertEqual(response.status_code, 404)
        self.close()

    def testUserPermission(self):
        self.client.login(
            request=HttpRequest(), username=self.username, password=self.password
        )
        response = self.client.get(reverse("data:upload"))
        self.assertEqual(response.status_code, 404)
        self.close()

    def testDeleteAll(self):
        settings.DEBUG = True
        self.client.login(
            request=HttpRequest(), username=self.super, password=self.password
        )
        url = reverse("data:upload")

        data = {"deleteData": True, "data_to_upload": {}}
        self.client.post(url, data=data)

        self.assertEqual(InvoiceGlobalSettings.objects.count(), 0)
        self.assertEqual(Year.objects.count(), 0)
        self.assertEqual(State.objects.count(), 0)
        self.assertEqual(Region.objects.count(), 0)
        self.assertEqual(School.objects.count(), 0)
        self.assertEqual(Campus.objects.count(), 0)
        self.assertEqual(Venue.objects.count(), 0)
        self.assertEqual(DivisionCategory.objects.count(), 0)
        self.assertEqual(Division.objects.count(), 0)
        self.assertEqual(PlatformCategory.objects.count(), 0)
        self.assertEqual(HardwarePlatform.objects.count(), 0)
        self.assertEqual(SoftwarePlatform.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(SchoolAdministrator.objects.count(), 0)
        self.assertEqual(AssociationMember.objects.count(), 0)
        self.assertEqual(Coordinator.objects.count(), 0)
        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(QuestionResponse.objects.count(), 0)
        self.assertEqual(Event.objects.count(), 0)
        self.assertEqual(AvailableDivision.objects.count(), 0)
        self.assertEqual(BaseEventAttendance.objects.count(), 0)
        self.assertEqual(Invoice.objects.count(), 0)
        self.assertEqual(MentorEventFileUpload.objects.count(), 0)
        self.assertEqual(EventAvailableFileType.objects.count(), 0)
        self.assertEqual(InvoicePayment.objects.count(), 0)
        self.assertEqual(WorkshopAttendee.objects.count(), 0)
        self.assertEqual(Team.objects.count(), 0)
        self.assertEqual(Student.objects.count(), 0)
        self.close()

    def testRecreateAll(self):
        settings.DEBUG = True
        self.client.login(
            request=HttpRequest(), username=self.super, password=self.password
        )
        url = reverse("data:upload")

        with open("dev_data/tests/main.json", "r") as file:
            data = file.read(-1)
            data = data.replace("TODAYDATE", f'"{datetime.date.today()}"')
            loadedJSON = json.loads(data)
        data = {"deleteData": True, "data_to_upload": loadedJSON}
        self.client.post(url, data=data)

        response = self.client.get(reverse("data:download"))
        with open("dev_data/tests/main.txt", "r") as file:
            regex = file.read(-1)
        self.assertRegex(str(response.json()), regex)
        self.close()
