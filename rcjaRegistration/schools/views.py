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

    if request.method == 'POST':
        form = SchoolEditForm(request.POST, instance=school)
        campusFormset = CampusInlineFormset(request.POST, instance=school)
        schoolAdministratorFormset = SchoolAdministratorInlineFormset(request.POST, instance=school, form_kwargs={'user': request.user})

        try:
            if form.is_valid() and campusFormset.is_valid() and schoolAdministratorFormset.is_valid():
                # Save school
                school = form.save(commit=False)
                school.forceSchoolDetailsUpdate = False
                school.save()

                # Save campus formset
                # Need commit=False to do manual deletion to catch protected errors
                campuses = campusFormset.save(commit=False)

                for campus in campusFormset.deleted_objects:
                    try:
                        campus.delete()
                    except ProtectedError:
                        pass
                
                for campus in campuses:
                    campus.save()

                # Save administrators formset
                # Need commit=False to do manual deletion to catch protected errors
                administrators = schoolAdministratorFormset.save(commit=False)

                for administrator in schoolAdministratorFormset.deleted_objects:
                    try:
                        administrator.delete()
                    except ProtectedError:
                        pass

                for administrator in administrators:
                    administrator.save()

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

        except ValidationError:
            # To catch missing management data
            return HttpResponseBadRequest('Form data missing')

    else:
        form = SchoolEditForm(instance=school)
        campusFormset = CampusInlineFormset(instance=school)
        schoolAdministratorFormset = SchoolAdministratorInlineFormset(instance=school, form_kwargs={'user': request.user})
    
    try:
        return render(request, 'schools/schoolDetails.html', {'form': form, 'campusFormset': campusFormset, 'schoolAdministratorFormset':schoolAdministratorFormset})
    except ValidationError:
        # To catch missing management data
        return HttpResponseBadRequest('Form data missing')
