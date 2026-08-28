from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import Count, F, Q
from django.conf import settings
from django.urls import reverse
from coordination.permissions import checkCoordinatorPermission

import datetime, csv
import jwt

from .models import Event, BaseEventAttendance, Year, DivisionCategory, Division
from regions.models import State
from teams.models import Team, Student
from schools.models import Campus
from workshops.models import WorkshopAttendee
from .forms import getSummaryForm, getAdminEventsForm

from participationdeeds.tokens import dumps_school_or_mentor, deeds_available_for_event
from participationdeeds.participants import team_deed_counts, unattached_deeds_for_context, participant_deed_counts

# Need to check if schooladministrator is None

@login_required
def dashboard(request):
    # Events
    # Get user event filtering attributes
    if request.user.currentlySelectedSchool:
        usersEventAttendances = BaseEventAttendance.objects.filter(school=request.user.currentlySelectedSchool)
    else:
        usersEventAttendances = BaseEventAttendance.objects.filter(mentorUser=request.user, school=None)

    # Current state
    if request.user.currentlySelectedSchool:
        currentState = request.user.currentlySelectedSchool.state
    else:
        currentState = request.user.homeState

    # Get open events
    openForRegistrationEvents = Event.objects.filter(
        status='published',
        registrationsOpenDate__lte=datetime.datetime.today(),
        registrationsCloseDate__gte=datetime.datetime.today(),
    ).exclude(
        baseeventattendance__in=usersEventAttendances,
    ).prefetch_related('state', 'year').order_by('startDate').distinct()

    eventsAvailable = openForRegistrationEvents.exists()

    # Get not open events
    futureEvents = Event.objects.filter(
        Q(registrationsOpenDate__gt=datetime.datetime.today()) | Q(registrationsOpenDate__isnull=True),
        Q(startDate__gt=datetime.datetime.today()) | Q(startDate__isnull=True),
        status='published',
    ).exclude(
        pk__in=openForRegistrationEvents.values_list('pk', flat=True),
    ).exclude(
        baseeventattendance__in=usersEventAttendances,
    ).prefetch_related('state', 'year').order_by('startDate').distinct()

    # Filter open and future events by state
    if request.method == 'GET' and not 'viewAll' in request.GET:
        openForRegistrationEvents = openForRegistrationEvents.filter(Q(state=currentState) | Q(globalEvent=True) | Q(state__typeGlobal=True))
        futureEvents = futureEvents.filter(Q(state=currentState) | Q(globalEvent=True) | Q(state__typeGlobal=True))

    # Split competitions and workshops
    openForRegistrationCompetitions = openForRegistrationEvents.filter(eventType='competition')
    openForRegistrationWorkshops = openForRegistrationEvents.filter(eventType='workshop')

    # Get current and past events
    currentEvents = Event.objects.filter(
        endDate__gte=datetime.datetime.today(),
        baseeventattendance__in=usersEventAttendances,
        status="published",
    ).distinct().prefetch_related('state', 'year').order_by('startDate').distinct()

    pastEvents = Event.objects.filter(
        endDate__lt=datetime.datetime.today(),
        baseeventattendance__in=usersEventAttendances,
        status="published",
    ).prefetch_related('state', 'year').order_by('-startDate').distinct()

    # Invoices
    from invoices.models import Invoice
    invoices = Invoice.invoicesForUser(request.user)

    outstandingInvoices = sum([1 for invoice in invoices if invoice.amountDueInclGST() > 0.05]) # Rounded because consistent with what user sees and not used in subsequent calculations

    # Association join prompt
    showAssociationPrompt = not request.user.associationPromptShown
    if showAssociationPrompt:
        request.user.associationPromptShown = True
        request.user.save(update_fields=['associationPromptShown'], skipPrePostSave=True)

    context = {
        'futureEvents': futureEvents,
        'openForRegistrationCompetitions': openForRegistrationCompetitions,
        'openForRegistrationWorkshops': openForRegistrationWorkshops,
        'currentEvents': currentEvents,
        'pastEvents': pastEvents,
        'outstandingInvoices': outstandingInvoices,
        'invoices': invoices,
        'currentState': currentState,
        'eventsAvailable': eventsAvailable,
        'showAssociationPrompt': showAssociationPrompt
    }
    return render(request, 'events/dashboard.html', context)

