from django.contrib import admin
from coordination.permissions import selectedFilterQueryset

class FilteredRelatedOnlyFieldListFilter(admin.RelatedOnlyFieldListFilter):
    def field_choices(self, field, request, model_admin):
        qs = model_admin.get_queryset(request)
        pk_qs = (
            selectedFilterQueryset(model_admin, qs, request.user)
            .distinct()
            .values_list("%s__pk" % self.field_path, flat=True)
        )
        ordering = self.field_admin_ordering(field, request, model_admin)
        return field.get_choices(
            include_blank=False, limit_choices_to={"pk__in": pk_qs}, ordering=ordering
        )
