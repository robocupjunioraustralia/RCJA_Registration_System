from django import forms

from teams.models import Student


class ChildLookupForm(forms.Form):
    firstName = forms.CharField(label='Child first name', max_length=50)
    lastName = forms.CharField(label='Child last name', max_length=50)
    yearLevel = forms.IntegerField(label='Year level', min_value=1)


class ParticipationDeedSignForm(forms.Form):
    agree = forms.BooleanField(
        label='I have read and agree to the participation deed',
        required=True,
    )
    parentName = forms.CharField(label='Parent / guardian full name', max_length=100)


class AttachStudentForm(forms.Form):
    student = forms.ModelChoiceField(label='Student', queryset=None)

    def __init__(self, *args, students, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = students

        def label_from_instance(student):
            label = f'{student} (Year {student.yearLevel})'
            if isinstance(student, Student):
                label = f'{label} — {student.team.name}'
            return label

        self.fields['student'].label_from_instance = label_from_instance