def coordinatorEventDetailsPermissions(request, event):
    return checkCoordinatorPermission(request, Event, event, 'view')

def coordinatorInvoiceViewPermissions(request, event):
    from invoices.models import Invoice
    return checkCoordinatorPermission(request, Invoice, event, 'view')

def eventDetailsPermissions(request, event, filterDict):
    if coordinatorEventDetailsPermissions(request, event):
        return True

    if not event.published():
        return False

    if event.registrationsOpen():
        return True

    if event.registrationNotOpenYet():
        return True

    if BaseEventAttendance.objects.filter(**filterDict).exists():
        return True

    return False

def getDivisionsMaxReachedWarnings(event, user):
    # Get list of divisions that reached max number of teams
    divisionsMaxReachedWarnings = []
    for availableDivision in event.availabledivision_set.prefetch_related('division').all():
        if availableDivision.maxDivisionRegistrationsForSchoolReached(user):
            divisionsMaxReachedWarnings.append(f"{availableDivision.division}: Max {event.registrationName()}s for school for this event division reached. Contact the organiser if you want to register more {event.registrationName()}s in this division.")

        if availableDivision.maxDivisionRegistrationsTotalReached():
            divisionsMaxReachedWarnings.append(f"{availableDivision.division}: Max {event.registrationName()}s for this event division reached. Contact the organiser if you want to register more {event.registrationName()}s in this division.")

    return divisionsMaxReachedWarnings

def getAvailableToCopyTeams(request, event):
    # Get team filter dict
    filterDict = event.getBaseEventAttendanceFilterDict(request.user)

    # Get teams already copied
    copiedTeamsList = Team.objects.filter(**filterDict).filter(copiedFrom__isnull=False).values_list('copiedFrom', flat=True)

    # Replace event filtering with year filtering for current and previous event year
    del filterDict['event']
    filterDict['event__year__year__gte'] = event.year.year - 1
    filterDict['event__year__year__lte'] = event.year.year
    filterDict['event__status'] = 'published'

    availableDivisions = event.availabledivision_set.values_list('division', flat=True)

    # Get teams available to copy
    teams = Team.objects.filter(**filterDict)
    teams = teams.exclude(event=event) # Exclude teams of the current event
    availableToCopyTeams = teams.exclude(pk__in=copiedTeamsList) # Exclude already copied teams

    return teams, copiedTeamsList, availableToCopyTeams

