from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from .forms import SchoolForm, SchoolEditForm, CampusForm, SchoolAdministratorForm
from django.http import JsonResponse
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.core.exceptions import ValidationError, PermissionDenied
from django.forms import modelformset_factory, inlineformset_factory
from django.db.models import ProtectedError
from django.urls import reverse
from django.db import IntegrityError, transaction

from users.models import User
from .models import School, Campus, SchoolAdministrator

@login_required
def create(request):
    if request.method == 'POST':
        form = SchoolForm(request.POST)

        if form.is_valid(): 
            school = form.save()

            # Save school administrator
            SchoolAdministrator.objects.create(user=request.user, school=school)

            return redirect(reverse('users:details'))

    else:
        form = SchoolForm()

    return render(request, 'schools/createSchool.html', {'form': form})

@login_required
def setCurrentSchool(request, schoolID):
    school = get_object_or_404(School, pk=schoolID)

    # Check permissions
    if not request.user.schooladministrator_set.filter(school=school).exists():
        raise PermissionDenied("You do not have permission to view this school")

    # Set current school on user
    request.user.currentlySelectedSchool = school
    request.user.save(update_fields=['currentlySelectedSchool'])
    
    return redirect('/')

@login_required
def details(request):
    # Check permissions
    school = request.user.currentlySelectedSchool

    if not (request.user.currentlySelectedSchool and request.user.schooladministrator_set.filter(school=school).exists()):
        raise PermissionDenied("You do not have permission to view this school")

    # Campus formset
    CampusInlineFormset = inlineformset_factory(
        School,
        Campus,
        form=CampusForm,
        extra=0,
        can_delete=True
    )

    # School administrator formset
    SchoolAdministratorInlineFormset = inlineformset_factory(
        School,
        SchoolAdministrator,
        form=SchoolAdministratorForm,
        extra=0,
        can_delete=True
    )

    # Create get version of the forms here so that exist before the exception is added if missing management data
    form = SchoolEditForm(instance=school)
    campusFormset = CampusInlineFormset(instance=school)
    schoolAdministratorFormset = SchoolAdministratorInlineFormset(instance=school, form_kwargs={'user': request.user})

    if request.method == 'POST':
        # Create Post versions of forms
        form = SchoolEditForm(request.POST, instance=school)
        campusFormset = CampusInlineFormset(request.POST, instance=school)
        schoolAdministratorFormset = SchoolAdministratorInlineFormset(request.POST, instance=school, form_kwargs={'user': request.user})

        try:
            # Check all forms are valid, don't want short circuit logic because want errors to be raised from all forms even if one is invalid
            if all([x.is_valid() for x in (form, campusFormset, schoolAdministratorFormset)]):

                # Save school
                school = form.save(commit=False)
                school.forceSchoolDetailsUpdate = False

                # Want all data to save or none to save
                try:
                    with transaction.atomic():
                        school.save()

                        # Save administrators formset
                        # Do this before saving the campuses so if a campus is deleted the SET_NULL removes the relation, rather than getting a FK error
                        schoolAdministratorFormset.save()

                        # Save campus formset
                        campusFormset.save()

                # Catch deletion of protected objects
                except ProtectedError as e:
                    form.add_error(None, e.args[0])
                    return render(request, 'schools/schoolDetails.html', {'form': form, 'campusFormset': campusFormset, 'schoolAdministratorFormset':schoolAdministratorFormset})

                # Handle new administrator
                if form.cleaned_data['addAdministratorEmail']:
                    user, created = User.objects.get_or_create(
                        email__iexact=form.cleaned_data['addAdministratorEmail'],
                        defaults={
                            'email': form.cleaned_data['addAdministratorEmail'],
                            'forceDetailsUpdate': True,
                            })
                    SchoolAdministrator.objects.get_or_create(school=school, user=user)

                # Stay on page if continue_editing in response, else redirect to home
                if 'continue_editing' in request.POST:
                    return redirect(reverse('schools:details'))

                return redirect(reverse('events:dashboard'))

        # To catch missing management data
        except ValidationError as e:
            # Reset the formsets so that are valid and won't cause an error when passed to render
            campusFormset = CampusInlineFormset(instance=school)
            schoolAdministratorFormset = SchoolAdministratorInlineFormset(instance=school, form_kwargs={'user': request.user})

            # Add error to the form
            form.add_error(None, e.message)

    return render(request, 'schools/schoolDetails.html', {'form': form, 'campusFormset': campusFormset, 'schoolAdministratorFormset':schoolAdministratorFormset})
