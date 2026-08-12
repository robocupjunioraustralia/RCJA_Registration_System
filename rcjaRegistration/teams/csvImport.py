from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from schools.models import Campus

from .models import Team, Student, HardwarePlatform, SoftwarePlatform
from .forms import TeamForm, StudentForm

import csv
import io
import re

# Uploaded csv is re-posted in a hidden field on the preview page, so keep it small
MAX_UPLOAD_SIZE_BYTES = 1024 * 1024

def normaliseHeader(header):
    return ' '.join(header.split()).lower()

def fieldHeader(model, fieldName):
    return str(model._meta.get_field(fieldName).verbose_name)

# Column names come from the model field names so they stay in sync with the labels on the add team form
TEAM_NAME_HEADER = fieldHeader(Team, 'name')
DIVISION_HEADER = fieldHeader(Team, 'division')
CAMPUS_HEADER = fieldHeader(Team, 'campus')
HARDWARE_PLATFORM_HEADER = fieldHeader(Team, 'hardwarePlatform')
SOFTWARE_PLATFORM_HEADER = fieldHeader(Team, 'softwarePlatform')
GENDER_HEADER = fieldHeader(Student, 'gender')

STUDENT_FIELD_HEADERS = tuple(
    (fieldName, fieldHeader(Student, fieldName)) for fieldName in ('firstName', 'lastName', 'yearLevel', 'gender')
)

studentHeaderRegex = re.compile(
    r'^student\s+(\d+)\s+(' + '|'.join([re.escape(normaliseHeader(fieldLabel)) for fieldName, fieldLabel in STUDENT_FIELD_HEADERS]) + r')$'
)

# *****Headers*****

def campusFieldRelevant(user):
    # Matches the condition that shows the campus field on the add team form
    return Campus.objects.filter(school=user.currentlySelectedSchool).exists()

def studentHeader(studentNumber, fieldLabel):
    return f'Student {studentNumber} {fieldLabel}'

def teamHeaders(user):
    headers = [TEAM_NAME_HEADER, DIVISION_HEADER]

    if campusFieldRelevant(user):
        headers.append(CAMPUS_HEADER)

    headers += [HARDWARE_PLATFORM_HEADER, SOFTWARE_PLATFORM_HEADER]

    return headers

def csvHeaders(event, user):
    headers = teamHeaders(user)

    for studentNumber in range(1, event.maxMembersPerTeam + 1):
        for fieldName, fieldLabel in STUDENT_FIELD_HEADERS:
            headers.append(studentHeader(studentNumber, fieldLabel))

    return headers

# *****Options for display and validation*****

def divisionOptions(event, user):
    # Use the add team form so the division filtering logic is not duplicated
    return TeamForm(user=user, event=event).fields['division'].queryset

def campusOptions(user):
    return Campus.objects.filter(school=user.currentlySelectedSchool)

def genderOptions():
    return [label for value, label in Student.genderOptions]

def genderDisplayName(value):
    # Gender is accepted in any case, show the label from the model rather than what was typed
    return dict(Student.genderOptions).get(value.lower(), value)

def optionsTable(event, user):
    # Returns (headers, rows) with one column per restricted field, padded so it can be rendered as a table
    columns = [(DIVISION_HEADER, [division.name for division in divisionOptions(event, user)])]

    if campusFieldRelevant(user):
        columns.append((CAMPUS_HEADER, [campus.name for campus in campusOptions(user)]))

    columns.append((HARDWARE_PLATFORM_HEADER, [hardwarePlatform.name for hardwarePlatform in HardwarePlatform.objects.all()]))
    columns.append((SOFTWARE_PLATFORM_HEADER, [softwarePlatform.name for softwarePlatform in SoftwarePlatform.objects.all()]))
    columns.append((GENDER_HEADER, genderOptions()))

    headers = [header for header, options in columns]
    rowCount = max([len(options) for header, options in columns])
    rows = [[options[index] if index < len(options) else '' for header, options in columns] for index in range(rowCount)]

    return headers, rows

# *****File reading*****