@login_required
def details(request, eventID):
    event = get_object_or_404(Event, pk=eventID)

    # Get team and workshop attendee filter dict
    filterDict = event.getBaseEventAttendanceFilterDict(request.user)

    if not eventDetailsPermissions(request, event, filterDict):
        raise PermissionDenied("This event is unavailable")

    # Filter team or workshop attendee
    if event.boolWorkshop():
        teams = Team.objects.none()
        workshopAttendees = WorkshopAttendee.objects.filter(**filterDict)
    else:
        teams = Team.objects.filter(**filterDict)
        teams = teams.prefetch_related('student_set', 'division', 'campus', 'event')
        workshopAttendees = WorkshopAttendee.objects.none()

    # Get billing type label
    if event.boolWorkshop():
        billingTypeLabel = 'attendee'
    else:
        billingTypeLabel = event.competition_billingType

    _, _, availableToCopyTeams = getAvailableToCopyTeams(request, event)

    # Total registrations count for admins, excluding withdrawn teams
    if event.boolWorkshop():
        totalRegistrations = event.baseeventattendance_set.count()
    else:
        totalRegistrations = event.baseeventattendance_set.exclude(team__withdrawn=True).count()

    electronicParticipationDeedsEnabled = event.electronicParticipationDeedsEnabled
    schoolMagicLink = None
    unattachedDeedCount = 0
    completeDeedCount = 0
    incompleteDeedCount = 0
    teamDeedSummaries = {}

    hasStudentRegistrations = (teams.exists() or workshopAttendees.filter(attendeeType='student').exists())
    electronicParticipationDeedsAvailable = electronicParticipationDeedsEnabled and hasStudentRegistrations
    if electronicParticipationDeedsAvailable:
        school = filterDict.get('school')
        mentorUser = request.user if school is None else None 
        if deeds_available_for_event(event):
            token = dumps_school_or_mentor(event, school=school, mentorUser=mentorUser)
            schoolMagicLink = request.build_absolute_uri(
                reverse('participationdeeds:sign_participation_deed', kwargs={'token': token})
            )
        unattachedDeedCount = unattached_deeds_for_context(event, school=school, mentorUser=mentorUser).count()
        completeDeedCount, incompleteDeedCount = participant_deed_counts(
            event,
            school=school,
            mentorUser=mentorUser,
        )
        if not event.boolWorkshop():
            for team in teams:
                complete, total = team_deed_counts(team)
                team.deedSummary = f"{complete}/{total}"
                teamDeedSummaries[team.id] = (complete, total)

    context = {
        'event': event,
        'availableDivisions': event.availabledivision_set.prefetch_related('division'),
        'divisionPricing': event.availabledivision_set.exclude(division_billingType='event').exists(),
        'teams': teams,
        'workshopAttendees': workshopAttendees,
        'showCampusColumn': BaseEventAttendance.objects.filter(**filterDict).exclude(campus=None).exists(),
        'billingTypeLabel': billingTypeLabel,
        'hasAdminPermissions': coordinatorEventDetailsPermissions(request, event),
        'hasInvoiceViewPermissions': coordinatorInvoiceViewPermissions(request, event),
        'maxEventRegistrationsForSchoolReached': event.maxEventRegistrationsForSchoolReached(request.user),
        'maxEventRegistrationsTotalReached': event.maxEventRegistrationsTotalReached(),
        'divisionsMaxReachedWarnings': getDivisionsMaxReachedWarnings(event, request.user),
        'duplicateTeamsAvailable': availableToCopyTeams.exists(),
        'totalRegistrations': totalRegistrations,
        'electronicParticipationDeedsEnabled': electronicParticipationDeedsEnabled,
        'electronicParticipationDeedsAvailable': electronicParticipationDeedsAvailable,
        'schoolMagicLink': schoolMagicLink,
        'unattachedDeedCount': unattachedDeedCount,
        'completeDeedCount': completeDeedCount,
        'incompleteDeedCount': incompleteDeedCount,
        'teamDeedSummaries': teamDeedSummaries,
    }
    return render(request, 'events/details.html', context)

def cms(request, eventID):
    event = get_object_or_404(Event, pk=eventID)

    if event.cmsEventId:
        return redirect(settings.CMS_EVENT_URL_VIEW.replace("{EVENT_ID}", event.cmsEventId))

    # Check permissions for cms event creation
    # Only challenge coordinators with permission to change the event can create the CMS event instance for competitions
    if event.eventType != 'competition':
        raise PermissionDenied("The CMS for this event is unavailable")

    if not checkCoordinatorPermission(request, Event, event, 'change'):
        raise PermissionDenied("The CMS for this event is unavailable")

    cmsPayload = {
        "event": event.id,
        "user": request.user.id,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=settings.CMS_JWT_EXPIRY_MINUTES)
    }
    cmsToken = jwt.encode(cmsPayload, settings.CMS_JWT_SECRET, algorithm='HS256')
    return redirect(settings.CMS_EVENT_URL_CREATE.replace("{TOKEN}", cmsToken))

@login_required
def loggedInUnderConstruction(request):
    return render(request,'common/loggedInUnderConstruction.html')

