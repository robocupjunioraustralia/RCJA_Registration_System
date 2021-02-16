from django.db.models import Q

from regions.models import State, Region

class RegionLookupObj:
    def __init__(self, stateID, regions):
        self.id = stateID
        self.regions = regions

def getRegionsLookup():
    """
    Creates a list of objects with state id and a list of regions that are available for that state.
    """

    regionsLookup = []

    # Add blank state id with global regions for when no state selected
    regionsLookup.append(RegionLookupObj('', Region.objects.filter(state=None)))

    # Add regions for each state
    for state in State.objects.filter(typeRegistration=True):
        regionsLookup.append(RegionLookupObj(state.id, Region.objects.filter(Q(state=None) | Q(state=state))))

    return regionsLookup