def readUploadedFile(uploadedFile):
    # Returns (csvText, error)
    if uploadedFile.size > MAX_UPLOAD_SIZE_BYTES:
        return None, f'File is too large. The maximum size is {MAX_UPLOAD_SIZE_BYTES // 1024} KB.'

    try:
        # utf-8-sig so the byte order mark Excel writes is stripped from the first header
        return uploadedFile.read().decode('utf-8-sig'), None
    except UnicodeDecodeError:
        return None, 'File could not be read. Please make sure it is a CSV file saved with UTF-8 encoding.'

# *****Validation*****

class ImportedTeam:
    # Holds one row of the csv, its validation errors and the unsaved forms used to create the team
    # The row is displayed like the team table on the event details page, so errors are grouped by the cell they belong in
    def __init__(self, rowNumber, showCampus):
        self.rowNumber = rowNumber
        self.showCampus = showCampus

        self.name = ''
        self.division = ''
        self.campus = ''
        self.hardwarePlatform = ''
        self.softwarePlatform = ''
        self.students = []

        self.nameErrors = []
        self.divisionErrors = []
        self.campusErrors = []
        self.hardwarePlatformErrors = []
        self.softwarePlatformErrors = []
        self.studentErrors = []

        self.teamForm = None
        self.studentForms = []

    @property
    def errors(self):
        return (
            self.nameErrors + self.divisionErrors + self.campusErrors +
            self.hardwarePlatformErrors + self.softwarePlatformErrors + self.studentErrors
        )

    def errorList(self, fieldName):
        # Errors without a cell of their own, including whole row errors, are shown in the name cell
        errorLists = {
            'division': self.divisionErrors,
            'hardwarePlatform': self.hardwarePlatformErrors,
            'softwarePlatform': self.softwarePlatformErrors,
        }

        if self.showCampus:
            errorLists['campus'] = self.campusErrors

        return errorLists.get(fieldName, self.nameErrors)

def matchHeaders(event, user, headerRow):
    # Returns (columnIndexes, errors); columnIndexes maps expected header to its column in the file
    errors = []
    columnIndexes = {}

    fileHeaders = {}
    for index, header in enumerate(headerRow):
        fileHeaders.setdefault(normaliseHeader(header), index)

    for header in teamHeaders(user):
        if normaliseHeader(header) in fileHeaders:
            columnIndexes[header] = fileHeaders[normaliseHeader(header)]
        else:
            errors.append(f"Required column '{header}' is missing from the file.")

    # Reject student columns beyond the limit for this event, otherwise those students would be silently dropped
    for header in headerRow:
        match = studentHeaderRegex.match(normaliseHeader(header))
        if match and int(match.group(1)) > event.maxMembersPerTeam:
            errors.append(f"Column '{header.strip()}' is not allowed. This event allows a maximum of {event.maxMembersPerTeam} students per team.")
            break

    # Trailing students can be left out of the file entirely, but a student must have all of its columns
    for studentNumber in range(1, event.maxMembersPerTeam + 1):
        studentColumnIndexes = {}
        missingHeaders = []

        for fieldName, fieldLabel in STUDENT_FIELD_HEADERS:
            header = studentHeader(studentNumber, fieldLabel)
            if normaliseHeader(header) in fileHeaders:
                studentColumnIndexes[header] = fileHeaders[normaliseHeader(header)]
            else:
                missingHeaders.append(header)

        if studentNumber == 1 or studentColumnIndexes:
            if missingHeaders:
                for header in missingHeaders:
                    errors.append(f"Required column '{header}' is missing from the file.")
            columnIndexes.update(studentColumnIndexes)

    return columnIndexes, errors

def resolveByName(queryset, name, fieldLabel, errors):
    # Returns (object, lookupFailed)
    if not name:
        return None, False

    try:
        return queryset.get(name__iexact=name), False
    except ObjectDoesNotExist:
        validOptions = ', '.join([str(option) for option in queryset]) or 'none available'
        errors.append(f"{fieldLabel}: '{name}' is not a valid option. Valid options are: {validOptions}.")
    except MultipleObjectsReturned:
        errors.append(f"{fieldLabel}: '{name}' matches more than one option. Please contact the event coordinator.")

    return None, True

def formErrors(form, skipFields=(), prefix=''):
    # Returns a list of (fieldName, message) so each error can be shown against the field it belongs to
    errors = []

    for fieldName, fieldErrors in form.errors.items():
        if fieldName in skipFields:
            continue

        if fieldName == '__all__':
            label = 'Error'
        else:
            label = form.fields[fieldName].label or fieldName

        for fieldError in fieldErrors:
            errors.append((fieldName, f'{prefix}{label}: {fieldError}'))

    return errors