def mentorEventAttendanceAccessPermissions(request, eventAttendance):
    if request.user.currentlySelectedSchool:
        # If user is a school administrator can only edit the currently selected school
        if request.user.currentlySelectedSchool != eventAttendance.school:
            return False

    else:
        # If not a school administrator allow editing individually entered eventAttendances
        if eventAttendance.mentorUser != request.user or eventAttendance.school:
            return False

    return True

def createPermissionForEvent(event, eventType):
    # Check is correct event type
    if event.eventType != eventType:
        raise PermissionDenied('Teams/ attendees cannot be created for this event type')

    # Check registrations open
    if not event.registrationsOpen():
        raise PermissionDenied("Registration has closed for this event")

    # Check event is published
    if not event.published():
        raise PermissionDenied("Event is not published")

def checkEventLimitsReached(request, event):
    if event.maxEventRegistrationsForSchoolReached(request.user):
        raise PermissionDenied(f"Max {event.registrationName()}s for school for this event reached. Contact the organiser if you want to register more {event.registrationName()}s for this event.")

    if event.maxEventRegistrationsTotalReached():
        raise PermissionDenied(f"Max {event.registrationName()}s for this event reached. Contact the organiser if you want to register more {event.registrationName()}s for this event.")

class CreateEditBaseEventAttendance(LoginRequiredMixin, View):
    def common(self, request, event, eventAttendance):
        createPermissionForEvent(event, self.eventType)

        # Check administrator of this eventAttendance
        if eventAttendance and not mentorEventAttendanceAccessPermissions(request, eventAttendance):
            raise PermissionDenied("You are not an administrator of this team/ attendee")

        if not eventAttendance:
            checkEventLimitsReached(request, event)

    def delete(self, request, teamID=None, attendeeID=None, eventID=None, sourceTeamID=None):
        # This endpoint should never be called with eventID or sourceTeamID
        if eventID or sourceTeamID:
            return HttpResponseForbidden()
        
        # Accept multiple variables because used for both teams and workshops
        # Need to lookup the relevant one
        eventAttendanceID = None
        if teamID is not None:
            eventAttendanceID = teamID
        if attendeeID is not None:
            eventAttendanceID = attendeeID

        eventAttendance = get_object_or_404(BaseEventAttendance, pk=eventAttendanceID)
        event = eventAttendance.event
        self.common(request, event, eventAttendance)

        # Delete team
        eventAttendance.delete()
        return HttpResponse(status=204)

# Event summary pages

