from django import forms

from .models import Question, QuestionResponse

import datetime

class QuestionResponseForm(forms.ModelForm):
    class Meta:
        model = QuestionResponse
        fields = ['question', 'response']

    # Override init to set user and question
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Question field
        self.fields['question'].disabled = True
        self.fields['question'].widget = forms.HiddenInput()

        question = Question.objects.get(pk=self.initial['question'])

        # Response
        self.fields['response'].label = f"{'Required: ' if question.required else ''}{question.questionText}"
        self.fields['response'].required = question.required
    
    def has_changed(self, *args, **kwargs):
        if not self.instance.pk:
            return True
        return super().has_changed(*args, **kwargs)
