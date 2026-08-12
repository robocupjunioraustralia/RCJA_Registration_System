from django.test import TestCase
from django.urls import reverse
from django.http import HttpRequest
from django.core.files.uploadedfile import SimpleUploadedFile

from unittest.mock import patch

from common.baseTests import createStates, createUsers, createSchools, createEvents, createTeams

from teams.models import Team, Student

# Column names come from the model field verbose names
# Header for a school mentor on an event with the default four members per team
FULL_HEADER = (
    'Name,Division,Campus,Hardware platform,Software platform,'
    'Student 1 First name,Student 1 Last name,Student 1 Year level,Student 1 Gender,'
    'Student 2 First name,Student 2 Last name,Student 2 Year level,Student 2 Gender,'
    'Student 3 First name,Student 3 Last name,Student 3 Year level,Student 3 Gender,'
    'Student 4 First name,Student 4 Last name,Student 4 Year level,Student 4 Gender'
)

# Columns for trailing students can be left out of the file
HEADER = (
    'Name,Division,Campus,Hardware platform,Software platform,'
    'Student 1 First name,Student 1 Last name,Student 1 Year level,Student 1 Gender'
)

HEADER_NO_CAMPUS = (
    'Name,Division,Hardware platform,Software platform,'
    'Student 1 First name,Student 1 Last name,Student 1 Year level,Student 1 Gender'
)

VALID_ROW = 'Team 10,Division 3,,HW 1,HW 1,Alice,Smith,7,Female'
VALID_ROW_NO_CAMPUS = 'Team 10,Division 3,HW 1,HW 1,Alice,Smith,7,Female'

def buildCSV(*lines):
    return '\r\n'.join(lines) + '\r\n'

def csvUpload(content):
    return SimpleUploadedFile('teams.csv', content.encode('utf-8'), content_type='text/csv')

class ImportCSVBase:
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createSchools(cls)
        createEvents(cls)
        createTeams(cls)

    def setUp(self):
        self.event = self.state1_openCompetition
        self.importURL = reverse('teams:importCSV', kwargs={'eventID': self.event.id})
        self.templateURL = reverse('teams:importCSVTemplate', kwargs={'eventID': self.event.id})
        self.loginMentor1()

    def loginMentor1(self):
        self.client.login(request=HttpRequest(), username=self.email_user_state1_school1_mentor1, password=self.password)

    def loginIndependentMentor5(self):
        self.client.login(request=HttpRequest(), username=self.email_user_state1_independent_mentor5, password=self.password)

    def preview(self, content):
        return self.client.post(self.importURL, {'preview': '', 'csvFile': csvUpload(content)})

    def importTeams(self, content):
        return self.client.post(self.importURL, {'import': '', 'csvText': content})

    # The page heading also contains the words 'Import teams', so match the submit button itself
    def assertImportButtonShown(self, response):
        self.assertContains(response, 'name="import"')

    def assertImportButtonNotShown(self, response):
        self.assertNotContains(response, 'name="import"')