def getEventsForSummary(state, year):
    """ Create list of event dictionaries of all events in state and year """
    eventList = Event.objects.filter(state = state, year = year).order_by('startDate', 'endDate')

    # Find information for events
    events = []
    for event in eventList:
        eventDict = {}
        eventDict["name"] = event.name

        if event.startDate==event.endDate:
            if event.startDate is not None:
                eventDict["date"] = event.startDate.strftime('%d/%m/%Y')
            else:
                eventDict["date"] = None
        else:
            eventDict["date"] = f"{event.startDate.strftime('%d/%m/%Y')} - {event.endDate.strftime('%d/%m/%Y')}"

        if event.eventType == "competition":
            # Initialise counting variables
            teamNumber = 0
            studentNumber = 0
            maleNumber = 0
            femaleNumber = 0
            otherNumber = 0

            # Count all teams
            attendances = BaseEventAttendance.objects.filter(event=event)
            for attendance in attendances:
                teamNumber += 1
                students = Student.objects.filter(team=attendance.childObject())
                for student in students:
                    studentNumber += 1
                    if student.gender == "male":
                        maleNumber += 1
                    elif student.gender == "female":
                        femaleNumber += 1
                    else:
                        otherNumber += 1

            # Create output
            if studentNumber > 0:
                mPercent = round(maleNumber/studentNumber*100)
                fPercent = round(femaleNumber/studentNumber*100)
                oPercent = round(otherNumber/studentNumber*100)
            else:
                mPercent, fPercent, oPercent = [0,0,0]
            eventDict["participants_one"] = f"Teams: {teamNumber}"
            eventDict["participants_two"] = f"Students: {studentNumber}"
            eventDict["participants_three"] = f"{fPercent}%F, {mPercent}%M, {oPercent}% other"
        else: # Workshop
            # Initialise counting variables
            studentNumber = 0
            teacherNumber = 0
            maleNumber = 0
            femaleNumber = 0
            otherNumber = 0

            # Count all students
            attendances = BaseEventAttendance.objects.filter(event=event)
            for attendance in attendances:
                attendance = attendance.childObject()
                if attendance.attendeeType == "student":
                    studentNumber += 1
                else:
                    teacherNumber += 1
                if attendance.gender == "male":
                    maleNumber += 1
                elif attendance.gender == "female":
                    femaleNumber += 1
                else:
                    otherNumber += 1

            # Create output
            if studentNumber + teacherNumber > 0:
                mPercent = round(maleNumber/(studentNumber+teacherNumber)*100)
                fPercent = round(femaleNumber/(studentNumber+teacherNumber)*100)
                oPercent = round(otherNumber/(studentNumber+teacherNumber)*100)
            else:
                mPercent, fPercent, oPercent = [0,0,0]
            eventDict["participants_one"] = f"Students: {studentNumber}"
            eventDict["participants_two"] = f"Teachers: {teacherNumber}"
            eventDict["participants_three"] = f"{fPercent}%F, {mPercent}%M, {oPercent}% other"

        if event.venue != None:
            eventDict["location"] = event.venue.name
        else:
            eventDict["location"] = "None"

        events.append(eventDict)

    return events

@login_required
def summaryReport(request):
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to view this page")

    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    form = getSummaryForm(request)
    if form.is_valid():
        selected_state = State.objects.get(id = form.cleaned_data["state"])
        selected_year = Year.objects.get(year = form.cleaned_data["year"])
        events = getEventsForSummary(selected_state, selected_year)
    else:
        events = []
        selected_state = None
        selected_year = None

    context = {
        "events": events,
        "form": form,
        'state': selected_state,
        'year': selected_year,
    }
    return render(request, 'events/summaryReport.html', context)


@login_required
def singlePageAdminSummary(request, eventID):
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to view this page")

    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    event = get_object_or_404(Event, pk=eventID)

    if not coordinatorEventDetailsPermissions(request, event):
        raise PermissionDenied("You do not have permission to view this page") 

    if event.boolWorkshop():
        context = getAdminWorkshopSummary(event)
        context["column1"] = "Students"
        context["column0"] = "Teachers"
        return render(request, 'events/adminDetails.html', context)
    else:
        context = getAdminCompetitionSummary(event)
        context["column1"] = "Students"
        context["column0"] = "Teams"
        return render(request, 'events/adminDetails.html', context)

@login_required
def eventAdminSummary(request):
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to view this page")

    output = ""
    if request.method == "POST":
        form = getAdminEventsForm(request)
        if form.is_valid():
            output = form.cleaned_data
            if len(form.cleaned_data['workshops']):
                events_list = form.cleaned_data['workshops']
                columnHeadings = ["Teachers", "Students"]
                summaryFunction = getAdminWorkshopSummary
            else:
                events_list = form.cleaned_data['competitions']
                columnHeadings = ["Teams", "Students"]
                summaryFunction = getAdminCompetitionSummary

            if len(events_list)==1 and not form.cleaned_data['csv']:
                event = get_object_or_404(Event, pk=events_list[0])
                context = summaryFunction(event)
                context["column0"] = columnHeadings[0]
                context["column1"] = columnHeadings[1]
                return render(request, 'events/adminDetails.html', context)

            else:
                events = [summaryFunction(get_object_or_404(Event, pk=event_id)) for event_id in events_list]
                context = mergeMultipleAdminSummary(events)
                context["column0"] = columnHeadings[0]
                context["column1"] = columnHeadings[1]

                if form.cleaned_data['csv']:
                    return summary_csv(context)
                else:
                    return render(request, 'events/adminMultiDetails.html', context)

    else:
        form = getAdminEventsForm(request)
    return render(request, "events/adminBlank.html", {"form": form, 'output':output})

