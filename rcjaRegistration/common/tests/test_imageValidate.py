from django.test import TestCase
from django.urls import reverse
from django.http import HttpRequest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile, InMemoryUploadedFile
from unittest.mock import patch

from django.db.models.fields.files import ImageFieldFile

from PIL import Image
from io import BytesIO

from django.db import models
from common.models import checkImage

from django.core.files.images import ImageFile
from django.core.files.storage import InMemoryStorage
from django.db.models import ImageField 

import datetime

class ModelWithImage(models.Model):
    image = ImageField(storage=InMemoryStorage())

def createImage(width, height):
    
    file = ImageFieldFile(ModelWithImage(),ModelWithImage.image.field,"Test.png")
    image = Image.new(mode = "RGB", size = (width, height))
    output = BytesIO()
    image.save(output, format="png")
    output.seek(0)
    file.save(file.name,ImageFile(output, file.name))
    return file

def newCommonSetUp(self):
        
        """self.state1 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='Victoria', abbreviation='VIC')
        self.state2 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='NSW', abbreviation='NSW')
        self.region1 = Region.objects.create(name='Test Region', description='test desc')

        self.user1 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email1, password=self.password, homeState=self.state1)
        self.user2 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email2, password=self.password, homeState=self.state1)
        self.user3 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email3, password=self.password, homeState=self.state2)
        self.superUser = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email_superUser, password=self.password, is_superuser=True, is_staff=True, homeState=self.state1)

        self.school1 = School.objects.create(name='School 1', state=self.state1, region=self.region1)
        self.school2 = School.objects.create(name='School 2', state=self.state1, region=self.region1)
        self.school3 = School.objects.create(name='School 3', state=self.state2, region=self.region1)

        self.year = Year.objects.create(year=2020)
        self.event = Event.objects.create(
            year=self.year,
            state=self.state1,
            name='Test event 1',
            eventType='competition',
            status='published',
            maxMembersPerTeam=5,
            entryFeeIncludesGST=True,
            competition_billingType='team',
            competition_defaultEntryFee = 50,
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

        self.jpegFile = SimpleUploadedFile("jpeg.jpeg", b"file_content", content_type="image/jpeg")"""
"""
@patch('storages.backends.s3boto3.S3Boto3Storage.save', return_value='fileName.ext')
def createFile(self, mock_save):
    return MentorEventFileUpload.objects.create(eventAttendance=self.team1, fileType=self.fileType1, fileUpload=self.docFile, originalFilename="doc.doc", uploadedBy=self.user2)
"""

class Base_Test_ImageValidate(TestCase):    
    def url(self):
        pass

    def setUp(self):
        newCommonSetUp(self)
    
    def testCorrectSize(self):
        file = createImage(400,300)
        file.save(file.name,checkImage(file))
        self.assertEqual(400, file.width)
        self.assertEqual(300, file.height)

    def testTooWide(self):
        file = createImage(700,300)
        file.save(file.name,checkImage(file))
        self.assertEqual(400, file.width)
        self.assertEqual(300, file.height)

    def testTooHigh(self):
        file = createImage(400,500)
        file.save(file.name,checkImage(file))
        self.assertEqual(400, file.width)
        self.assertEqual(300, file.height)