class TestImportCSVPermissions(ImportCSVBase, TestCase):
    def testPageLoads(self):
        response = self.client.get(self.importURL)
        self.assertEqual(200, response.status_code)

    def testLoginRequired(self):
        self.client.logout()
        response = self.client.get(self.importURL)
        self.assertEqual(302, response.status_code)
        self.assertEqual(f'/accounts/login/?next={self.importURL}', response.url)

    def testButtonOnEventDetailsPage(self):
        response = self.client.get(reverse('events:details', kwargs={'eventID': self.event.id}))
        self.assertContains(response, f'href="{self.importURL}"')
        self.assertContains(response, 'Import CSV')

    def testButtonNotOnEventDetailsPageWhenRegistrationClosed(self):
        closedEvent = self.state1_closedCompetition1

        # A team is needed for this mentor to be allowed to view the details page of a closed event
        Team.objects.create(
            event = closedEvent,
            division = self.division3,
            mentorUser = self.user_state1_school1_mentor1,
            school = self.school1_state1,
            name = 'Closed Event Team',
            hardwarePlatform = self.hardwarePlatform,
            softwarePlatform = self.softwarePlatform,
        )

        response = self.client.get(reverse('events:details', kwargs={'eventID': closedEvent.id}))
        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, reverse('teams:importCSV', kwargs={'eventID': closedEvent.id}))

    def testDeniedWorkshop(self):
        response = self.client.get(reverse('teams:importCSV', kwargs={'eventID': self.state1_openWorkshop.id}))
        self.assertEqual(403, response.status_code)
        self.assertContains(response, 'Teams/ attendees cannot be created for this event type', status_code=403)

    def testDeniedRegistrationClosed(self):
        response = self.client.get(reverse('teams:importCSV', kwargs={'eventID': self.state1_closedCompetition1.id}))
        self.assertEqual(403, response.status_code)
        self.assertContains(response, 'Registration has closed for this event', status_code=403)

    def testDeniedNotPublished(self):
        self.event.status = 'draft'
        self.event.save()

        response = self.client.get(self.importURL)
        self.assertEqual(403, response.status_code)
        self.assertContains(response, 'Event is not published', status_code=403)

    def testDeniedMaxRegistrationsForSchoolReached(self):
        self.event.event_maxRegistrationsPerSchool = 2
        self.event.save()

        response = self.client.get(self.importURL)
        self.assertEqual(403, response.status_code)

    def testPostDeniedRegistrationClosed(self):
        response = self.client.post(
            reverse('teams:importCSV', kwargs={'eventID': self.state1_closedCompetition1.id}),
            {'preview': '', 'csvFile': csvUpload(buildCSV(HEADER, VALID_ROW))},
        )
        self.assertEqual(403, response.status_code)

class TestImportCSVTemplateDownloadPermissions(ImportCSVBase, TestCase):
    def testLoginRequired(self):
        self.client.logout()

        response = self.client.get(self.templateURL)
        self.assertEqual(302, response.status_code)
        self.assertEqual(f'/accounts/login/?next={self.templateURL}', response.url)

    def testDeniedWorkshop(self):
        response = self.client.get(reverse('teams:importCSVTemplate', kwargs={'eventID': self.state1_openWorkshop.id}))
        self.assertEqual(403, response.status_code)
        self.assertContains(response, 'Teams/ attendees cannot be created for this event type', status_code=403)

    def testDeniedRegistrationClosed(self):
        response = self.client.get(reverse('teams:importCSVTemplate', kwargs={'eventID': self.state1_closedCompetition1.id}))
        self.assertEqual(403, response.status_code)
        self.assertContains(response, 'Registration has closed for this event', status_code=403)

    def testDeniedNotPublished(self):
        self.event.status = 'draft'
        self.event.save()

        response = self.client.get(self.templateURL)
        self.assertEqual(403, response.status_code)
        self.assertContains(response, 'Event is not published', status_code=403)

    def testDeniedMaxRegistrationsForSchoolReached(self):
        # This school already has two teams in this event
        self.event.event_maxRegistrationsPerSchool = 2
        self.event.save()

        response = self.client.get(self.templateURL)
        self.assertEqual(403, response.status_code)
        self.assertContains(response, 'Max teams for school for this event reached', status_code=403)

    def testDeniedMaxRegistrationsForEventReached(self):
        self.event.event_maxRegistrationsForEvent = 1
        self.event.save()

        response = self.client.get(self.templateURL)
        self.assertEqual(403, response.status_code)
        self.assertContains(response, 'Max teams for this event reached', status_code=403)

