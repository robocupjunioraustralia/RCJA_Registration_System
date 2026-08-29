import datetime

from django.core import signing

from events.models import Event
from schools.models import School
from users.models import User

SALT_SCHOOL = 'participationdeeds.school'


def deeds_available_for_event(event):
    if not event.electronicParticipationDeedsEnabled:
        return False
    if not event.hasAllDetails():
        return False
    return datetime.date.today() <= event.startDate


def dumps_school_or_mentor(event, school=None, mentorUser=None):
    payload = {'event': event.pk}
    if school is not None:
        payload['school'] = school.pk
    else:
        payload['mentor'] = mentorUser.pk
    return signing.dumps(payload, salt=SALT_SCHOOL)


def loads_school_or_mentor(token):
    data = signing.loads(token, salt=SALT_SCHOOL)
    event = Event.objects.select_related('state').get(pk=data['event'])
    school = None
    mentorUser = None
    if 'school' in data and data['school'] is not None:
        school = School.objects.get(pk=data['school'])
    elif 'mentor' in data and data['mentor'] is not None:
        mentorUser = User.objects.get(pk=data['mentor'])
    else:
        raise signing.BadSignature('Missing school or mentor')
    return event, school, mentorUser
