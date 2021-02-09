from django.contrib import admin
from common.adminMixins import FKActionsRemove
from coordination.permissions import InlineAdminPermissions

from .models import EventAvailableFileType

class EventAvailableFileTypeInline(FKActionsRemove, InlineAdminPermissions, admin.TabularInline):
    model = EventAvailableFileType
    extra = 0
