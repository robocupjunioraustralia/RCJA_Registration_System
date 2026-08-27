from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_ipv46_address
from django.http import Http404, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from events.models import Event
from events.views import (
    coordinatorEventDetailsPermissions,
    eventDetailsPermissions,
    mentorEventAttendanceAccessPermissions,
)

from .forms import ChildLookupForm, ParticipationDeedSignForm, AttachStudentForm
from .models import ParticipationDeed
from .tokens import (
    loads_school_or_mentor,
    deeds_available_for_event,
)
from .participants import (
    match_participant,
    attach_deed,
    unattached_deeds_for_context,
    participants_without_deed,
    eligible_workshop_students_queryset,
    mentor_teams_for_context,
    summary_groups_for_event,
    participant_deed_counts,
)
from invoices.models import InvoiceGlobalSettings
from teams.models import Student, Team
from workshops.models import WorkshopAttendee


def _invalid_link_response(request, message='This participation deed link is invalid or has expired.'):
    return render(request, 'participationdeeds/invalid.html', {'message': message}, status=400)


def _client_ip_address(request):
    """Return the client IP, preferring X-Forwarded-For when behind a reverse proxy."""
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        ipAddress = forwarded_for.split(',')[0].strip()
    else:
        ipAddress = (request.META.get('REMOTE_ADDR') or '').strip()
    if not ipAddress:
        return None
    try:
        validate_ipv46_address(ipAddress)
    except ValidationError:
        return None
    return ipAddress


def _mentor_context_for_event(request, event):
    """Return (school, mentorUser) for the current mentor's registration context."""
    filterDict = event.getBaseEventAttendanceFilterDict(request.user)
    school = filterDict.get('school')
    if school is not None:
        return school, None
    return None, request.user


def _mentor_event_access(request, event):
    if not event.electronicParticipationDeedsEnabled:
        raise PermissionDenied('Electronic participation deeds are not enabled for this event.')

    filterDict = event.getBaseEventAttendanceFilterDict(request.user)
    if not eventDetailsPermissions(request, event, filterDict):
        raise PermissionDenied('This event is unavailable')

    if event.boolWorkshop():
        has_reg = WorkshopAttendee.objects.filter(**filterDict).filter(attendeeType='student').exists()
    else:
        has_reg = Team.objects.filter(**filterDict).exists()
    if not has_reg:
        raise PermissionDenied('No registrations for this event.')

    return _mentor_context_for_event(request, event)


def sign_participation_deed(request, token):
    try:
        event, school, mentorUser = loads_school_or_mentor(token)
    except (signing.BadSignature, Event.DoesNotExist, Exception):
        return _invalid_link_response(request)

    if not deeds_available_for_event(event):
        return _invalid_link_response(request)

    lookup_form = ChildLookupForm(request.POST or None)
    sign_form = None
    child_data = None

    if request.method == 'POST':
        if 'parentName' in request.POST:
            # Signing step — child details from hidden fields
            lookup_form = ChildLookupForm({
                'firstName': request.POST.get('firstName', ''),
                'lastName': request.POST.get('lastName', ''),
                'yearLevel': request.POST.get('yearLevel', ''),
            })
            sign_form = ParticipationDeedSignForm(
                request.POST,
                child_first_name=request.POST.get('firstName', ''),
                child_last_name=request.POST.get('lastName', ''),
            )
            if lookup_form.is_valid() and sign_form.is_valid():
                child = lookup_form.cleaned_data
                participant = match_participant(
                    event,
                    child['firstName'],
                    child['lastName'],
                    child['yearLevel'],
                    school=school,
                    mentorUser=mentorUser,
                )
                deed = ParticipationDeed.objects.create(
                    parentName=sign_form.cleaned_data['parentName'],
                    submittedFirstName=child['firstName'].strip(),
                    submittedLastName=child['lastName'].strip(),
                    submittedYearLevel=str(child['yearLevel']).strip(),
                    school=school,
                    mentorUser=mentorUser if school is None else None,
                    originalEvent=event,
                    ipAddress=_client_ip_address(request),
                    userAgent=request.META.get('HTTP_USER_AGENT', '')[:2000],
                    loggedInUser=request.user if request.user.is_authenticated else None,
                )
                if participant is not None and not participant.participationDeed_id:
                    attach_deed(participant, deed)
                return render(request, 'participationdeeds/thanks.html', {'event': event})
            child_data = {
                'firstName': request.POST.get('firstName', ''),
                'lastName': request.POST.get('lastName', ''),
                'yearLevel': request.POST.get('yearLevel', ''),
            }
        elif lookup_form.is_valid():
            child_data = lookup_form.cleaned_data
            sign_form = ParticipationDeedSignForm(
                child_first_name=child_data['firstName'],
                child_last_name=child_data['lastName'],
            )

    return render(request, 'participationdeeds/sign.html', {
        'event': event,
        'school': school,
        'mentorUser': mentorUser,
        'lookup_form': lookup_form,
        'sign_form': sign_form,
        'child_data': child_data,
        'deed_text': event.state.bleachedParticipationDeedText(),
        'invoiceSettings': InvoiceGlobalSettings.objects.first(),
        'today': timezone.localdate(),
        'token': token,
    })