class TestImportCSVTemplateDownload(ImportCSVBase, TestCase):
    def testTemplateIsCSV(self):
        response = self.client.get(self.templateURL)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/csv', response['Content-Type'])
        self.assertIn('attachment;', response['Content-Disposition'])

    def testTemplateFilenameUsesFullEventName(self):
        response = self.client.get(self.templateURL)
        self.assertEqual(
            'attachment; filename="State 1 Open Competition 2021 (ST1) Team Import Template.csv"',
            response['Content-Disposition'],
        )

    def testTemplateHeader(self):
        response = self.client.get(self.templateURL)
        self.assertEqual(FULL_HEADER, response.content.decode('utf-8').strip())

    def testTemplateHasNoCampusColumnForIndependentMentor(self):
        self.loginIndependentMentor5()

        response = self.client.get(self.templateURL)
        header = response.content.decode('utf-8').strip()
        self.assertNotIn('Campus', header)
        self.assertTrue(header.startswith('Name,Division,Hardware platform,Software platform,'))

    def testTemplateStudentColumnsMatchMaxMembersPerTeam(self):
        self.event.maxMembersPerTeam = 2
        self.event.save()

        response = self.client.get(self.templateURL)
        header = response.content.decode('utf-8').strip()
        self.assertIn('Student 2 Gender', header)
        self.assertNotIn('Student 3 First name', header)

class TestImportCSVOptionsTable(ImportCSVBase, TestCase):
    # Literal text in a template is not autoescaped, so the apostrophe is unchanged
    campusNote = "Campus is optional, leave the column blank if you don't want to set a campus."

    def testOptionsTableHeadings(self):
        response = self.client.get(self.importURL)
        self.assertContains(response, '<th>Division</th><th>Campus</th><th>Hardware platform</th><th>Software platform</th><th>Gender</th>')

    def testOptionsTableRows(self):
        response = self.client.get(self.importURL)
        self.assertContains(response, '<td>Division 3</td><td>Campus 1</td><td>HW 1</td><td>HW 1</td><td>Male</td>')

    def testShorterColumnsArePadded(self):
        # There are three genders but only two divisions and campuses and one of each platform
        response = self.client.get(self.importURL)
        self.assertContains(response, '<td>Division 4</td><td>Campus 2</td><td></td><td></td><td>Female</td>')
        self.assertContains(response, '<td></td><td></td><td></td><td></td><td>Other</td>')

    def testCampusNoteShown(self):
        response = self.client.get(self.importURL)
        self.assertContains(response, self.campusNote)

    def testNoCampusColumnForIndependentMentor(self):
        self.loginIndependentMentor5()

        response = self.client.get(self.importURL)
        self.assertContains(response, '<th>Division</th><th>Hardware platform</th><th>Software platform</th><th>Gender</th>')
        self.assertNotContains(response, self.campusNote)

