from teams.models import Student
from workshops.models import WorkshopAttendee
from participationdeeds.models import ParticipationDeed



def school_for_participant(participant):
    """Return the school for a competition student or workshop attendee."""
    if isinstance(participant, Student):
        return participant.team.school
    return participant.school

def mentor_for_participant(participant):
    """Return the mentor user for a competition student or workshop attendee."""
    if isinstance(participant, Student):
        return participant.team.mentorUser
    return participant.mentorUser

def eligible_students_queryset(event, school=None, mentorUser=None):
    """Return competition students for an event, filtered to a school or independent mentor."""
    qs = Student.objects.filter(team__event=event).select_related('team', 'participationDeed')
    if school is not None:
        qs = qs.filter(team__school=school)
    else:
        qs = qs.filter(team__school=None, team__mentorUser=mentorUser)
    return qs


def eligible_workshop_students_queryset(event, school=None, mentorUser=None):
    """Return workshop student attendees for an event, filtered to a school or independent mentor."""
    qs = WorkshopAttendee.objects.filter(event=event, attendeeType='student').select_related('participationDeed')
    if school is not None:
        qs = qs.filter(school=school)
    else:
        qs = qs.filter(school=None, mentorUser=mentorUser)
    return qs


def eligible_participants(event, school=None, mentorUser=None):
    """Return all eligible participants for an event as a list (workshop or competition)."""
    if event.boolWorkshop():
        return eligible_workshop_students_queryset(event, school=school, mentorUser=mentorUser)
    return eligible_students_queryset(event, school=school, mentorUser=mentorUser)


def match_participant(event, firstName, lastName, yearLevel, school=None, mentorUser=None):
    """Return the single matching participant, or None if zero or multiple matches."""
    yearLevel = str(yearLevel).strip()
    matches = []

    qs = eligible_participants(event, school=school, mentorUser=mentorUser)
    qs = qs.filter(firstName__iexact=firstName.strip(), lastName__iexact=lastName.strip())
    for participant in qs:
        if str(participant.yearLevel).strip() == yearLevel:
            matches.append(participant)

    if len(matches) == 1:
        return matches[0]
    return None


def team_deed_counts(team):
    """Return (complete, total) participation deed counts for a team's students."""
    students = list(team.student_set.all())
    total = len(students)
    complete = sum(1 for student in students if student.participationDeed_id)
    return complete, total


def participant_deed_counts(event, school=None, mentorUser=None):
    """Return (complete, incomplete) deed counts across eligible students for a mentor context."""
    qs = eligible_participants(event, school=school, mentorUser=mentorUser)
    total = qs.count()
    complete = qs.exclude(participationDeed=None).count()
    return complete, total - complete


def participant_has_deed(participant):
    """Return whether the participant already has a participation deed attached."""
    return participant.participationDeed_id is not None


def unattached_deeds_for_context(event, school=None, mentorUser=None):
    """Return deeds for an event/school/mentor that are not attached to any participant."""
    qs = ParticipationDeed.objects.filter(originalEvent=event)
    if school is not None:
        qs = qs.filter(school=school)
    else:
        qs = qs.filter(school=None, mentorUser=mentorUser)

    # Unattached: no students and no workshop attendees point at this deed
    qs = qs.filter(student=None, workshopattendee=None)
    return qs.distinct()


def participants_without_deed(event, school=None, mentorUser=None):
    """Return eligible participants for an event/school/mentor who have no deed attached."""
    if event.boolWorkshop():
        qs = eligible_workshop_students_queryset(event, school=school, mentorUser=mentorUser)
    else:
        qs = eligible_students_queryset(event, school=school, mentorUser=mentorUser)
    return qs.filter(participationDeed=None).order_by('firstName', 'lastName')


def mentor_teams_for_context(event, school=None, mentorUser=None):
    """Return teams for an event filtered to a school or independent mentor, with students prefetched."""
    from teams.models import Team
    qs = Team.objects.filter(event=event).prefetch_related('student_set__participationDeed', 'division')
    if school is not None:
        qs = qs.filter(school=school)
    else:
        qs = qs.filter(school=None, mentorUser=mentorUser)
    return qs.order_by('name')


def attach_deed(participant, deed):
    """Attach a participation deed to a participant and save."""
    participant.participationDeed = deed
    participant.save(update_fields=['participationDeed', 'updatedDateTime'])

def summary_groups_for_event(event):
    """Group participants by school or independent mentor with complete/incomplete/unattached lists."""
    groups = {}

    if event.boolWorkshop():
        participants = WorkshopAttendee.objects.filter(event=event, attendeeType='student').select_related(
            'school', 'mentorUser', 'participationDeed'
        )
    else:
        participants = Student.objects.filter(team__event=event).select_related(
            'team__school', 'team__mentorUser', 'participationDeed'
        )

    for participant in participants:
        school = school_for_participant(participant)
        mentor = mentor_for_participant(participant)
        if school is not None:
            key = ('school', school.pk)
            label = str(school)
        else:
            key = ('mentor', mentor.pk)
            label = f'Independent: {mentor.fullname_or_email()}'

        group = groups.setdefault(key, {
            'label': label,
            'school': school,
            'mentorUser': mentor,
            'complete': [],
            'incomplete': [],
        })
        if participant_has_deed(participant):
            group['complete'].append(participant)
        else:
            group['incomplete'].append(participant)

    unattached_by_key = {}
    for deed in ParticipationDeed.objects.filter(originalEvent=event).filter(student=None, workshopattendee=None):
        if deed.school_id:
            key = ('school', deed.school_id)
        else:
            key = ('mentor', deed.mentorUser_id)
        unattached_by_key.setdefault(key, []).append(deed)

    result = []
    for key, group in sorted(groups.items(), key=lambda item: item[1]['label'].lower()):
        group['unattached'] = unattached_by_key.pop(key, [])
        result.append(group)

    # Groups that only have unattached deeds
    for key, deeds in unattached_by_key.items():
        deed = deeds[0]
        if deed.school_id:
            label = str(deed.school)
            school = deed.school
            mentor = None
        else:
            label = f'Independent: {deed.mentorUser.fullname_or_email()}'
            school = None
            mentor = deed.mentorUser
        result.append({
            'label': label,
            'school': school,
            'mentorUser': mentor,
            'complete': [],
            'incomplete': [],
            'unattached': deeds,
        })

    result.sort(key=lambda g: g['label'].lower())
    return result
