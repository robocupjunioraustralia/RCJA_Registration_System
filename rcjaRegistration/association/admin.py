from django.contrib import admin, messages
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from common.adminMixins import ExportCSVMixin, DifferentAddFieldsMixin, FKActionsRemove
from coordination.permissions import AdminPermissions, InlineAdminPermissions

from .models import AssociationMember
from users.admin import UserAdmin
from users.models import User

import datetime

@admin.register(AssociationMember)
class SchoolAdmin(FKActionsRemove, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        '__str__',
        'getState',
        'membershipActive',
        'membershipType',
        'approvalStatus',
        'membershipStartDate',
        'membershipEndDate',
    ]
    readonly_fields = [
        'getState',
        'homeRegion',
        'email',
        'mobileNumber',
        'membershipActive',
        'membershipType',
        'rulesAcceptedDate',
        'approvalRejectionBy',
        'approvalRejectionDate',
    ]
    fieldsets = [
        ('User details', {
            'fields': [
                'user',
                'birthday',
                'address',
                'email',
                'mobileNumber',
                'getState',
                'homeRegion',
            ]
        }),
        ('Membership details', {
            'fields': [
                'membershipStartDate',
                'membershipEndDate',
                'lifeMemberAwardedDate',
                'membershipType',
                'membershipActive',
                'rulesAcceptedDate',
            ]
        }),
        ('Approval details', {
            'fields': [
                'approvalStatus',
                'approvalRejectionBy',
                'approvalRejectionDate',
            ]
        }),
    ]
    list_filter = [
        ('user__homeState', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'user__homeState__name',
        'user__homeState__abbreviation',
        'user__homeRegion__name',
        'user__email',
        'user__mobileNumber',
    ]
    autocomplete_fields = [
        'user'
    ]
    actions = [
        'bulkApproveMembers',
        'bulkRejectMembers',
        'export_as_csv',
    ]
    exportFields = [
        'pk',
        'user',
        'email',
        'mobileNumber',
        'getState',
        'homeRegion',
        'birthday',
        'address',
        'membershipActive',
        'membershipType',
        'membershipStartDate',
        'membershipEndDate',
    ]

    # Set approvalRejectionBy and approvedDate
    def save_model(self, request, obj, form, change):
        if obj.approvalRejectionBy is None and obj.approvalStatus != 'pending':
            obj.approvalRejectionBy = request.user

        if obj.approvalRejectionDate is None and obj.approvalStatus != 'pending':
            obj.approvalRejectionDate = datetime.date.today()

        super().save_model(request, obj, form, change)

    # Bulk approve/reject actions
    def setApprovalStatus(self, request, queryset, newStatus):
        # Messaging variables
        numberUpdated = 0
        skippedNotPending = 0

        approvalStatusLabel = AssociationMember._meta.get_field('approvalStatus').verbose_name

        for member in queryset:
            # approvalStatus is readonly once approved/rejected
            if member.approvalStatus != 'pending' and member.approvalRejectionDate:
                skippedNotPending += 1
                continue

            # Update status and other relevant fields
            member.approvalStatus = newStatus
            member.approvalRejectionBy = request.user
            member.approvalRejectionDate = datetime.date.today()

            # Persist changes
            member.save()
            numberUpdated += 1

            # Log the action
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(AssociationMember).pk,
                object_id=member.id,
                object_repr=str(member),
                action_flag=CHANGE,
                change_message=[{"changed": {"fields": [approvalStatusLabel]}}],
            )

        if numberUpdated > 0:
            self.message_user(request, f"{numberUpdated} association member(s) {newStatus}.", messages.SUCCESS)

        if skippedNotPending > 0:
            self.message_user(
                request,
                f"{skippedNotPending} association member(s) skipped (status can only be changed if pending).",
                messages.WARNING
            )

    def bulkApproveMembers(self, request, queryset):
        self.setApprovalStatus(request, queryset, 'approved')
    bulkApproveMembers.short_description = "Approve selected"
    bulkApproveMembers.allowed_permissions = ('change',)

    def bulkRejectMembers(self, request, queryset):
        self.setApprovalStatus(request, queryset, 'rejected')
    bulkRejectMembers.short_description = "Reject selected"
    bulkRejectMembers.allowed_permissions = ('change',)

    def get_readonly_fields(self, request, obj):
        readonly_fields = super().get_readonly_fields(request, obj).copy()

        if obj is None:
            return readonly_fields

        # Make approvalStatus readonly if not pending
        if obj.approvalStatus != 'pending' and obj.approvalRejectionDate:
            readonly_fields += ['approvalStatus']

        return readonly_fields

    # State based filtering

    fkFilterFields = {
        'user': {
            'fieldAdmin': UserAdmin,
            'fieldModel': User,
        },
    }

    statePermissionsFilterLookup = 'user__homeState__coordinator'