@login_required
def mentor_summary(request, eventID):
    event = get_object_or_404(Event, pk=eventID)
    school, mentorUser = _mentor_event_access(request, event)

    unattached = unattached_deeds_for_context(event, school=school, mentorUser=mentorUser)
    can_attach_deeds = participants_without_deed(event, school=school, mentorUser=mentorUser).exists()
    completeDeedCount, incompleteDeedCount = participant_deed_counts(
        event,
        school=school,
        mentorUser=mentorUser,
    )

    teams = None
    attendees = None
    if event.boolWorkshop():
        attendees = eligible_workshop_students_queryset(event, school=school, mentorUser=mentorUser)
    else:
        teams = mentor_teams_for_context(event, school=school, mentorUser=mentorUser)

    return render(request, 'participationdeeds/mentor_summary.html', {
        'event': event,
        'teams': teams,
        'attendees': attendees,
        'unattached': unattached,
        'can_attach_deeds': can_attach_deeds,
        'completeDeedCount': completeDeedCount,
        'incompleteDeedCount': incompleteDeedCount,
    })


@login_required
def attach_deed_view(request, eventID, deedID):
    event = get_object_or_404(Event, pk=eventID)
    school, mentorUser = _mentor_event_access(request, event)

    deed = get_object_or_404(ParticipationDeed, pk=deedID, originalEvent=event)
    if not mentorEventAttendanceAccessPermissions(request, deed):
        raise PermissionDenied("You do not have permission to view this deed.")

    if deed.isAttached():
        return redirect(reverse('participationdeeds:mentor_summary', kwargs={'eventID': event.id}))

    students = participants_without_deed(event, school=school, mentorUser=mentorUser)
    if not students.exists():
        return redirect(reverse('participationdeeds:mentor_summary', kwargs={'eventID': event.id}))

    form = AttachStudentForm(request.POST or None, students=students)
    if request.method == 'POST' and form.is_valid():
        student = form.cleaned_data['student']
        attach_deed(student, deed)
        return redirect(reverse('participationdeeds:mentor_summary', kwargs={'eventID': event.id}))

    return render(request, 'participationdeeds/attach.html', {
        'event': event,
        'form': form,
        'deed': deed,
    })


@login_required
@require_http_methods(['DELETE'])
def delete_unattached_deed(request, deedID):
    deed = get_object_or_404(ParticipationDeed, pk=deedID)
    _mentor_event_access(request, deed.originalEvent)

    if not mentorEventAttendanceAccessPermissions(request, deed):
        raise PermissionDenied("You do not have permission to delete this deed.")
    if deed.isAttached():
        raise PermissionDenied("Only unattached deeds can be deleted.")

    deed.delete()
    return HttpResponse(status=204)


@login_required
def coordinator_summary(request, eventID):
    event = get_object_or_404(Event, pk=eventID)
    if not coordinatorEventDetailsPermissions(request, event):
        raise PermissionDenied('You do not have permission to view this page.')

    groups = summary_groups_for_event(event) if event.electronicParticipationDeedsEnabled else []

    return render(request, 'participationdeeds/coordinator_summary.html', {
        'event': event,
        'groups': groups,
        'enabled': event.electronicParticipationDeedsEnabled,
    })
