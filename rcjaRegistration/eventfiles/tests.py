from django.test import TestCase
from django.urls import reverse
from django.http import HttpRequest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

from invoices.models import InvoiceGlobalSettings
from users.models import User
from regions.models import State, Region
from schools.models import School, SchoolAdministrator, Campus
from events.models import Event, Year, Division, AvailableDivision
from coordination.models import Coordinator
from teams.models import Team, Student, HardwarePlatform, SoftwarePlatform

from .models import MentorEventFileType, MentorEventFileUpload, EventAvailableFileType
from .forms import MentorEventFileUploadForm

import datetime

def newCommonSetUp(self):
        self.state1 = State.objects.create(typeRegistration=True, name='Victoria', abbreviation='VIC')
        self.state2 = State.objects.create(typeRegistration=True, name='NSW', abbreviation='NSW')
        self.region1 = Region.objects.create(name='Test Region', description='test desc')

        self.user1 = User.objects.create_user(email=self.email1, password=self.password, homeState=self.state1)
        self.user2 = User.objects.create_user(email=self.email2, password=self.password, homeState=self.state1)
        self.user3 = User.objects.create_user(email=self.email3, password=self.password, homeState=self.state2)
        self.superUser = User.objects.create_user(email=self.email_superUser, password=self.password, is_superuser=True, is_staff=True, homeState=self.state1)

        self.school1 = School.objects.create(name='School 1', abbreviation='sch1', state=self.state1, region=self.region1)
        self.school2 = School.objects.create(name='School 2', abbreviation='sch2', state=self.state1, region=self.region1)
        self.school3 = School.objects.create(name='School 3', abbreviation='sch3', state=self.state2, region=self.region1)

        self.year = Year.objects.create(year=2020)
        self.event = Event.objects.create(
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

        self.invoiceSettings = InvoiceGlobalSettings.objects.create(
            invoiceFromName='From Name',
            invoiceFromDetails='Test Details Text',
            invoiceFooterMessage='Test Footer Text',
        )

        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.team2 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 2', division=self.division1)

        self.docFile = SimpleUploadedFile("doc.doc", b"file_content", content_type="application/msword")
        self.pdfFile = SimpleUploadedFile("pdf.pdf", b"file_content", content_type="application/pdf")
        self.jpegFile = SimpleUploadedFile("jpeg.jpeg", b"file_content", content_type="image/jpeg")
        self.noExtFile = SimpleUploadedFile("noext", b"file_content", content_type="image/jpeg")

        self.fileType1 = MentorEventFileType.objects.create(name="File Type 1")

        self.availableFileType1 = EventAvailableFileType.objects.create(event=self.event, fileType=self.fileType1, uploadDeadline=(datetime.datetime.now() + datetime.timedelta(days=5)).date())

@patch('storages.backends.s3boto3.S3Boto3Storage.save', return_value='fileName.ext')
def createFile(self, mock_save):
    return MentorEventFileUpload.objects.create(eventAttendance=self.team1, fileType=self.fileType1, fileUpload=self.docFile, originalFilename="doc.doc", uploadedBy=self.user2)

class Base_Test_MentorEventFileUploadView:
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'
    
    def url(self):
        pass

    def setUp(self):
        newCommonSetUp(self)

class Test_MentorEventFileUploadView_LoginRequired(Base_Test_MentorEventFileUploadView, TestCase):
    def testNewFileGet(self):
        response = self.client.get(reverse('eventfiles:uploadFile', kwargs={'eventAttendanceID':self.team1.id}))
        self.assertEqual(response.url, f"/accounts/login/?next=/teams/{self.team1.id}/uploadFile")
        self.assertEqual(response.status_code, 302)

    def testExistingFileGet(self):
        self.uploadedFile1 = createFile(self)

        response = self.client.get(reverse('eventfiles:edit', kwargs={'uploadedFileID':self.uploadedFile1.id}))
        self.assertEqual(response.url, f"/accounts/login/?next=/eventfiles/{self.uploadedFile1.id}/edit")
        self.assertEqual(response.status_code, 302)

# Permissions

class Base_Test_MentorEventFileUploadView_Permissions(Base_Test_MentorEventFileUploadView):
    def setUp(self):
        super().setUp()
        self.login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

    def getResponse(self):
        return self.client.get(self.url())

    def testPageLoads(self):
        response = self.getResponse()
        self.assertEqual(response.status_code, 200)

    def testUsesCorrectTemplate(self):
        response = self.getResponse()
        self.assertTemplateUsed(response, 'eventfiles/uploadMentorEventFile.html')

    def testDeniedUploadDeadlinePassed(self):
        self.availableFileType1.uploadDeadline=(datetime.datetime.now() - datetime.timedelta(days=5)).date()
        self.availableFileType1.save()

        response = self.getResponse()
        self.assertEqual(response.status_code, 403)
        return response

    def testDeniedNotAdminTeam(self):
        self.team1.mentorUser = self.user2
        self.team1.save()

        response = self.getResponse()
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You are not an administrator of this team/ attendee", status_code=403)

    def testDeniedEventNotPublished(self):
        self.event.status = 'draft'
        self.event.save()

        response = self.getResponse()
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Event is not published", status_code=403)

    @patch('events.models.BaseEventAttendance.eventAttendanceType', return_value='workshopattendee')
    def testDeniedWorkshopAttendee(self, mock_eventAttendanceType):
        response = self.getResponse()
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "File upload is only supported for teams", status_code=403)

