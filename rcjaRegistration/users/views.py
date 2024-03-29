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
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.encoding import iri_to_uri
from urllib.parse import urlparse

from .models import User
from userquestions.models import Question, QuestionResponse
from userquestions.forms import QuestionResponseForm
from schools.models import School

from regions.utils import getRegionsLookup
from coordination.permissions import checkCoordinatorPermission

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
        questionFormset = QuestionReponseFormSet(request.POST, instance=request.user, initial=questionResponseInitials, error_messages={"missing_management_form": "ManagementForm data is missing or has been tampered with"})

        # Don't redirect to home if use was forced here and no schools, so user can create a school
        displayAgain = request.user.forceDetailsUpdate and not request.user.currentlySelectedSchool

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

    return render(request, 'registration/profile.html', {'form': form, 'questionFormset': questionFormset, 'schools':schools, 'regionsLookup': getRegionsLookup()})

@sensitive_post_parameters('password', 'passwordConfirm')
@sensitive_variables('form', 'cleaned_data')
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

    return render(request, 'registration/signup.html', {'form': form, 'regionsLookup': getRegionsLookup()})

def termsAndConditions(request):
    if request.user.is_authenticated:
        return render(request,'termsAndConditions/termsAndConditionsLoggedIn.html')
    else:
        return render(request,'termsAndConditions/termsAndConditionsNoAuth.html') 

def redirectCurrentPage(request):
    referrer = request.META.get('HTTP_REFERER', '')
    parsed = urlparse(referrer)
    uri = iri_to_uri(parsed.path)
    if url_has_allowed_host_and_scheme(uri, None):
        return redirect(uri)
    else:
        return redirect('/')

@login_required
def setCurrentAdminYear(request, year):
    if request.method != "POST":
        raise PermissionDenied("Forbidden method")

    # Restrict to staff
    if not request.user.is_staff:
        raise PermissionDenied("Must be staff")

    if year == 0:
        request.user.currentlySelectedAdminYear = None

    else:
        from events.models import Year
        year = get_object_or_404(Year, pk=year)

        # Set current year on user
        request.user.currentlySelectedAdminYear = year

    # Save field
    request.user.save(update_fields=['currentlySelectedAdminYear'])
    
    return redirectCurrentPage(request)

@login_required
def setCurrentAdminState(request, stateID):
    if request.method != "POST":
        raise PermissionDenied("Forbidden method")

    # Restrict to staff
    if not request.user.is_staff:
        raise PermissionDenied("Must be staff")

    if stateID == 0:
        request.user.currentlySelectedAdminState = None

    else:
        from regions.models import State
        state = get_object_or_404(State, pk=stateID)

        # Check permissions
        if not checkCoordinatorPermission(request, State, state, 'view'):
            raise PermissionDenied("You do not have permission to view this state")

        # Set current state on user
        request.user.currentlySelectedAdminState = state

    # Save field
    request.user.save(update_fields=['currentlySelectedAdminState'])
    
    return redirectCurrentPage(request)

@login_required
def adminChangelog(request):
    # Restrict to staff
    if not request.user.is_staff:
        raise PermissionDenied("Must be staff")

    return render(request, 'users/adminChangelog.html')
