from rest_framework import serializers

from events.models import Event
from regions.models import State, Region

# *****Regions*****

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = [
            'id',
            'name',
            'abbreviation'
        ]

# *****Events*****

class EventSerializer(serializers.ModelSerializer):
    state = StateSerializer(read_only=True)
    class Meta:
        model = Event
        fields = [
            'id',
            'year',
            'state',
            'globalEvent',
            'name',
            'eventType',
            # Dates
            'startDate',
            'endDate',
            'registrationsOpenDate',
            'registrationsCloseDate',
            # Team details
            'maxMembersPerTeam',
            'event_maxTeamsPerSchool',
            'event_maxTeamsForEvent',
            # Billing
            'entryFeeIncludesGST',
            'event_defaultEntryFee',
            'paymentDueDate',
            # Competition billing
            'event_billingType',
            'event_specialRateNumber',
            'event_specialRateFee',
            # Workshop billing
            'workshopTeacherEntryFee',
            'workshopStudentEntryFee',
            # Details
            'directEnquiriesTo',
            'venue',
            'eventDetails',
            'additionalInvoiceMessage',
            # Divisions
            'divisions',
        ]