class Test_MentorEventFileUploadView_Permissions_NewFile_Get(Base_Test_MentorEventFileUploadView_Permissions, TestCase):
    def url(self):
        return reverse('eventfiles:uploadFile', kwargs={'eventAttendanceID': self.team1.id})
    
    def testDeniedUploadDeadlinePassed(self):
        response = super().testDeniedUploadDeadlinePassed()
        self.assertContains(response, "File upload not available", status_code=403)

class Test_MentorEventFileUploadView_Permissions_ExistingFile_Get(Base_Test_MentorEventFileUploadView_Permissions, TestCase):
    def setUp(self):
        super().setUp()
        self.uploadedFile1 = createFile(self)

    def url(self):
        return reverse('eventfiles:edit', kwargs={'uploadedFileID': self.uploadedFile1.id})

    def testDeniedUploadDeadlinePassed(self):
        response = super().testDeniedUploadDeadlinePassed()
        self.assertContains(response, "The upload deadline has passed for this file type for this event", status_code=403)

class Test_MentorEventFileUploadView_Permissions_NewFile_Post(Base_Test_MentorEventFileUploadView_Permissions, TestCase):
    def url(self):
        return reverse('eventfiles:uploadFile', kwargs={'eventAttendanceID': self.team1.id})

    def getResponse(self):
        return self.client.post(self.url())

    def testDeniedUploadDeadlinePassed(self):
        response = super().testDeniedUploadDeadlinePassed()
        self.assertContains(response, "File upload not available", status_code=403)

class Patched_Base_Test_MentorEventFileUploadView_Permissions(Base_Test_MentorEventFileUploadView_Permissions):
    @patch('storages.backends.s3boto3.S3Boto3Storage.delete')
    @patch('storages.backends.s3boto3.S3Boto3Storage.size', return_value=1)
    @patch('storages.backends.s3boto3.S3Boto3Storage.save', return_value='fileName.ext')
    def testPageLoads(self, mock_save, mock_size, mock_delete):
        return super().testPageLoads()

    @patch('storages.backends.s3boto3.S3Boto3Storage.delete')
    @patch('storages.backends.s3boto3.S3Boto3Storage.size', return_value=1)
    @patch('storages.backends.s3boto3.S3Boto3Storage.save', return_value='fileName.ext')
    def testUsesCorrectTemplate(self, mock_save, mock_size, mock_delete):
        return super().testUsesCorrectTemplate()

class Test_MentorEventFileUploadView_Permissions_ExistingFile_Post(Patched_Base_Test_MentorEventFileUploadView_Permissions, TestCase):
    def setUp(self):
        super().setUp()
        self.uploadedFile1 = createFile(self)

    def url(self):
        return reverse('eventfiles:edit', kwargs={'uploadedFileID': self.uploadedFile1.id})

    def getResponse(self):
        return self.client.post(self.url())

    def testDeniedUploadDeadlinePassed(self):
        response = super().testDeniedUploadDeadlinePassed()
        self.assertContains(response, "The upload deadline has passed for this file type for this event", status_code=403)

class Test_MentorEventFileUploadView_Permissions_ExistingFile_Delete(Patched_Base_Test_MentorEventFileUploadView_Permissions, TestCase):
    def setUp(self):
        super().setUp()
        self.uploadedFile1 = createFile(self)

    def url(self):
        return reverse('eventfiles:edit', kwargs={'uploadedFileID': self.uploadedFile1.id})

    def getResponse(self):
        return self.client.delete(self.url())

    @patch('storages.backends.s3boto3.S3Boto3Storage.delete')
    @patch('storages.backends.s3boto3.S3Boto3Storage.size', return_value=1)
    @patch('storages.backends.s3boto3.S3Boto3Storage.save', return_value='fileName.ext')
    def testPageLoads(self, mock_save, mock_size, mock_delete):
        response = self.getResponse()
        self.assertEqual(response.status_code, 204)

    @patch('storages.backends.s3boto3.S3Boto3Storage.delete')
    @patch('storages.backends.s3boto3.S3Boto3Storage.size', return_value=1)
    @patch('storages.backends.s3boto3.S3Boto3Storage.save', return_value='fileName.ext')
    def testUsesCorrectTemplate(self, mock_save, mock_size, mock_delete):
        response = self.getResponse()
        self.assertTemplateNotUsed(response, 'eventfiles/uploadMentorEventFile.html')

    def testDeniedUploadDeadlinePassed(self):
        response = super().testDeniedUploadDeadlinePassed()
        self.assertContains(response, "The upload deadline has passed for this file type for this event", status_code=403)

