from rest_framework import serializers
# from common.serializers import *

from events.models import Event
from regions.models import State, Region

# *****Regions*****

# class StateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = State
#         fields = '__all__'

# class RegionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Region
#         fields = '__all__'

# # *****Events*****

# class EventSerializer(serializers.ModelSerializer):
#     state = StateSerializer(read_only=True)
#     class Meta:
#         model = Event
#         # fields = ['id','year','state','creationDateTime','updatedDateTime','name','maxMembersPerTeam','startDate']
#         fields = '__all__'

