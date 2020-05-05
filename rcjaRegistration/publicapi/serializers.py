from rest_framework import serializers

# *****Regions*****

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        from regions.models import State
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
        from events.models import AvailableDivision
        model = AvailableDivision
        fields = [
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
        from events.models import Venue
        model = Venue
        fields = [
            'name',
            'address',
        ]

class BasicUserSerializer(serializers.ModelSerializer):
    fullName = serializers.CharField(label='Full name', source='get_full_name')
    class Meta:
        from users.models import User
        model = User
        fields = [
            'fullName',
            'email',
        ]

class EventSerializer(serializers.ModelSerializer):
    availabledivisions = AvailableDivisionSerializer(read_only=True, many=True, source='availabledivision_set')
    venue = VenueSerializer(read_only=True)
    directEnquiriesTo = BasicUserSerializer(read_only=True)
    registrationURL = serializers.CharField(label='Registration URL', source='get_absolute_url')

    class Meta:
        from events.models import Event
        model = Event
        fields = [
            'id',
            'state',
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
            'registrationURL',
            # Divisions
            'availabledivisions',
        ]
