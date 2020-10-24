from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from .forms import UserForm, UserSignupForm
from django.http import JsonResponse
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.core.exceptions import ValidationError, PermissionDenied
from django.forms import modelformset_factory, inlineformset_factory
from django.urls import reverse

from .models import User
from userquestions.models import Question, QuestionResponse
from userquestions.forms import QuestionResponseForm
from schools.models import School

@login_required
def details(request):
    # Schools
    schools = School.objects.filter(schooladministrator__user=request.user)

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

    # Create get version of the forms here so that exist before the exception is added if missing management data
    form = UserForm(instance=request.user)
    questionFormset = QuestionReponseFormSet(instance=request.user, initial=questionResponseInitials)

    if request.method == 'POST':
        # Create Post versions of forms
        form = UserForm(request.POST, instance=request.user)
        questionFormset = QuestionReponseFormSet(request.POST, instance=request.user, initial=questionResponseInitials)

        # Don't redirect to home if use was forced here and no schools, so user can create a school
        displayAgain = request.user.forceDetailsUpdate and not request.user.currentlySelectedSchool

        try:
            if all([x.is_valid() for x in (form, questionFormset)]):
                # Save user
                user = form.save(commit=False)
                user.forceDetailsUpdate = False
                user.save()

                # Save question response questionFormset
                questionFormset.save() 

                # Stay on page if continue_editing in response or if must display again, else redirect to home
                if displayAgain or 'continue_editing' in request.POST:
                    return redirect(reverse('users:details'))

                return redirect(reverse('events:dashboard'))

        # To catch missing management data
        except ValidationError as e:
            # Reset the formsets so that are valid and won't cause an error when passed to render
            questionFormset = QuestionReponseFormSet(instance=request.user, initial=questionResponseInitials)

            # Add error to the form
            form.add_error(None, e.message)

    return render(request, 'registration/profile.html', {'form': form, 'questionFormset': questionFormset, 'schools':schools})

def signup(request):
    if request.method == 'POST':
        form = UserSignupForm(request.POST)

        if form.is_valid():
            # Save user
            user = form.save()
            user.set_password(form.cleaned_data["password"])
            user.forceDetailsUpdate = True # Force redirect to details page so user can submit question responses and create a school
            user.save()

            # Login and redirect
            login(request, user)
            return redirect(reverse('users:details'))
    else:
        form = UserSignupForm()

    return render(request, 'registration/signup.html', {'form': form})

def termsAndConditions(request):
    if request.user.is_authenticated:
        return render(request,'termsAndConditions/termsAndConditionsLoggedIn.html')
    else:
        return render(request,'termsAndConditions/termsAndConditionsNoAuth.html') 
