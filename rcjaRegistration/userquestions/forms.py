from django import forms
from django.forms import modelformset_factory, inlineformset_factory
from django.core.exceptions import ValidationError

from .models import Question, QuestionResponse

import datetime

class QuestionResponseForm(forms.ModelForm):
    class Meta:
        model = QuestionResponse
        fields = ['question', 'user', 'response']

    # Override init to set user and question
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # User field
        self.fields['user'].initial = self.instance.user.id
        self.fields['user'].disabled = True
        self.fields['user'].widget = forms.HiddenInput()

        # Question field
        # self.fields['question'].initial = question.id
        self.fields['question'].disabled = True
        self.fields['question'].widget = forms.HiddenInput()

        # Response
        self.fields['response'].label_tag = question.questionText
        self.fields['response'].required = question.required
