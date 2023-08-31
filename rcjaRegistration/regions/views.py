from django.shortcuts import render
from django.db.models import Q
from dal import autocomplete
from coordination.permissions import coordinatorFilterQueryset, getFilteringPermissionLevels
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from regions.models import Region
from regions.admin import RegionAdmin

class RegionAutocomplete(LoginRequiredMixin, PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    permission_required = 'regions.view_region'

    def get_queryset(self):
        # Determine which filters to apply
        stateFilterLookup = getattr(RegionAdmin, 'stateFilterLookup', False)
        globalFilterLookup = getattr(RegionAdmin, 'globalFilterLookup', False)

        # Get permission levels
        statePermissionLevels, globalPermissionLevels = getFilteringPermissionLevels(Region, ['view', 'change'])

        # Get queryset and filter by querystring
        queryset = Region.objects.all()

        if self.q:
            queryset = queryset.filter(name__icontains=self.q)

        state = self.forwarded.get('homeState', None)

        if state:
            queryset = queryset.filter(Q(state=None) | Q(state=state))
        else:
            queryset = queryset.filter(state=None)

        # Filter queryset by coordinator and return
        return coordinatorFilterQueryset(queryset, self.request, statePermissionLevels, globalPermissionLevels, stateFilterLookup, globalFilterLookup)
