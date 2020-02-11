from django.contrib import admin
from common.admin import *

from .models import *

# Register your models here.

class MentorQuestionResponseInline(admin.TabularInline):
    model = MentorQuestionResponse
    extra = 0

    # Only mentor can ever change response
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(MentorQuestion)
class MentorQuestionAdmin(admin.ModelAdmin):
    pass

# Temporary for demo. Needs same permissions as inline if left accessible.
@admin.register(MentorQuestionResponse)
class MentorQuestionResponseAdmin(admin.ModelAdmin):
    pass