def studentDisplayName(studentData):
    # Matches the students column on the event details page, with the gender added
    name = f"{studentData['firstName']} {studentData['lastName']}".strip()
    details = ', '.join([detail for detail in (studentData['yearLevel'], genderDisplayName(studentData['gender'])) if detail])

    if details:
        return f'{name} ({details})'

    return name

class RegistrationLimits:
    # Tracks registration counts across the whole csv so a batch cannot exceed a limit that a single team would not
    def __init__(self, event, user):
        self.event = event
        self.user = user
        self.filterDict = event.getBaseEventAttendanceFilterDict(user)

        self.schoolCount = event.baseeventattendance_set.filter(**self.filterDict).count()
        self.totalCount = event.baseeventattendance_set.count()

        self.availableDivisions = {availableDivision.division_id: availableDivision for availableDivision in event.availabledivision_set.all()}
        self.divisionSchoolCounts = {}
        self.divisionTotalCounts = {}

    def divisionSchoolCount(self, availableDivision):
        if availableDivision.division_id not in self.divisionSchoolCounts:
            self.divisionSchoolCounts[availableDivision.division_id] = availableDivision.division.baseeventattendance_set.filter(**self.filterDict).count()

        return self.divisionSchoolCounts[availableDivision.division_id]

    def divisionTotalCount(self, availableDivision):
        if availableDivision.division_id not in self.divisionTotalCounts:
            self.divisionTotalCounts[availableDivision.division_id] = availableDivision.division.baseeventattendance_set.filter(event=self.event).count()

        return self.divisionTotalCounts[availableDivision.division_id]

    def checkAndCount(self, division, errors):
        event = self.event
        registrationName = event.registrationName()

        if event.event_maxRegistrationsPerSchool is not None and self.schoolCount >= event.event_maxRegistrationsPerSchool:
            errors.append(f'Max {registrationName}s for school for this event reached. Contact the organiser if you want to register more {registrationName}s for this event.')

        if event.event_maxRegistrationsForEvent is not None and self.totalCount >= event.event_maxRegistrationsForEvent:
            errors.append(f'Max {registrationName}s for this event reached. Contact the organiser if you want to register more {registrationName}s for this event.')

        self.schoolCount += 1
        self.totalCount += 1

        if division is None:
            return

        availableDivision = self.availableDivisions.get(division.id)
        if availableDivision is None:
            return

        if availableDivision.division_maxRegistrationsPerSchool is not None:
            if self.divisionSchoolCount(availableDivision) >= availableDivision.division_maxRegistrationsPerSchool:
                errors.append(f'{division}: Max {registrationName}s for school for this event division reached. Contact the organiser if you want to register more {registrationName}s in this division.')

            self.divisionSchoolCounts[availableDivision.division_id] += 1

        if availableDivision.division_maxRegistrationsForDivision is not None:
            if self.divisionTotalCount(availableDivision) >= availableDivision.division_maxRegistrationsForDivision:
                errors.append(f'{division}: Max {registrationName}s for this event division reached. Contact the organiser if you want to register more {registrationName}s in this division.')

            self.divisionTotalCounts[availableDivision.division_id] += 1

