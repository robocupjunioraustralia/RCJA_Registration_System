from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from .forms import SchoolForm, SchoolEditForm, CampusForm, SchoolAdministratorForm, AdminSchoolsMergeForm
from django.http import JsonResponse
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.core.exceptions import ValidationError, PermissionDenied
from django.forms import modelformset_factory, inlineformset_factory
from django.db.models import ProtectedError
from django.urls import reverse
from django.db import IntegrityError, transaction
from coordination.permissions import checkCoordinatorPermission

from users.models import User
from .models import School, Campus, SchoolAdministrator

from regions.utils import getRegionsLookup

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

    return render(request, 'schools/createSchool.html', {'form': form, 'regionsLookup': getRegionsLookup()})

@login_required
def setCurrentSchool(request, schoolID):
    if request.method != "POST":
        raise PermissionDenied("Forbidden method")

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
        campusFormset = CampusInlineFormset(request.POST, instance=school, error_messages={"missing_management_form": "ManagementForm data is missing or has been tampered with"})
        schoolAdministratorFormset = SchoolAdministratorInlineFormset(request.POST, instance=school, form_kwargs={'user': request.user}, error_messages={"missing_management_form": "ManagementForm data is missing or has been tampered with"})

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

    return render(request, 'schools/schoolDetails.html', {'form': form, 'campusFormset': campusFormset, 'schoolAdministratorFormset':schoolAdministratorFormset, 'regionsLookup': getRegionsLookup()})

