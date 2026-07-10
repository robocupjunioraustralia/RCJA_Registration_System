from django.test import TestCase
from django.urls import reverse
from django.http import HttpRequest
from django.core.files.uploadedfile import SimpleUploadedFile

from unittest.mock import patch

from eventfiles.models import (
    EventAvailableFileType,
    MentorEventFileType,
    MentorEventFileUpload,
)
from teams.models import Team
from users.models import User
from regions.models import State, Region
from schools.models import School, SchoolAdministrator
from events.models import Event, Year, Division, AvailableDivision

import datetime

# Create your tests here.


def commonSetUp(obj):  # copied from events, todo refactor
    obj.username = "user@user.com"
    obj.password = "password"
    obj.user = User.objects.create_user(
        adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION,
        email=obj.username,
        password=obj.password,
    )

    obj.super = "admin@user.com"
    obj.password = "password"
    obj.admin = User.objects.create_user(
        adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION,
        email=obj.super,
        password=obj.password,
        is_superuser=True,
    )

    obj.newState = State.objects.create(
        typeCompetition=True,
        typeUserRegistration=True,
        name="Victoria",
        abbreviation="VIC",
    )
    obj.newRegion = Region.objects.create(name="Test Region", description="test desc")
    obj.newSchool = School.objects.create(
        name="Melbourne High", state=obj.newState, region=obj.newRegion
    )
    obj.schoolAdministrator = SchoolAdministrator.objects.create(
        school=obj.newSchool, user=obj.user
    )
    obj.year = Year.objects.create(year=2019)
    obj.division = Division.objects.create(name="Division 1 Name")

    obj.afterEvent = Event.objects.create(
        year=obj.year,
        state=obj.newState,
        name="test old not reg",
        eventType="competition",
        status="published",
        maxMembersPerTeam=5,
        competition_defaultEntryFee=4,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
        endDate=(datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
        registrationsOpenDate=(
            datetime.datetime.now() + datetime.timedelta(days=-1)
        ).date(),
        registrationsCloseDate=(
            datetime.datetime.now() + datetime.timedelta(days=-1)
        ).date(),
        directEnquiriesTo=obj.user,
    )
    obj.afterEventDivision = AvailableDivision.objects.create(
        division=obj.division, event=obj.afterEvent
    )
    obj.fileType1 = MentorEventFileType.objects.create(name="File Type 1")
    obj.availableFileafterEvent = EventAvailableFileType.objects.create(
        event=obj.afterEvent,
        fileType=obj.fileType1,
        uploadDeadline=(datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
    )
    obj.afterEventTeam = Team.objects.create(
        event=obj.afterEvent,
        division=obj.division,
        school=obj.newSchool,
        mentorUser=obj.user,
        name="test",
    )

    obj.beforeDueEvent = Event.objects.create(
        year=obj.year,
        state=obj.newState,
        name="test new not reg",
        eventType="competition",
        status="published",
        maxMembersPerTeam=2,
        competition_defaultEntryFee=4,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=3)).date(),
        endDate=(datetime.datetime.now() + datetime.timedelta(days=4)).date(),
        registrationsOpenDate=(
            datetime.datetime.now() + datetime.timedelta(days=-2)
        ).date(),
        registrationsCloseDate=(
            datetime.datetime.now() + datetime.timedelta(days=+2)
        ).date(),
        directEnquiriesTo=obj.user,
    )
    obj.beforeDueAvailableDivision = AvailableDivision.objects.create(
        division=obj.division, event=obj.beforeDueEvent
    )
    obj.availableFilebeforeDue = EventAvailableFileType.objects.create(
        event=obj.beforeDueEvent,
        fileType=obj.fileType1,
        uploadDeadline=(datetime.datetime.now() + datetime.timedelta(days=2)).date(),
    )
    obj.beforeDueTeam = Team.objects.create(
        event=obj.beforeDueEvent,
        division=obj.division,
        school=obj.newSchool,
        mentorUser=obj.user,
        name="test new team",
    )

    obj.afterDueEvent = Event.objects.create(
        year=obj.year,
        state=obj.newState,
        name="test old yes reg",
        eventType="competition",
        status="published",
        maxMembersPerTeam=5,
        competition_defaultEntryFee=4,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=3)).date(),
        endDate=(datetime.datetime.now() + datetime.timedelta(days=4)).date(),
        registrationsOpenDate=(
            datetime.datetime.now() + datetime.timedelta(days=-6)
        ).date(),
        registrationsCloseDate=(
            datetime.datetime.now() + datetime.timedelta(days=-5)
        ).date(),
        directEnquiriesTo=obj.user,
    )
    obj.afterDueEvent.divisions.add(obj.division)
    obj.availableFileafterDue = EventAvailableFileType.objects.create(
        event=obj.afterDueEvent,
        fileType=obj.fileType1,
        uploadDeadline=(datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
    )
    obj.afterDueTeam = Team.objects.create(
        event=obj.afterDueEvent,
        division=obj.division,
        school=obj.newSchool,
        mentorUser=obj.user,
        name="test new team",
    )


class TestFileUpload(TestCase):
    def setUp(self):
        commonSetUp(self)

    @patch("storages.backends.s3boto3.S3Boto3Storage.size", return_value=1)
    @patch("storages.backends.s3boto3.S3Boto3Storage.save", return_value="fileName.ext")
    def testBeforeDueMentor(self, mock_size, mock_save):
        self.client.login(
            request=HttpRequest(), username=self.username, password=self.password
        )
        response = self.client.get(
            reverse("teams:details", kwargs={"teamID": self.beforeDueTeam.pk})
        )
        self.assertContains(response, "Upload a new file")

        file = SimpleUploadedFile(
            "something.txt", b"file_content", content_type="text/plain"
        )
        payload = {"fileUpload": file, "fileType": self.fileType1.pk}
        response = self.client.post(
            reverse(
                "eventfiles:uploadFile",
                kwargs={"eventAttendanceID": self.beforeDueTeam.pk},
            ),
            data=payload,
            follow=False,
        )
        self.assertEqual(response.status_code, 302)
        try:
            file = MentorEventFileUpload.objects.get(eventAttendance=self.beforeDueTeam)
        except MentorEventFileUpload.DoesNotExist as E:
            self.fail("Didn't add file")
        self.assertEqual(file.uploadedBy, self.user)
        self.assertEqual(file.fileType, self.fileType1)

    @patch("storages.backends.s3boto3.S3Boto3Storage.size", return_value=1)
    @patch("storages.backends.s3boto3.S3Boto3Storage.save", return_value="fileName.ext")
    def testAfterDueMentor(self, mock_size, mock_save):
        self.client.login(
            request=HttpRequest(), username=self.username, password=self.password
        )
        response = self.client.get(
            reverse("teams:details", kwargs={"teamID": self.afterDueTeam.pk})
        )
        self.assertNotContains(response, "Upload a new file")

        file = SimpleUploadedFile(
            "something.txt", b"file_content", content_type="text/plain"
        )
        payload = {"fileUpload": file, "fileType": self.fileType1.pk}
        response = self.client.post(
            reverse(
                "eventfiles:uploadFile",
                kwargs={"eventAttendanceID": self.afterDueTeam.pk},
            ),
            data=payload,
            follow=False,
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            0,
            MentorEventFileUpload.objects.filter(
                eventAttendance=self.afterDueTeam
            ).count(),
        )

    @patch("storages.backends.s3boto3.S3Boto3Storage.size", return_value=1)
    @patch("storages.backends.s3boto3.S3Boto3Storage.save", return_value="fileName.ext")
    def testBeforeDueCoordinator(self, mock_size, mock_save):
        self.client.login(
            request=HttpRequest(), username=self.super, password=self.password
        )
        response = self.client.get(
            reverse("teams:details", kwargs={"teamID": self.beforeDueTeam.pk})
        )
        self.assertContains(response, "Upload a new file")

        file = SimpleUploadedFile(
            "something.txt", b"file_content", content_type="text/plain"
        )
        payload = {"fileUpload": file, "fileType": self.fileType1.pk}
        response = self.client.post(
            reverse(
                "eventfiles:uploadFile",
                kwargs={"eventAttendanceID": self.beforeDueTeam.pk},
            ),
            data=payload,
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        try:
            file = MentorEventFileUpload.objects.get(eventAttendance=self.beforeDueTeam)
        except MentorEventFileUpload.DoesNotExist as E:
            self.fail("Didn't add file")
        self.assertEqual(file.uploadedBy, self.admin)
        self.assertEqual(file.fileType, self.fileType1)

    @patch("storages.backends.s3boto3.S3Boto3Storage.size", return_value=1)
    @patch("storages.backends.s3boto3.S3Boto3Storage.save", return_value="fileName.ext")
    def testAfterDueCoordinator(self, mock_size, mock_save):
        self.client.login(
            request=HttpRequest(), username=self.super, password=self.password
        )
        response = self.client.get(
            reverse("teams:details", kwargs={"teamID": self.afterDueTeam.pk})
        )
        self.assertContains(response, "Upload a new file")

        file = SimpleUploadedFile(
            "something.txt", b"file_content", content_type="text/plain"
        )
        payload = {"fileUpload": file, "fileType": self.fileType1.pk}
        response = self.client.post(
            reverse(
                "eventfiles:uploadFile",
                kwargs={"eventAttendanceID": self.afterDueTeam.pk},
            ),
            data=payload,
            follow=False,
        )
        self.assertEqual(response.status_code, 302)
        try:
            file = MentorEventFileUpload.objects.get(eventAttendance=self.afterDueTeam)
        except MentorEventFileUpload.DoesNotExist as E:
            self.fail("Didn't add file")
        self.assertEqual(file.uploadedBy, self.admin)
        self.assertEqual(file.fileType, self.fileType1)

    @patch("storages.backends.s3boto3.S3Boto3Storage.size", return_value=1)
    @patch("storages.backends.s3boto3.S3Boto3Storage.save", return_value="fileName.ext")
    def testAfterEventCoordinator(self, mock_size, mock_save):
        self.client.login(
            request=HttpRequest(), username=self.super, password=self.password
        )
        response = self.client.get(
            reverse("teams:details", kwargs={"teamID": self.afterEventTeam.pk})
        )
        self.assertNotContains(response, "Upload a new file")

        file = SimpleUploadedFile(
            "something.txt", b"file_content", content_type="text/plain"
        )
        payload = {"fileUpload": file, "fileType": self.fileType1.pk}
        response = self.client.post(
            reverse(
                "eventfiles:uploadFile",
                kwargs={"eventAttendanceID": self.afterEventTeam.pk},
            ),
            data=payload,
            follow=False,
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            0,
            MentorEventFileUpload.objects.filter(
                eventAttendance=self.afterDueTeam
            ).count(),
        )


class TestFileDeletion(TestCase):
    def setUp(self):
        commonSetUp(self)

    @patch("storages.backends.s3boto3.S3Boto3Storage.size", return_value=1)
    @patch(
        "storages.backends.s3boto3.S3Boto3Storage.save", return_value="something.txt"
    )
    @patch("storages.backends.s3boto3.S3Boto3Storage.delete")
    def testBeforeDueMentor(self, mock_size, mock_save, mock_delete):
        file = SimpleUploadedFile(
            "something.txt", b"file_content", content_type="text/plain"
        )
        upload = MentorEventFileUpload.objects.create(
            eventAttendance=self.beforeDueTeam,
            uploadedBy=self.user,
            fileType=self.fileType1,
            fileUpload=file,
            originalFilename="something.txt",
        )
        self.client.login(
            request=HttpRequest(), username=self.username, password=self.password
        )
        response = self.client.get(
            reverse("teams:details", kwargs={"teamID": self.beforeDueTeam.pk})
        )
        self.assertContains(response, "Delete</button>")
        response = self.client.delete(
            reverse(
                "eventfiles:edit",
                kwargs={"uploadedFileID": upload.pk},
            ),
            data={},
            follow=False,
        )
        self.assertEqual(
            MentorEventFileUpload.objects.filter(
                eventAttendance=self.beforeDueTeam
            ).count(),
            0,
        )

    @patch("storages.backends.s3boto3.S3Boto3Storage.size", return_value=1)
    @patch("storages.backends.s3boto3.S3Boto3Storage.save", return_value="fileName.ext")
    @patch("storages.backends.s3boto3.S3Boto3Storage.delete")
    def testAfterDueMentor(self, mock_size, mock_save, mock_delete):
        file = SimpleUploadedFile(
            "something.txt", b"file_content", content_type="text/plain"
        )
        upload = MentorEventFileUpload.objects.create(
            eventAttendance=self.afterDueTeam,
            uploadedBy=self.user,
            fileType=self.fileType1,
            fileUpload=file,
            originalFilename="something.txt",
        )
        self.client.login(
            request=HttpRequest(), username=self.username, password=self.password
        )
        response = self.client.get(
            reverse("teams:details", kwargs={"teamID": self.afterDueTeam.pk})
        )
        self.assertNotContains(response, "Delete</button>")
        response = self.client.delete(
            reverse(
                "eventfiles:edit",
                kwargs={"uploadedFileID": upload.pk},
            ),
            data={},
            follow=False,
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            1,
            MentorEventFileUpload.objects.filter(
                eventAttendance=self.afterDueTeam
            ).count(),
        )

    @patch("storages.backends.s3boto3.S3Boto3Storage.size", return_value=1)
    @patch("storages.backends.s3boto3.S3Boto3Storage.save", return_value="fileName.ext")
    @patch("storages.backends.s3boto3.S3Boto3Storage.delete")
    def testBeforeDueCoordinator(self, mock_size, mock_save, mock_delete):
        file = SimpleUploadedFile(
            "something.txt", b"file_content", content_type="text/plain"
        )
        upload = MentorEventFileUpload.objects.create(
            eventAttendance=self.beforeDueTeam,
            uploadedBy=self.user,
            fileType=self.fileType1,
            fileUpload=file,
            originalFilename="something.txt",
        )
        self.client.login(
            request=HttpRequest(), username=self.super, password=self.password
        )
        response = self.client.get(
            reverse("teams:details", kwargs={"teamID": self.beforeDueTeam.pk})
        )
        self.assertContains(response, "Delete</button>")
        response = self.client.delete(
            reverse(
                "eventfiles:edit",
                kwargs={"uploadedFileID": upload.pk},
            ),
            data={},
            follow=False,
        )
        self.assertEqual(
            MentorEventFileUpload.objects.filter(
                eventAttendance=self.beforeDueTeam
            ).count(),
            0,
        )

    @patch("storages.backends.s3boto3.S3Boto3Storage.size", return_value=1)
    @patch("storages.backends.s3boto3.S3Boto3Storage.save", return_value="fileName.ext")
    @patch("storages.backends.s3boto3.S3Boto3Storage.delete")
    def testAfterDueCoordinator(self, mock_size, mock_save, mock_delete):
        file = SimpleUploadedFile(
            "something.txt", b"file_content", content_type="text/plain"
        )
        upload = MentorEventFileUpload.objects.create(
            eventAttendance=self.afterDueTeam,
            uploadedBy=self.user,
            fileType=self.fileType1,
            fileUpload=file,
            originalFilename="something.txt",
        )
        self.client.login(
            request=HttpRequest(), username=self.super, password=self.password
        )
        response = self.client.get(
            reverse("teams:details", kwargs={"teamID": self.afterDueTeam.pk})
        )
        self.assertContains(response, "Delete</button>")
        response = self.client.delete(
            reverse(
                "eventfiles:edit",
                kwargs={"uploadedFileID": upload.pk},
            ),
            data={},
            follow=False,
        )
        self.assertEqual(
            MentorEventFileUpload.objects.filter(
                eventAttendance=self.afterDueTeam
            ).count(),
            0,
        )

    @patch("storages.backends.s3boto3.S3Boto3Storage.size", return_value=1)
    @patch("storages.backends.s3boto3.S3Boto3Storage.save", return_value="fileName.ext")
    def testAfterEventCoordinator(self, mock_size, mock_save):
        file = SimpleUploadedFile(
            "something.txt", b"file_content", content_type="text/plain"
        )
        upload = MentorEventFileUpload.objects.create(
            eventAttendance=self.afterEventTeam,
            uploadedBy=self.user,
            fileType=self.fileType1,
            fileUpload=file,
            originalFilename="something.txt",
        )
        self.client.login(
            request=HttpRequest(), username=self.super, password=self.password
        )
        response = self.client.get(
            reverse("teams:details", kwargs={"teamID": self.afterEventTeam.pk})
        )
        self.assertNotContains(response, "Delete</button>")
        response = self.client.delete(
            reverse(
                "eventfiles:edit",
                kwargs={"uploadedFileID": upload.pk},
            ),
            data={},
            follow=False,
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            1,
            MentorEventFileUpload.objects.filter(
                eventAttendance=self.afterEventTeam
            ).count(),
        )