def validateRow(event, user, importedTeam, cells, columnIndexes, options, limits):
    def cellValue(header):
        index = columnIndexes.get(header)
        if index is None or index >= len(cells):
            return ''
        return cells[index].strip()

    # Resolve names to primary keys because the form fields are model choice fields
    lookupFailedFields = []

    def resolveCell(fieldName, header, queryset):
        value, lookupFailed = resolveByName(queryset, cellValue(header), header, importedTeam.errorList(fieldName))
        if lookupFailed:
            lookupFailedFields.append(fieldName)
        return value

    division = resolveCell('division', DIVISION_HEADER, options['division'])
    hardwarePlatform = resolveCell('hardwarePlatform', HARDWARE_PLATFORM_HEADER, options['hardwarePlatform'])
    softwarePlatform = resolveCell('softwarePlatform', SOFTWARE_PLATFORM_HEADER, options['softwarePlatform'])

    campus = None
    if CAMPUS_HEADER in columnIndexes:
        campus = resolveCell('campus', CAMPUS_HEADER, options['campus'])

    # Show the matched object where there is one so the mentor can see what the text in their file matched
    importedTeam.name = cellValue(TEAM_NAME_HEADER)
    importedTeam.division = division or cellValue(DIVISION_HEADER)
    importedTeam.campus = campus or cellValue(CAMPUS_HEADER)
    importedTeam.hardwarePlatform = hardwarePlatform or cellValue(HARDWARE_PLATFORM_HEADER)
    importedTeam.softwarePlatform = softwarePlatform or cellValue(SOFTWARE_PLATFORM_HEADER)

    # School and event are disabled fields on the form so are set from the form initial, same as the add team form
    teamForm = TeamForm(
        data = {
            'name': cellValue(TEAM_NAME_HEADER),
            'division': division.id if division else None,
            'campus': campus.id if campus else None,
            'hardwarePlatform': hardwarePlatform.id if hardwarePlatform else None,
            'softwarePlatform': softwarePlatform.id if softwarePlatform else None,
        },
        user = user,
        event = event,
    )
    teamForm.is_valid()
    for fieldName, message in formErrors(teamForm, skipFields=lookupFailedFields):
        importedTeam.errorList(fieldName).append(message)
    importedTeam.teamForm = teamForm

    # Students
    for studentNumber in range(1, event.maxMembersPerTeam + 1):
        studentData = {}
        for fieldName, fieldLabel in STUDENT_FIELD_HEADERS:
            studentData[fieldName] = cellValue(studentHeader(studentNumber, fieldLabel))

        # A student left blank is skipped, a partially filled student is an error
        if not any(studentData.values()):
            continue

        # Gender is accepted in any case
        studentData['gender'] = studentData['gender'].lower()

        importedTeam.students.append(studentDisplayName(studentData))

        studentForm = StudentForm(data=studentData)
        studentForm.is_valid()
        for fieldName, message in formErrors(studentForm, prefix=f'Student {studentNumber} '):
            importedTeam.studentErrors.append(message)
        importedTeam.studentForms.append(studentForm)

    if not importedTeam.studentForms:
        importedTeam.studentErrors.append('At least one student is required.')

    limits.checkAndCount(division, importedTeam.nameErrors)

def parseAndValidateCSV(event, user, csvText):
    # Validates the csv without touching the database
    # Returns (importedTeams, fileErrors)
    try:
        # newline='' so the csv module handles the line endings, as it does for a file opened for csv reading
        allRows = [row for row in csv.reader(io.StringIO(csvText, newline=''))]
    except csv.Error as error:
        return [], [f'File could not be read as a CSV: {error}']

    # Ignore blank lines, including the trailing newline Excel adds
    allRows = [row for row in allRows if any(cell.strip() for cell in row)]

    if not allRows:
        return [], ['The file is empty. Please download the template and fill it out.']

    columnIndexes, headerErrors = matchHeaders(event, user, allRows[0])
    if headerErrors:
        return [], headerErrors

    dataRows = allRows[1:]
    if not dataRows:
        return [], ['The file does not contain any teams.']

    limits = RegistrationLimits(event, user)
    options = {
        'division': divisionOptions(event, user),
        'campus': campusOptions(user),
        'hardwarePlatform': HardwarePlatform.objects.all(),
        'softwarePlatform': SoftwarePlatform.objects.all(),
    }
    importedTeams = []
    seenNames = {}

    for rowNumber, cells in enumerate(dataRows, start=2):
        importedTeam = ImportedTeam(rowNumber, CAMPUS_HEADER in columnIndexes)
        validateRow(event, user, importedTeam, cells, columnIndexes, options, limits)

        # Team.clean only checks for duplicate names already in the database
        name = importedTeam.teamForm.data.get('name')
        if name:
            if name in seenNames:
                importedTeam.nameErrors.append(f'{TEAM_NAME_HEADER}: Duplicate of the team on row {seenNames[name]} of this file.')
            else:
                seenNames[name] = rowNumber

        importedTeams.append(importedTeam)

    return importedTeams, []

def hasErrors(importedTeams):
    return any(importedTeam.errors for importedTeam in importedTeams)