# File upload post

class Test_MentorEventFileUploadView_NewFileUpload_Post(Base_Test_MentorEventFileUploadView, TestCase):
    def setUp(self):
        super().setUp()
        self.login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

    def url(self):
        return reverse('eventfiles:uploadFile', kwargs={'eventAttendanceID': self.team1.id})

    def getResponse(self):
        return self.client.post(self.url())

    def testErrorBlankForm(self):
        response = self.getResponse()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "File: This field is required.")
        self.assertContains(response, "Type: This field is required.")

    @patch('storages.backends.s3boto3.S3Boto3Storage.size', return_value=1)
    @patch('storages.backends.s3boto3.S3Boto3Storage.save', return_value='fileName.ext')
    def testSuccess(self, mock_save, mock_size):
        data = {
            'fileUpload': self.docFile,
            'fileType': self.fileType1.id,
        }
        self.assertEqual(MentorEventFileUpload.objects.count(), 0)
        response = self.client.post(self.url(), data=data)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(MentorEventFileUpload.objects.count(), 1)
        self.assertEqual(MentorEventFileUpload.objects.first().uploadedBy, self.user1)
        self.assertEqual(MentorEventFileUpload.objects.first().eventAttendance.childObject(), self.team1)
        self.assertEqual(MentorEventFileUpload.objects.first().originalFilename, "doc.doc")

class Test_MentorEventFileUploadView_ExistingFile_Post(Base_Test_MentorEventFileUploadView, TestCase):
    def setUp(self):
        super().setUp()
        self.login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        self.uploadedFile1 = createFile(self)

    def url(self):
        return reverse('eventfiles:edit', kwargs={'uploadedFileID': self.uploadedFile1.id})

    @patch('storages.backends.s3boto3.S3Boto3Storage.size', return_value=1)
    @patch('storages.backends.s3boto3.S3Boto3Storage.save', return_value='fileName.ext')
    def testSuccess(self, mock_save, mock_size):
        data = {
            'fileUpload': self.jpegFile,
            'fileType': self.fileType1.id,
            'comments': 'hello'
        }
        self.assertEqual(MentorEventFileUpload.objects.count(), 1)
        response = self.client.post(self.url(), data=data)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(MentorEventFileUpload.objects.count(), 1)
        self.assertEqual(MentorEventFileUpload.objects.first().uploadedBy, self.user2)
        self.assertEqual(MentorEventFileUpload.objects.first().eventAttendance.childObject(), self.team1)
        self.assertEqual(MentorEventFileUpload.objects.first().originalFilename, "doc.doc")
        self.assertEqual(MentorEventFileUpload.objects.first().comments, "hello")

# File upload delete