@login_required
def adminMergeSchools(request, school1ID, school2ID):
    # Restrict to staff
    if not request.user.is_staff:
        raise PermissionDenied("Must be staff")

    school1 = get_object_or_404(School, pk=school1ID)
    school2 = get_object_or_404(School, pk=school2ID)

    if not (
        checkCoordinatorPermission(request, School, school1, 'change') and
        checkCoordinatorPermission(request, School, school1, 'delete') and
        checkCoordinatorPermission(request, School, school2, 'change') and
        checkCoordinatorPermission(request, School, school2, 'delete')
    ):
        raise PermissionDenied("No permission on selected schools")

    eventAttendeeChanges = []
    campusChanges = []
    schoolAdministratorChanges = []
    invoiceChanges = []

    validated = False
    if request.method == 'POST':
        # Create Post version of form
        form = AdminSchoolsMergeForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    keepExistingCampuses = form.cleaned_data['keepExistingCampuses']
                    # Create new campuses
                    campus1Name = form.cleaned_data['school1NewCampusName']
                    if campus1Name:
                        try:
                            school1NewCampus = Campus.objects.get(school=school1, name=campus1Name)
                            school1NewCampus.oldSchool = school1NewCampus.school
                        except Campus.DoesNotExist:
                            school1NewCampus = Campus(school=school1, name=form.cleaned_data['school1NewCampusName'])
                            school1NewCampus.oldSchool = None
                        school1NewCampus.full_clean()
                        campusChanges.append(school1NewCampus)
                    else:
                        school1NewCampus = None

                    if school1NewCampus and "merge" in request.POST:
                        school1NewCampus.save()

                    campus2Name = form.cleaned_data['school2NewCampusName']
                    if campus2Name:
                        try:
                            school2NewCampus = Campus.objects.get(school=school2, name=campus2Name)
                            school2NewCampus.oldSchool = school2NewCampus.school
                            school2NewCampus.school = school1
                        except Campus.DoesNotExist:
                            school2NewCampus = Campus(school=school1, name=form.cleaned_data['school2NewCampusName'])
                            school2NewCampus.oldSchool = None
                        school2NewCampus.full_clean()
                        campusChanges.append(school2NewCampus)
                    else:
                        school2NewCampus = None

                    if school2NewCampus and "merge" in request.POST:
                        school2NewCampus.save()

                    # School 1
                    # School administrators
                    for school1Administrator in school1.schooladministrator_set.all():
                        school1Administrator.oldSchool = school1Administrator.school

                        school1Administrator.oldCampus = school1Administrator.campus
                        newCampus = school1NewCampus if not keepExistingCampuses else (school1Administrator.campus or school1NewCampus)
                        school1Administrator.campus = newCampus

                        schoolAdministratorChanges.append(school1Administrator)

                        if "merge" in request.POST:
                            school1Administrator.save()

                    # Invoices
                    for invoice in school1.invoice_set.all():
                        invoice.oldSchool = invoice.school
                        invoice.oldCampus = invoice.campus

                        if invoice.invoiceAmountInclGST_unrounded() < 0.05 and not invoice.invoicepayment_set.exists():
                            invoice.school = None
                            invoice.campus = None
                        else:
                            newCampus = school1NewCampus if not keepExistingCampuses else (invoice.campus or school1NewCampus)
                            invoice.campus = newCampus

                        invoiceChanges.append(invoice)

                        if "merge" in request.POST:
                            try:
                                if invoice.school is None:
                                    invoice.delete()
                                else:
                                    invoice.full_clean()
                                    invoice.save()
                            except ValidationError as e:
                                raise ValidationError(f"Couldn't save invoice {invoice.invoiceNumber} because already a conflicting invoice, couldn't delete because invoice amount is not 0. Remove any invoice payments and set invoice override for anything connected to this invoice, then try again. ({e.args[0]})")

                    # Event attendances
                    for eventAttendanceParent in school1.baseeventattendance_set.all():
                        eventAttendance = eventAttendanceParent.childObject()

                        eventAttendance.oldSchool = eventAttendance.school

                        eventAttendance.oldCampus = eventAttendance.campus
                        newCampus = school1NewCampus if not keepExistingCampuses else (eventAttendance.campus or school1NewCampus)
                        eventAttendance.campus = newCampus

                        eventAttendeeChanges.append(eventAttendance)

                        if "merge" in request.POST:
                            eventAttendance.save(skipPrePostSave=True)

                    # If not keeping campuses existing campuses will be deleted, add them to changes list and delete
                    for campus in school1.campus_set.all():
                        if campus != school1NewCampus:
                            campus.oldSchool = campus.school
                            campus.school = school1 if keepExistingCampuses else None

                            campusChanges.append(campus)

                            if "merge" in request.POST:
                                if keepExistingCampuses:
                                    campus.save()
                                else:
                                    campus.delete()

                    # School 2
                    if school1 != school2:
                        # School administrators
                        for school2Administrator in school2.schooladministrator_set.all():
                            school2Administrator.oldSchool = school2Administrator.school
                            school2Administrator.school = school1

                            school2Administrator.oldCampus = school2Administrator.campus
                            newCampus = school2NewCampus if not keepExistingCampuses else (school2Administrator.campus or school2NewCampus)
                            school2Administrator.campus = newCampus

                            schoolAdministratorChanges.append(school2Administrator)

                            if "merge" in request.POST:
                                schoolAdministrator, created = SchoolAdministrator.objects.update_or_create(school=school1, user=school2Administrator.user, defaults={'campus': newCampus})

                        # Invoices
                        for invoice in school2.invoice_set.all():
                            invoice.oldSchool = invoice.school
                            invoice.oldCampus = invoice.campus

                            if invoice.invoiceAmountInclGST_unrounded() < 0.05 and not invoice.invoicepayment_set.exists():
                                invoice.school = None
                                invoice.campus = None
                            else:
                                invoice.school = school1
                                newCampus = school2NewCampus if not keepExistingCampuses else (invoice.campus or school2NewCampus)
                                invoice.campus = newCampus

                            invoiceChanges.append(invoice)

                            if "merge" in request.POST:
                                try:
                                    if invoice.school is None:
                                        invoice.delete()
                                    else:
                                        invoice.full_clean()
                                        invoice.save()
                                except ValidationError as e:
                                    raise ValidationError(f"Couldn't save invoice {invoice.invoiceNumber} because already a conflicting invoice, couldn't delete because invoice amount is not 0. Remove any invoice payments and set invoice override for anything connected to this invoice, then try again. ({e.args[0]})")

                        # Event attendances
                        for eventAttendanceParent in school2.baseeventattendance_set.all():
                            eventAttendance = eventAttendanceParent.childObject()

                            eventAttendance.oldSchool = eventAttendance.school
                            eventAttendance.school = school1

                            eventAttendance.oldCampus = eventAttendance.campus
                            newCampus = school2NewCampus if not keepExistingCampuses else (eventAttendance.campus or school2NewCampus)
                            eventAttendance.campus = newCampus

                            eventAttendeeChanges.append(eventAttendance)

                            if "merge" in request.POST:
                                eventAttendance.save(skipPrePostSave=True)

                        # If not keeping campuses existing campuses will be deleted, add them to changes list and delete
                        for campus in school2.campus_set.all():
                            if campus != school2NewCampus:
                                campus.oldSchool = campus.school
                                campus.school = school1 if keepExistingCampuses else None

                                campusChanges.append(campus)
                                if "merge" in request.POST:
                                    if keepExistingCampuses:
                                        campus.save()
                                    else:
                                        campus.delete()
                        
                        # Delete school 2
                        if "merge" in request.POST:
                            school2.delete()
                            for invoice in school1.invoice_set.all():
                                invoice.calculateAndSaveAllTotals()

                    validated = True
                    if "merge" in request.POST:
                        # raise ValidationError('To stop execution to DB')
                        return redirect(reverse('admin:schools_school_changelist'))
                        

            except ValidationError as e:
                form.add_error(None, e.args[0])

    else:
        form = AdminSchoolsMergeForm()

    context = {
        'form': form,
        'school1': school1,
        'school2': school2,
        'validated': validated,
        'campusChanges': campusChanges,
        'schoolAdministratorChanges': schoolAdministratorChanges,
        "invoiceChanges": invoiceChanges,
        'eventAttendeeChanges': eventAttendeeChanges,
    }

    return render(request, 'schools/adminMergeSchools.html', context)