class TestImportCSVPreview(ImportCSVBase, TestCase):
    def testValidFileShowsImportButton(self):
        response = self.preview(buildCSV(HEADER, VALID_ROW))
        self.assertEqual(200, response.status_code)
        self.assertImportButtonShown(response)
        self.assertContains(response, 'No errors were found')

    def testUploadFormHiddenWhenImportButtonShown(self):
        response = self.preview(buildCSV(HEADER, VALID_ROW))
        self.assertNotContains(response, 'name="preview"')
        self.assertNotContains(response, 'name="csvFile"')
        # The cancel button moves to the import form, so there is still exactly one
        self.assertContains(response, 'Cancel', count=1)

    def testUploadFormShownWhenThereAreErrors(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,Not A Division,,HW 1,HW 1,Alice,Smith,7,Female'))
        self.assertImportButtonNotShown(response)
        self.assertContains(response, 'name="preview"')
        self.assertContains(response, 'name="csvFile"')
        self.assertContains(response, 'Cancel', count=1)

    def testGenderShownAsDisplayName(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,Division 3,,HW 1,HW 1,Alice,Smith,7,fEmAlE'))
        self.assertContains(response, 'Alice Smith (7, Female)')

    def testValidFileCreatesNothing(self):
        teamCount = Team.objects.count()
        studentCount = Student.objects.count()

        self.preview(buildCSV(HEADER, VALID_ROW))

        self.assertEqual(teamCount, Team.objects.count())
        self.assertEqual(studentCount, Student.objects.count())

    def testInvalidFileCreatesNothing(self):
        teamCount = Team.objects.count()
        studentCount = Student.objects.count()

        self.preview(buildCSV(HEADER, 'Team 10,Not A Division,,HW 1,HW 1,Alice,Smith,7,Female'))

        self.assertEqual(teamCount, Team.objects.count())
        self.assertEqual(studentCount, Student.objects.count())

    def testTeamValuesShownInTable(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,Division 3,Campus 1,HW 1,HW 1,Alice,Smith,7,Female'))
        self.assertContains(response, 'Team 10')
        self.assertContains(response, 'Campus 1')
        self.assertContains(response, 'Alice Smith (7, Female)')

    def testNoFileUploaded(self):
        response = self.client.post(self.importURL, {'preview': ''})
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'This field is required')
        self.assertImportButtonNotShown(response)

    def testEmptyFileUpload(self):
        response = self.preview('')
        self.assertContains(response, 'The submitted file is empty')
        self.assertImportButtonNotShown(response)

    def testFileWithOnlyBlankLines(self):
        response = self.preview('\r\n\r\n')
        self.assertContains(response, 'The file is empty')
        self.assertImportButtonNotShown(response)

    def testHeaderOnlyFile(self):
        response = self.preview(buildCSV(HEADER))
        self.assertContains(response, 'does not contain any teams')
        self.assertImportButtonNotShown(response)

    def testMissingColumn(self):
        response = self.preview(buildCSV(
            'Name,Division,Campus,Hardware platform,Student 1 First name,Student 1 Last name,Student 1 Year level,Student 1 Gender',
            'Team 10,Division 3,,HW 1,Alice,Smith,7,Female',
        ))
        self.assertContains(response, "Required column &#x27;Software platform&#x27; is missing from the file.")
        self.assertImportButtonNotShown(response)

    def testBOMAndUntidyHeadingsAccepted(self):
        response = self.preview('\ufeff' + buildCSV(HEADER.replace('Name', ' NAME ', 1), VALID_ROW))
        self.assertContains(response, 'No errors were found')

    def testUnknownDivision(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,Not A Division,,HW 1,HW 1,Alice,Smith,7,Female'))
        self.assertContains(response, 'is not a valid option')
        self.assertContains(response, 'Division 3, Division 4')
        self.assertImportButtonNotShown(response)

    def testDivisionNotAvailableForEvent(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,Division 1,,HW 1,HW 1,Alice,Smith,7,Female'))
        self.assertContains(response, 'is not a valid option')
        self.assertImportButtonNotShown(response)

    def testDivisionCaseInsensitive(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,DIVISION 3,,HW 1,HW 1,Alice,Smith,7,Female'))
        self.assertContains(response, 'No errors were found')

    def testUnknownHardwarePlatform(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,Division 3,,Not A Platform,HW 1,Alice,Smith,7,Female'))
        self.assertContains(response, 'Hardware platform: &#x27;Not A Platform&#x27; is not a valid option')
        self.assertImportButtonNotShown(response)

    def testUnknownCampus(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,Division 3,Not A Campus,HW 1,HW 1,Alice,Smith,7,Female'))
        self.assertContains(response, 'Campus: &#x27;Not A Campus&#x27; is not a valid option')
        self.assertImportButtonNotShown(response)

    def testCampusOfAnotherSchoolRejected(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,Division 3,Campus 3,HW 1,HW 1,Alice,Smith,7,Female'))
        self.assertContains(response, 'is not a valid option')
        self.assertImportButtonNotShown(response)

    def testValidCampusAccepted(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,Division 3,Campus 2,HW 1,HW 1,Alice,Smith,7,Female'))
        self.assertContains(response, 'No errors were found')

    def testBlankTeamName(self):
        response = self.preview(buildCSV(HEADER, ',Division 3,,HW 1,HW 1,Alice,Smith,7,Female'))
        self.assertContains(response, 'Name: This field is required')
        self.assertImportButtonNotShown(response)

    def testInvalidTeamNameCharacters(self):
        response = self.preview(buildCSV(HEADER, 'Team #10!,Division 3,,HW 1,HW 1,Alice,Smith,7,Female'))
        self.assertContains(response, "Contains character that isn")
        self.assertImportButtonNotShown(response)

    def testDuplicateTeamNameInDatabase(self):
        response = self.preview(buildCSV(HEADER, 'Team 1,Division 3,,HW 1,HW 1,Alice,Smith,7,Female'))
        self.assertContains(response, 'Team with this name in this event already exists')
        self.assertImportButtonNotShown(response)

    def testDuplicateTeamNameInFile(self):
        response = self.preview(buildCSV(
            HEADER,
            VALID_ROW,
            VALID_ROW,
        ))
        self.assertContains(response, 'Duplicate of the team on row 2 of this file')
        self.assertImportButtonNotShown(response)

    def testTeamNameExistingInAnotherEventAllowed(self):
        # Team 3 exists in state2_openCompetition, team names only need to be unique within an event
        response = self.preview(buildCSV(HEADER, 'Team 3,Division 3,,HW 1,HW 1,Alice,Smith,7,Female'))
        self.assertContains(response, 'No errors were found')

    def testNoStudents(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,Division 3,,HW 1,HW 1,,,,'))
        self.assertContains(response, 'At least one student is required')
        self.assertImportButtonNotShown(response)

    def testPartiallyFilledStudent(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,Division 3,,HW 1,HW 1,Alice,,,'))
        self.assertContains(response, 'Student 1 Last name: This field is required')
        self.assertContains(response, 'Student 1 Year level: This field is required')
        self.assertImportButtonNotShown(response)

    def testInvalidGender(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,Division 3,,HW 1,HW 1,Alice,Smith,7,Alien'))
        self.assertContains(response, 'Student 1 Gender: Select a valid choice')
        self.assertImportButtonNotShown(response)

    def testGenderAcceptedInAnyCase(self):
        response = self.preview(buildCSV(
            HEADER,
            'Team 10,Division 3,,HW 1,HW 1,Alice,Smith,7,FEMALE',
            'Team 11,Division 3,,HW 1,HW 1,Bob,Smith,7,Male',
            'Team 12,Division 3,,HW 1,HW 1,Chris,Smith,7,oThEr',
        ))
        self.assertContains(response, 'No errors were found')

    def testInvalidYearLevel(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,Division 3,,HW 1,HW 1,Alice,Smith,Year Seven,Female'))
        self.assertContains(response, 'Student 1 Year level: Enter a whole number')
        self.assertImportButtonNotShown(response)

    def testTooManyStudentColumns(self):
        self.event.maxMembersPerTeam = 2
        self.event.save()

        response = self.preview(buildCSV(
            'Name,Division,Campus,Hardware platform,Software platform,'
            'Student 1 First name,Student 1 Last name,Student 1 Year level,Student 1 Gender,'
            'Student 2 First name,Student 2 Last name,Student 2 Year level,Student 2 Gender,'
            'Student 3 First name,Student 3 Last name,Student 3 Year level,Student 3 Gender',
            'Team 10,Division 3,,HW 1,HW 1,Alice,Smith,7,Female,Bob,Smith,7,Male,Chris,Smith,7,Other',
        ))
        self.assertContains(response, 'maximum of 2 students per team')
        self.assertImportButtonNotShown(response)

    def testPartialStudentColumnGroup(self):
        response = self.preview(buildCSV(
            'Name,Division,Campus,Hardware platform,Software platform,'
            'Student 1 First name,Student 1 Last name,Student 1 Year level,Student 1 Gender,'
            'Student 2 First name,Student 2 Last name',
            'Team 10,Division 3,,HW 1,HW 1,Alice,Smith,7,Female,Bob,Smith',
        ))
        self.assertContains(response, "Required column &#x27;Student 2 Year level&#x27; is missing from the file.")
        self.assertImportButtonNotShown(response)

    def testErrorOnOneRowBlocksWholeFile(self):
        response = self.preview(buildCSV(
            HEADER,
            VALID_ROW,
            'Team 11,Not A Division,,HW 1,HW 1,Bob,Smith,7,Male',
        ))
        self.assertContains(response, 'is not a valid option')
        self.assertImportButtonNotShown(response)

    def testIndependentMentorHasNoCampusColumn(self):
        self.loginIndependentMentor5()

        response = self.preview(buildCSV(HEADER_NO_CAMPUS, VALID_ROW_NO_CAMPUS))
        self.assertContains(response, 'No errors were found')

class TestImportCSVPreviewTable(ImportCSVBase, TestCase):
    # The preview table is laid out like the team table on the event details page, with errors in the cell they relate to
    TWO_STUDENT_HEADER = (
        'Name,Division,Campus,Hardware platform,Software platform,'
        'Student 1 First name,Student 1 Last name,Student 1 Year level,Student 1 Gender,'
        'Student 2 First name,Student 2 Last name,Student 2 Year level,Student 2 Gender'
    )

    def testHeadings(self):
        response = self.preview(buildCSV(HEADER, VALID_ROW))
        self.assertInHTML(
            '<thead><th>Team name</th><th>Division</th><th>Campus</th>'
            '<th>Hardware platform</th><th>Software platform</th><th>Students</th></thead>',
            response.content.decode(),
        )

    def testStudentsGroupedIntoOneCell(self):
        response = self.preview(buildCSV(
            self.TWO_STUDENT_HEADER,
            'Team 10,Division 3,,HW 1,HW 1,Alice,Smith,7,Female,Bob,Jones,8,Male',
        ))
        self.assertInHTML('<td>Alice Smith (7, Female), Bob Jones (8, Male)</td>', response.content.decode())

    def testMatchedOptionShownRatherThanTheTextInTheFile(self):
        # The whole row is checked because the options table above it also contains cells with these names
        response = self.preview(buildCSV(HEADER, 'Team 10,DIVISION 3,,hw 1,HW 1,Alice,Smith,7,Female'))
        self.assertInHTML(
            '<tr><td>Team 10</td><td>Division 3</td><td></td><td>HW 1</td><td>HW 1</td><td>Alice Smith (7, Female)</td></tr>',
            response.content.decode(),
        )

    def testDivisionErrorInDivisionCell(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,Not A Division,,HW 1,HW 1,Alice,Smith,7,Female'))
        self.assertInHTML(
            '<td>Not A Division<div class="error-text">'
            "Division: 'Not A Division' is not a valid option. Valid options are: Division 3, Division 4."
            '</div></td>',
            response.content.decode(),
        )

    def testHardwarePlatformErrorInHardwarePlatformCell(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,Division 3,,Not A Platform,HW 1,Alice,Smith,7,Female'))
        self.assertInHTML(
            '<td>Not A Platform<div class="error-text">'
            "Hardware platform: 'Not A Platform' is not a valid option. Valid options are: HW 1."
            '</div></td>',
            response.content.decode(),
        )

    def testStudentErrorInStudentsCell(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,Division 3,,HW 1,HW 1,Alice,,7,Female'))
        self.assertInHTML(
            '<td>Alice (7, Female)<div class="error-text">Student 1 Last name: This field is required.</div></td>',
            response.content.decode(),
        )

    def testNameErrorInNameCell(self):
        response = self.preview(buildCSV(HEADER, 'Team 10,Division 3,,HW 1,HW 1,Alice,Smith,7,Female', 'Team 10,Division 3,,HW 1,HW 1,Bob,Jones,8,Male'))
        self.assertInHTML(
            '<td>Team 10<div class="error-text">Name: Duplicate of the team on row 2 of this file.</div></td>',
            response.content.decode(),
        )

    def testWholeRowErrorInNameCell(self):
        # Two teams already exist for this school and event, so the third row in the file is over the limit
        self.event.event_maxRegistrationsPerSchool = 4
        self.event.save()

        response = self.preview(buildCSV(
            HEADER,
            'Team 10,Division 3,,HW 1,HW 1,Alice,Smith,7,Female',
            'Team 11,Division 3,,HW 1,HW 1,Bob,Jones,8,Male',
            'Team 12,Division 3,,HW 1,HW 1,Chris,Brown,9,Other',
        ))
        self.assertInHTML(
            '<td>Team 12<div class="error-text">Max teams for school for this event reached. '
            'Contact the organiser if you want to register more teams for this event.</div></td>',
            response.content.decode(),
        )

    def testNoCampusColumnForIndependentMentor(self):
        self.loginIndependentMentor5()

        response = self.preview(buildCSV(HEADER_NO_CAMPUS, VALID_ROW_NO_CAMPUS))
        self.assertNotContains(response, '<th>Campus</th>')

class TestImportCSVPreviewLimits(ImportCSVBase, TestCase):
    def testCumulativeEventLimitForSchool(self):
        # Two teams already exist for this school and event
        self.event.event_maxRegistrationsPerSchool = 4
        self.event.save()

        response = self.preview(buildCSV(
            HEADER,
            'Team 10,Division 3,,HW 1,HW 1,Alice,Smith,7,Female',
            'Team 11,Division 3,,HW 1,HW 1,Bob,Smith,7,Male',
            'Team 12,Division 3,,HW 1,HW 1,Chris,Smith,7,Other',
        ))
        self.assertContains(response, 'Max teams for school for this event reached')
        self.assertImportButtonNotShown(response)

    def testCumulativeEventLimitForSchoolNotExceeded(self):
        self.event.event_maxRegistrationsPerSchool = 4
        self.event.save()

        response = self.preview(buildCSV(
            HEADER,
            'Team 10,Division 3,,HW 1,HW 1,Alice,Smith,7,Female',
            'Team 11,Division 3,,HW 1,HW 1,Bob,Smith,7,Male',
        ))
        self.assertContains(response, 'No errors were found')

    def testCumulativeEventLimitTotal(self):
        self.event.event_maxRegistrationsForEvent = 3
        self.event.save()

        response = self.preview(buildCSV(
            HEADER,
            'Team 10,Division 3,,HW 1,HW 1,Alice,Smith,7,Female',
            'Team 11,Division 3,,HW 1,HW 1,Bob,Smith,7,Male',
        ))
        self.assertContains(response, 'Max teams for this event reached')
        self.assertImportButtonNotShown(response)

    def testCumulativeDivisionLimitForSchool(self):
        availableDivision = self.availableDivision3_state1_openCompetition
        availableDivision.division_maxRegistrationsPerSchool = 3
        availableDivision.save()

        response = self.preview(buildCSV(
            HEADER,
            'Team 10,Division 3,,HW 1,HW 1,Alice,Smith,7,Female',
            'Team 11,Division 3,,HW 1,HW 1,Bob,Smith,7,Male',
        ))
        self.assertContains(response, 'Max teams for school for this event division reached')
        self.assertImportButtonNotShown(response)

    def testCumulativeDivisionLimitDoesNotAffectOtherDivision(self):
        availableDivision = self.availableDivision3_state1_openCompetition
        availableDivision.division_maxRegistrationsPerSchool = 3
        availableDivision.save()

        response = self.preview(buildCSV(
            HEADER,
            'Team 10,Division 3,,HW 1,HW 1,Alice,Smith,7,Female',
            'Team 11,Division 4,,HW 1,HW 1,Bob,Smith,7,Male',
        ))
        self.assertContains(response, 'No errors were found')

class TestImportCSVCreate(ImportCSVBase, TestCase):
    def testRedirectsToEventDetails(self):
        response = self.importTeams(buildCSV(HEADER, VALID_ROW))
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('events:details', kwargs={'eventID': self.event.id}), response.url)

    def testCreatesTeam(self):
        self.importTeams(buildCSV(HEADER, VALID_ROW))

        team = Team.objects.get(event=self.event, name='Team 10')
        self.assertEqual(self.division3, team.division)
        self.assertEqual(self.hardwarePlatform, team.hardwarePlatform)
        self.assertEqual(self.softwarePlatform, team.softwarePlatform)
        self.assertIsNone(team.campus)

    def testCreatesStudents(self):
        self.importTeams(buildCSV(HEADER, VALID_ROW))

        team = Team.objects.get(event=self.event, name='Team 10')
        student = team.student_set.get()
        self.assertEqual('Alice', student.firstName)
        self.assertEqual('Smith', student.lastName)
        self.assertEqual(7, student.yearLevel)
        self.assertEqual('female', student.gender)

    def testCreatesMultipleTeamsAndStudents(self):
        self.importTeams(buildCSV(
            FULL_HEADER,
            'Team 10,Division 3,,HW 1,HW 1,Alice,Smith,7,Female,Bob,Smith,8,Male,,,,,,,,',
            'Team 11,Division 4,Campus 1,HW 1,HW 1,Chris,Jones,9,Other,,,,,,,,,,,,',
        ))

        team10 = Team.objects.get(event=self.event, name='Team 10')
        team11 = Team.objects.get(event=self.event, name='Team 11')

        self.assertEqual(2, team10.student_set.count())
        self.assertEqual(1, team11.student_set.count())
        self.assertEqual(self.division4, team11.division)
        self.assertEqual(self.campus1_school1, team11.campus)

    def testSetsMentorUserAndSchool(self):
        self.importTeams(buildCSV(HEADER, VALID_ROW))

        team = Team.objects.get(event=self.event, name='Team 10')
        self.assertEqual(self.user_state1_school1_mentor1, team.mentorUser)
        self.assertEqual(self.school1_state1, team.school)

    def testSetsCSVImported(self):
        self.importTeams(buildCSV(HEADER, VALID_ROW))

        team = Team.objects.get(event=self.event, name='Team 10')
        self.assertTrue(team.csv_imported)

    def testTeamsNotImportedFromCSVAreNotFlagged(self):
        self.assertFalse(self.state1_event1_team1.csv_imported)

    def testIndependentMentorHasNoSchool(self):
        self.loginIndependentMentor5()

        self.importTeams(buildCSV(HEADER_NO_CAMPUS, VALID_ROW_NO_CAMPUS))

        team = Team.objects.get(event=self.event, name='Team 10')
        self.assertEqual(self.user_state1_independent_mentor5, team.mentorUser)
        self.assertIsNone(team.school)

    def testValidationIsRerun(self):
        # A team created between preview and import makes the name a duplicate
        Team.objects.create(
            event = self.event,
            division = self.division3,
            mentorUser = self.user_state1_school1_mentor1,
            school = self.school1_state1,
            name = 'Team 10',
            hardwarePlatform = self.hardwarePlatform,
            softwarePlatform = self.softwarePlatform,
        )
        teamCount = Team.objects.count()

        response = self.importTeams(buildCSV(HEADER, VALID_ROW))

        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Team with this name in this event already exists')
        self.assertEqual(teamCount, Team.objects.count())

    def testTamperedCSVTextRejected(self):
        teamCount = Team.objects.count()
        studentCount = Student.objects.count()

        response = self.importTeams(buildCSV(HEADER, 'Team 10,Not A Division,,HW 1,HW 1,Alice,Smith,7,Female'))

        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'is not a valid option')
        self.assertEqual(teamCount, Team.objects.count())
        self.assertEqual(studentCount, Student.objects.count())

    def testEmptyCSVTextRejected(self):
        teamCount = Team.objects.count()

        response = self.importTeams('')

        self.assertEqual(200, response.status_code)
        self.assertEqual(teamCount, Team.objects.count())

    def testImportIsAtomic(self):
        teamCount = Team.objects.count()
        studentCount = Student.objects.count()

        content = buildCSV(
            HEADER,
            'Team 10,Division 3,,HW 1,HW 1,Alice,Smith,7,Female',
            'Team 11,Division 3,,HW 1,HW 1,Bob,Smith,7,Male',
        )

        # Fail on the second team so the first team and its student must be rolled back
        originalSave = Team.save
        def failOnSecondTeam(team, *args, **kwargs):
            if team.name == 'Team 11':
                raise ValueError('Simulated failure')
            return originalSave(team, *args, **kwargs)

        with patch.object(Team, 'save', failOnSecondTeam):
            with self.assertRaises(ValueError):
                self.importTeams(content)

        self.assertEqual(teamCount, Team.objects.count())
        self.assertEqual(studentCount, Student.objects.count())