def mergeMultipleAdminSummary(events):
    comps_number = len(events)
    total_col1 = [0]*comps_number
    total_col0 = [0]*comps_number

    categoriesCol1 = {}
    categoriesCol0 = {}
    for i, event in enumerate(events):
        for cat_id, category in event["division_data"].items():
            categoryCol1 = categoriesCol1.get(cat_id, {
                "name": category["name"],
                "rows": {},
                "subtotal": comps_number*[0],
            })

            categoryCol0 = categoriesCol0.get(cat_id, {
                "name": category["name"],
                "rows": {},
                "subtotal": comps_number*[0],
            })

            for row in category["rows"]:
                _cat_id, div_name, col1, col0 = row
                c_1 = categoryCol1["rows"].get(div_name, [div_name] + comps_number*[0])
                c_0 = categoryCol0["rows"].get(div_name, [div_name] + comps_number*[0])
                c_1[i+1] = col1
                c_0[i+1] = col0
                categoryCol1["rows"][div_name] = c_1
                categoryCol0["rows"][div_name] = c_0
            
            categoryCol0["subtotal"][i] = category["subtotal"][1]
            categoryCol1["subtotal"][i] = category["subtotal"][0]
            categoriesCol1[cat_id] = categoryCol1
            categoriesCol0[cat_id] = categoryCol0

    for category in categoriesCol1.values():
        category["size"] = len(category["rows"]) + 1
    for category in categoriesCol0.values():
        category["size"] = len(category["rows"]) + 1

    # Schools
    schools = {}
    for i, event in enumerate(events):
        for school_name, col1, col0 in event["school_data"]:
            school = schools.get(school_name, {'name':school_name,'col1':[0]*comps_number,'col0':[0]*comps_number})
            school['col1'][i] += col1
            school['col0'][i] += col0
            schools[school_name] = school
            total_col1[i] += col1
            total_col0[i] += col0
    event_headers = [event["header"] for event in events]
    context = {'catCol1': categoriesCol1,
               'catCol0': categoriesCol0,
               'schools': schools,
               'events': event_headers,
               'total': {"col1": total_col1, "col0": total_col0}}
    return context

def _build_division_data(category_subtotal_data, division_grouping_data):
    """Pair division rows with category subtotals. Both sequences are ordered by category id."""
    division_data = {}
    division_grouping_index = 0

    for category in category_subtotal_data:
        rows = []
        while True:
            if (
                len(division_grouping_data) <= division_grouping_index
                or division_grouping_data[division_grouping_index][0] > category[0]
            ):
                break
            elif division_grouping_data[division_grouping_index][0] == category[0]:
                rows.append(division_grouping_data[division_grouping_index])
                division_grouping_index += 1
            else:
                division_grouping_index += 1

        division_data[category[0]] = {
            "name": category[1],
            "rows": rows,
            "subtotal": (category[2], category[3]),
            "size": len(rows) + 1,
        }

    return division_data


def _event_summary_context(event, category_subtotal_data, division_grouping_data, school_grouping_data):
    return {
        "name": event.name,
        "header": str(event),
        "year": str(event.year),
        "division_data": _build_division_data(category_subtotal_data, division_grouping_data),
        "school_data": school_grouping_data,
        "total": [
            sum(category[2] for category in category_subtotal_data),
            sum(category[3] for category in category_subtotal_data),
        ],
    }


def _append_independent_school(school_grouping_data, col1, col0):
    if col1 or col0:
        school_grouping_data.append(('Independent', col1, col0))
    return school_grouping_data


def _annotated_tuples(queryset, *fields):
    return [tuple(row[field] for field in fields) for row in queryset]


