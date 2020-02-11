from django.contrib import admin
from common.admin import *

from .models import *

# Register your models here.


@admin.register(MentorQuestion)
class MentorQuestionAdmin(admin.ModelAdmin):
    pass
