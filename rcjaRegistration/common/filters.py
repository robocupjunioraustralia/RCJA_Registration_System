from django.contrib import admin

class FilteredRelatedOnlyFieldListFilter(admin.RelatedOnlyFieldListFilter):
    def field_choices(self, field, request, model_admin):

        selectedFilterDict = {}

        stateSelectedFilterLookup = getattr(model_admin, 'stateSelectedFilterLookup', None)
        if stateSelectedFilterLookup:
            selectedFilterDict[stateSelectedFilterLookup] = request.user.currentlySelectedAdminState

        yearSelectedFilterLookup = getattr(model_admin, 'yearSelectedFilterLookup', None)
        if yearSelectedFilterLookup:
            selectedFilterDict[yearSelectedFilterLookup] = request.user.currentlySelectedAdminYear

        pk_qs = (
            model_admin.get_queryset(request)
            .filter(**selectedFilterDict)
            .distinct()
            .values_list("%s__pk" % self.field_path, flat=True)
        )
        ordering = self.field_admin_ordering(field, request, model_admin)
        return field.get_choices(
            include_blank=False, limit_choices_to={"pk__in": pk_qs}, ordering=ordering
        )