def getAdminCompetitionSummary(event):
    teams = Team.objects.filter(event=event, division__category__isnull=False)

    division_grouping_data = _annotated_tuples(
        teams.values('division__category_id', 'division__name', 'division_id')
        .annotate(
            student_count=Count('student'),
            team_count=Count('pk', distinct=True),
        )
        .order_by('division__category_id', 'division_id'),
        'division__category_id',
        'division__name',
        'student_count',
        'team_count',
    )

    category_subtotal_data = _annotated_tuples(
        teams.filter(division__in=event.divisions.all())
        .values('division__category_id', 'division__category__name')
        .annotate(
            student_count=Count('student'),
            team_count=Count('pk', distinct=True),
        )
        .order_by('division__category_id'),
        'division__category_id',
        'division__category__name',
        'student_count',
        'team_count',
    )

    school_grouping_data = _annotated_tuples(
        Team.objects.filter(event=event, school__isnull=False)
        .values('school__name')
        .annotate(
            team_count=Count('pk', distinct=True),
            student_count=Count('student'),
        )
        .order_by('school__name'),
        'school__name',
        'team_count',
        'student_count',
    )

    independent = Team.objects.filter(event=event, school__isnull=True).aggregate(
        team_count=Count('pk', distinct=True),
        student_count=Count('student'),
    )
    school_grouping_data = _append_independent_school(
        school_grouping_data,
        independent['team_count'],
        independent['student_count'],
    )

    return _event_summary_context(
        event,
        category_subtotal_data,
        division_grouping_data,
        school_grouping_data,
    )

def getAdminWorkshopSummary(event: Event):
    event_category_ids = event.divisions.exclude(category_id=None).values('category_id')

    division_grouping_data = list(
        Division.objects.filter(category_id__in=event_category_ids)
        .annotate(
            student_count=Count(
                'baseeventattendance',
                filter=Q(
                    baseeventattendance__event=event,
                    baseeventattendance__workshopattendee__attendeeType='student',
                ),
            ),
            teacher_count=Count(
                'baseeventattendance',
                filter=Q(
                    baseeventattendance__event=event,
                    baseeventattendance__workshopattendee__attendeeType='teacher',
                ),
            ),
        )
        .order_by('category_id', 'id')
        .values_list('category_id', 'name', 'student_count', 'teacher_count')
    )

    category_subtotal_data = list(
        DivisionCategory.objects.filter(pk__in=event_category_ids)
        .annotate(
            student_count=Count(
                'division__baseeventattendance',
                filter=Q(
                    division__baseeventattendance__event=event,
                    division__baseeventattendance__workshopattendee__attendeeType='student',
                ),
            ),
            teacher_count=Count(
                'division__baseeventattendance',
                filter=Q(
                    division__baseeventattendance__event=event,
                    division__baseeventattendance__workshopattendee__attendeeType='teacher',
                ),
            ),
        )
        .order_by('id')
        .values_list('id', 'name', 'student_count', 'teacher_count')
    )

    school_grouping_data = list(
        WorkshopAttendee.objects.filter(event=event, school__isnull=False)
        .values('school__name')
        .annotate(
            student_count=Count('pk', filter=Q(attendeeType='student')),
            teacher_count=Count('pk', filter=Q(attendeeType='teacher')),
        )
        .order_by('school__name')
        .values_list('school__name', 'student_count', 'teacher_count')
    )

    independent = WorkshopAttendee.objects.filter(event=event, school__isnull=True).aggregate(
        students=Count('pk', filter=Q(attendeeType='student')),
        teachers=Count('pk', filter=Q(attendeeType='teacher')),
    )
    school_grouping_data = _append_independent_school(
        school_grouping_data,
        independent['students'],
        independent['teachers'],
    )

    return _event_summary_context(
        event,
        category_subtotal_data,
        division_grouping_data,
        school_grouping_data,
    )

def summary_csv(context: dict[str, str]):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Attendance Summary.csv"'
    t = loader.get_template("events/adminCsv.txt")
    response.write(t.render(context))
    return response