class Test_MentorEventFileUploadView_Delete(Base_Test_MentorEventFileUploadView, TestCase):
    def setUp(self):
        super().setUp()
        self.login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        self.uploadedFile1 = createFile(self)

    def url(self):
        return reverse('eventfiles:edit', kwargs={'uploadedFileID': self.uploadedFile1.id})

    def getResponse(self):
        return self.client.delete(self.url())

    @patch('storages.backends.s3boto3.S3Boto3Storage.delete')
    def testSuccessfulDelete(self, mock_delete):
        self.assertEqual(MentorEventFileUpload.objects.count(), 1)
        response = self.getResponse()
        self.assertEqual(response.status_code, 204)
        self.assertEqual(MentorEventFileUpload.objects.count(), 0)

    @patch('storages.backends.s3boto3.S3Boto3Storage.delete')
    def testDeniedEventAttendanceID(self, mock_delete):
        self.assertEqual(MentorEventFileUpload.objects.count(), 1)

        url = reverse('eventfiles:uploadFile', kwargs={'eventAttendanceID': self.team1.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(MentorEventFileUpload.objects.count(), 1)

# Unit tests

class Test_MentorEventFileUploadForm(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        newCommonSetUp(self)

        self.uploadedFile1 = createFile(self)

    def testBlankFormUploadEnabled(self):
        form = MentorEventFileUploadForm(instance=None, uploadedFile=None, eventAttendance=self.team1)

        self.assertEqual(form.fields['fileUpload'].disabled, False)

    def testExistingFormUploadDisabled(self):
        form = MentorEventFileUploadForm(instance=self.uploadedFile1, uploadedFile=self.uploadedFile1, eventAttendance=self.team1)

        self.assertEqual(form.fields['fileUpload'].disabled, True)

    def testFileTypeQuerysetFiltered_uploadOpen(self):
        form = MentorEventFileUploadForm(instance=None, uploadedFile=None, eventAttendance=self.team1)

        self.assertIn(self.availableFileType1.fileType, form.fields['fileType'].queryset)

    def testFileTypeQuerysetFiltered_uploadClosed(self):
        self.availableFileType1.uploadDeadline = (datetime.datetime.now() - datetime.timedelta(days=5)).date()
        self.availableFileType1.save()

        form = MentorEventFileUploadForm(instance=None, uploadedFile=None, eventAttendance=self.team1)

        self.assertNotIn(self.availableFileType1.fileType, form.fields['fileType'].queryset)

class Test_MentorEventFileUpload_Clean(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        newCommonSetUp(self)

    def testValidNoExtensionRestrictions(self):
        uploadedFile = MentorEventFileUpload(eventAttendance=self.team1, fileType=self.fileType1, fileUpload=self.docFile, originalFilename="doc.doc", uploadedBy=self.user2)

        uploadedFile.clean()

    def testValidExtensionRestrictions(self):
        self.fileType1.allowedFileTypes = "doc,pdf"
        self.fileType1.save()

        uploadedFile = MentorEventFileUpload(eventAttendance=self.team1, fileType=self.fileType1, fileUpload=self.docFile, originalFilename="doc.doc", uploadedBy=self.user2)

        uploadedFile.clean()

    def testInvalidExtension(self):
        self.fileType1.allowedFileTypes = "png,jpeg"
        self.fileType1.save()

        uploadedFile = MentorEventFileUpload(eventAttendance=self.team1, fileType=self.fileType1, fileUpload=self.docFile, originalFilename="doc.doc", uploadedBy=self.user2)

        self.assertRaises(ValidationError, uploadedFile.clean)

    def testNoExtension(self):
        self.fileType1.allowedFileTypes = "png,jpeg"
        self.fileType1.save()

        uploadedFile = MentorEventFileUpload(eventAttendance=self.team1, fileType=self.fileType1, fileUpload=self.noExtFile, originalFilename="noext", uploadedBy=self.user2)

        self.assertRaises(ValidationError, uploadedFile.clean)

    @patch('eventfiles.models.MentorEventFileType.maxFilesizeBytes', return_value=5)
    def testInvalidFileSize(self, mock_size):
        uploadedFile = MentorEventFileUpload(eventAttendance=self.team1, fileType=self.fileType1, fileUpload=self.docFile, originalFilename="doc.doc", uploadedBy=self.user2)

        self.assertRaises(ValidationError, uploadedFile.clean)

class Test_MentorEventFileUpload_Methods(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        newCommonSetUp(self)
        self.uploadedFile = MentorEventFileUpload(eventAttendance=self.team1, fileType=self.fileType1, fileUpload=self.docFile, originalFilename="doc.doc", uploadedBy=self.user2)

    def testGetState(self):
        self.assertEqual(self.uploadedFile.getState(), self.state1)

    def testEvent(self):
        self.assertEqual(self.uploadedFile.event(), self.event)

    def testFilesize(self):
        self.assertEqual(self.uploadedFile.filesize(), "12\xa0bytes")

    @patch('storages.backends.s3boto3.S3Boto3Storage.url', return_value='testURL')
    def testFileURL(self, mock_URL):
        self.assertEqual(self.uploadedFile.fileURL(), "testURL")

    def testStr(self):
        self.assertEqual(str(self.uploadedFile), "doc.doc")

class Test_EventAvailableFileType_Methods(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        newCommonSetUp(self)

    def testGetState(self):
        self.assertEqual(self.availableFileType1.getState(), self.state1)

    def testStr(self):
        self.assertEqual(str(self.availableFileType1), "Test event 1 2020 (VIC): File Type 1")

class Test_MentorEventFileType_Methods(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        newCommonSetUp(self)

    def testMaxFilesizeBytes(self):
        self.assertEqual(self.fileType1.maxFilesizeBytes(), 104857600)

    def testMxFileSizeStr(self):
        self.assertEqual(self.fileType1.maxFileSizeStr(), "100.0\xa0MB")

    def testStr(self):
        self.assertEqual(str(self.fileType1), "File Type 1")

    def testCleanValidFilesize(self):
        fileType2 = MentorEventFileType(name="File Type 2", maxFilesizeMB=500)

        fileType2.clean()

    def testCleanInvalidFilesize(self):
        fileType2 = MentorEventFileType(name="File Type 2", maxFilesizeMB=5000)

        self.assertRaises(ValidationError, fileType2.clean)
