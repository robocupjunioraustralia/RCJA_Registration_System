from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from .forms import UserForm, UserSignupForm
from django.http import JsonResponse
from django.http import HttpResponseForbidden
from django.forms import modelformset_factory, inlineformset_factory
from django.urls import reverse

from .models import User
from userquestions.models import Question, QuestionResponse
from userquestions.forms import QuestionResponseForm

@login_required
def details(request):
    # Questions formset
    questions = Question.objects.all()
    numberQuestions = questions.count()

    QuestionReponseFormSet = inlineformset_factory(
        User,
        QuestionResponse,
        form=QuestionResponseForm,
        extra=numberQuestions,
        max_num=numberQuestions,
        can_delete=False
    )

    questionResponseInitials = []

    for question in questions:
        questionResponseInitials.append({
            'question': question.id,
            'user': request.user.id,
        })

    if request.method == 'POST':
        form = UserForm(request.POST, instance=request.user)
        questionFormset = QuestionReponseFormSet(request.POST, instance=request.user, initial=questionResponseInitials)

        if form.is_valid() and questionFormset.is_valid():
            # Save user
            user = form.save()

            # Save question response questionFormset
            questionFormset.save() 

            return redirect('/')
    else:
        form = UserForm(instance=request.user)
        questionFormset = QuestionReponseFormSet(instance=request.user, initial=questionResponseInitials)
    return render(request, 'registration/profile.html', {'form': form, 'questionFormset': questionFormset})

def signup(request):
    if request.method == 'POST':
        form = UserSignupForm(request.POST)

        if form.is_valid():
            # Save user
            user = form.save()
            user.set_password(form.cleaned_data["password"])
            user.save()

            # Save school administrator
            # if form.cleaned_data['school']:
            #     SchoolAdministrator.objects.create(user=user, school=form.cleaned_data['school'])

            # Login and redirect
            login(request, user)
            return redirect(reverse('users:details'))
    else:
        form = UserSignupForm()

    return render(request, 'registration/signup.html', {'form': form})

