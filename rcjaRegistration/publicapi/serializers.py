from rest_framework import serializers

from events.models import Event, AvailableDivision, Venue
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

class AvailableDivisionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(label='Name', source='division.name')
    description = serializers.CharField(label='Description', source='division.description')

    class Meta:
        model = AvailableDivision
        fields = [
            'id',
            'name',
            'description',
            # Team details
            'division_maxTeamsPerSchool',
            'division_maxTeamsForDivision',
            # Billing details
            'division_billingType',
            'division_entryFee',
        ]

class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = [
            'id',
            'name',
            'address',
        ]

class EventSerializer(serializers.ModelSerializer):
    availabledivision_set = AvailableDivisionSerializer(read_only=True, many=True)
    venue = VenueSerializer(read_only=True)

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
            'availabledivision_set',
        ]
