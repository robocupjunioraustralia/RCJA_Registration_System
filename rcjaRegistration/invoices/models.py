from django.db import models
from django.db.models import F, Q
from common.models import SaveDeleteMixin
from django.conf import settings
from django.core.exceptions import ValidationError

# **********MODELS**********

class InvoiceGlobalSettings(models.Model):
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    invoiceFromName = models.CharField('Invoice from name', max_length=50)
    invoiceFromDetails = models.TextField('Invoice from details')
    invoiceFooterMessage = models.TextField('Invoice footer message')
    firstInvoiceNumber = models.PositiveIntegerField('First invoice number', default=1)
    # Surcharge
    surchargeAmount = models.FloatField('Surcharge amount', default=0, help_text="Amount includes GST.")
    surchargeName = models.CharField('Surcharge name', max_length=30, default='Surcharge', help_text="Name of the surcharge on the invoice.")
    surchargeInvoiceDescription = models.CharField('Surcharge invoice description', max_length=70, blank=True, help_text="Appears in small text below the surcharge name on the invoice.")
    surchargeEventDescription = models.CharField('Surcharge event page description', max_length=200, blank=True, help_text="Appears on the event page below the surcharge amount.")

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Invoice settings'
        verbose_name_plural = 'Invoice settings'

    # Allow only one instance of model
    def clean(self):
        if InvoiceGlobalSettings.objects.exclude(pk=self.pk).exists():
            raise(ValidationError('May only be one global settings object'))

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return 'Invoice settings'

class Invoice(SaveDeleteMixin, models.Model):
    # Foreign keys
    event = models.ForeignKey('events.Event', verbose_name = 'Event', on_delete=models.CASCADE, editable=False)

    # User and school foreign keys
    invoiceToUser = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Invoice to', on_delete=models.PROTECT, editable=False)
    school = models.ForeignKey('schools.School', verbose_name='School', on_delete=models.PROTECT, null=True, blank=True, editable=False)
    campus = models.ForeignKey('schools.Campus', verbose_name='Campus', on_delete=models.PROTECT, null=True, blank=True, editable=False)

    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)

    # Fields
    invoiceNumber = models.PositiveIntegerField('Invoice number', unique=True, editable=False)
    invoicedDate = models.DateField('Invoiced date', null=True, blank=True) # Set when invoice first viewed
    purchaseOrderNumber = models.CharField('Purchase order number', max_length=30, blank=True)
    notes = models.TextField('Notes', blank=True)

    # Cache fields
    cache_amountGST_unrounded = models.FloatField('amountGST_unrounded', blank=True, null=True, editable=False)
    cache_totalQuantity = models.IntegerField('cache_totalQuantity', blank=True, null=True, editable=False)
    cache_invoiceAmountExclGST_unrounded = models.FloatField('cache_invoiceAmountExclGST_unrounded', blank=True, null=True, editable=False)
    cache_invoiceAmountInclGST_unrounded = models.FloatField('cache_invoiceAmountInclGST_unrounded', blank=True, null=True, editable=False)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Invoice'
        constraints = [
            models.UniqueConstraint(fields=['event', 'school'], condition=Q(campus=None), name='event_school'),
            models.UniqueConstraint(fields=['event', 'invoiceToUser'], condition=Q(school=None), name='event_user'),
            models.UniqueConstraint(fields=['event', 'school', 'campus'], name='event_school_campus'),
        ]
        ordering = ['-invoiceNumber']

    # *****Permissions*****
    @classmethod
    def stateCoordinatorPermissions(cls, level):
        if level == 'full':
            return [
                'add',
                'view',
                'change',
                'delete'
            ]
        elif level == 'billingmanager':
            return [
                'add',
                'view',
                'change',
                'delete'
            ]
        elif level in ['viewall']:
            return [
                'view',
            ]
        
        return []

    # Used in state coordinator permission checking
    def getState(self):
        return self.event.state

    # *****Save & Delete Methods*****

    def preSave(self):
        # Set invoice number
        if self.invoiceNumber is None:
            try:
                self.invoiceNumber = Invoice.objects.latest('invoiceNumber').invoiceNumber + 1
            except Invoice.DoesNotExist:
                try:
                    self.invoiceNumber = InvoiceGlobalSettings.objects.get().firstInvoiceNumber
                except InvoiceGlobalSettings.DoesNotExist:
                    self.invoiceNumber = 1
        
        # Set invoiced date to payment due date if None, when mentor views invoice date will get brought forward to current date if before paymend due date
        if self.invoicedDate is None:
            self.invoicedDate = self.event.paymentDueDate

    def postSave(self):
        self.calculateAndSaveAllTotals()

    def postDelete(self):
        # In case campus invoicing enabled and an invoice is deleted, recalculate totals on remaining
        for invoice in Invoice.objects.filter(school=self.school, event=self.event):
            invoice.calculateAndSaveAllTotals()

    # *****Methods*****

    # *****Get Methods*****

    def invoiceToUserName(self):
        return self.invoiceToUser.fullname_or_email()
    invoiceToUserName.short_description = 'Mentor'
    invoiceToUserName.admin_order_field = 'invoiceToUser'

    def invoiceToUserEmail(self):
        return self.invoiceToUser.email
    invoiceToUserEmail.short_description = 'Mentor email'
    invoiceToUserEmail.admin_order_field = 'invoiceToUser__email'

    @classmethod
    def invoicesForUser(cls, user):
        return Invoice.objects.filter(Q(invoiceToUser=user) | Q(school__schooladministrator__user=user)).distinct()

    def hiddenInvoice(self):
        return self.invoiceAmountInclGST_unrounded() < 0.05 and not self.invoicepayment_set.exists()

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('invoices:details', kwargs = {"invoiceID": self.id})

    # Campus

    # Returns true if campus based invoicing enabled for this school for this event
    def campusInvoicingEnabled(self):
        if not self.school:
            return False

        # Check if at least one invoice has campus field set
        return Invoice.objects.filter(school=self.school, event=self.event, campus__isnull=False).exists()

    # Returns true if teams with campus for this school and event exists and campus invoicing not already enabled
    def campusInvoicingAvailable(self):
        from teams.models import Team
        if not self.school:
            return False

        if self.campusInvoicingEnabled():
            return False

        # Check no payments made
        if self.invoicepayment_set.exists():
            return False

        return Team.objects.filter(school=self.school, event=self.event, campus__isnull=False).exists()

    # Teams

    # Filter for all items covered by this ivoice
    def allItemsFilterFields(self, ignoreCampus=False):
        if self.campusInvoicingEnabled() and not ignoreCampus:
            # Filter by school and campus
            return {
                'event': self.event,
                'school': self.school,
                'campus': self.campus,
                'invoiceOverride': None,
            }

        elif self.school:
            # If school but campuses not enableed filter by school
            return {
                'event': self.event,
                'school': self.school,
                'invoiceOverride': None,
            }

        else:
            # If no school filter by user
            return {
                'event': self.event,
                'mentorUser': self.invoiceToUser,
                'school': None,
                'invoiceOverride': None,
            }

    # Queryset of teams covered by this invoice
    def allTeams(self):
        from teams.models import Team
        return Team.objects.filter(**self.allItemsFilterFields())

    # Special rate teams

    # All special rate teams for this school/ mentor if independent
    def specialRateTeamsForSchool(self):
        from teams.models import Team

        numberSpecialRateTeams = self.event.competition_specialRateNumber

        # Check for special rate enabled
        if not numberSpecialRateTeams:
            return Team.objects.none()

        # Get special rate teams for this school for this invoice
        specialRateTeams = Team.objects.filter(**self.allItemsFilterFields(ignoreCampus=True)).order_by('creationDateTime')[:numberSpecialRateTeams]

        return specialRateTeams

    # Special rate teams for this invoice
    def specialRateTeams(self):
        # Filter teams for this invoice to those that receive special rate
        return self.allTeams().filter(pk__in=self.specialRateTeamsForSchool().values_list('pk', flat=True))

    # Standard rate teams for this invoice - teams that don't receive the special rate
    def standardRateTeams(self):
        # Filter teams for this invoice to exclude those that receive special rate
        return self.allTeams().exclude(pk__in=self.specialRateTeamsForSchool().values_list('pk', flat=True))

    # Need methods to calculate teams or students that get special rate and teams that don't
    # Maybe just make special rate require teams

    # Invoice items

    def standardRateDivisions(self):
        from events.models import Division
        return Division.objects.filter(baseeventattendance__in=self.standardRateTeams()).distinct()

    def invoiceItem(self, name, description, quantity, rawUnitCost, unit=None, excludeFromSurcharge=False):
        # Calculate totals
        if self.event.entryFeeIncludesGST:
            unitCost = rawUnitCost / 1.1
            totalInclGST = quantity * rawUnitCost
            totalExclGST = totalInclGST / 1.1
            gst = totalInclGST - totalExclGST

        else:
            unitCost = rawUnitCost
            totalExclGST = quantity * rawUnitCost
            gst = 0.1 * totalExclGST
            totalInclGST = totalExclGST * 1.1

        return {
            'name': name,
            'description': description,
            'quantity': quantity,
            'surchargeQuantity': quantity if unitCost > 0 and not excludeFromSurcharge else 0,
            'unitCost': unitCost,
            'unit': unit,
            'totalExclGST': totalExclGST,
            'gst': gst,
            'totalInclGST': totalInclGST,
        }

    def surchargeInvoiceItem(self, quantity):
        # Get surcharge name and description
        try:
            surchargeName = InvoiceGlobalSettings.objects.get().surchargeName
            surchargeInvoiceDescription = InvoiceGlobalSettings.objects.get().surchargeInvoiceDescription
        except InvoiceGlobalSettings.DoesNotExist:
            surchargeName = 'Surcharge'
            surchargeInvoiceDescription = ''

        # Get values
        unitCost = self.event.eventSurchargeAmount / 1.1
        totalExclGST = quantity * unitCost
        gst = 0.1 * totalExclGST
        totalInclGST = quantity * self.event.eventSurchargeAmount

        return {
            'name': surchargeName,
            'description': surchargeInvoiceDescription,
            'quantity': quantity,
            'unitCost': unitCost,
            'unit': None,
            'totalExclGST': totalExclGST,
            'gst': gst,
            'totalInclGST': totalInclGST,
        }

    def workshopInvoiceItem(self, attendees, division, nameSuffix, unitCost, override):
        namePrefix = "Other attendees - " if override else ""
        name = f'{namePrefix}{division.name} - {nameSuffix}'
        description = ", ".join(map(lambda attendee: attendee.strNameAndSchool(), attendees)) if override else ""
        return self.invoiceItem(name, description, attendees.count(), unitCost)
    
    def workshopInvoiceItems(self, attendees, override=False):
        invoiceItems = []

        # Get details
        teacherUnitCost = self.event.workshopTeacherEntryFee
        studentUnitCost = self.event.workshopStudentEntryFee

        # Get divisions
        from events.models import Division
        divisions = Division.objects.filter(baseeventattendance__in=attendees).distinct()

        # Create invoice items
        for division in divisions:
            # Split teacher and student

            # Teachers
            teacherAttedees = attendees.filter(division=division, attendeeType='teacher')
            if teacherAttedees.count() > 0:
                invoiceItems.append(self.workshopInvoiceItem(teacherAttedees, division, 'teacher', teacherUnitCost, override))

            # Students
            studentAttedees = attendees.filter(division=division, attendeeType='student')
            if studentAttedees.count() > 0:
                invoiceItems.append(self.workshopInvoiceItem(studentAttedees, division, 'student', studentUnitCost, override))
        
        return invoiceItems

    def competitionDivisionInvoiceItem(self, teams, division, namePrefix = "", description = ""):
        from events.models import AvailableDivision
        from teams.models import Student
        # Get available division
        try:
            availableDivision = self.event.availabledivision_set.get(division=division)
        except AvailableDivision.DoesNotExist:
            availableDivision = None

        # Get unit cost, use availableDivision value if present, otherwise use value from event
        unitCost = self.event.competition_defaultEntryFee
        unit = self.event.competition_billingType
        if availableDivision and availableDivision.division_entryFee is not None:
            unitCost = availableDivision.division_entryFee
            unit = availableDivision.division_billingType

        # Get quantity
        quantity = 0
        if unit == 'team':
            quantity = teams.count()

        elif unit == 'student':
            quantity = Student.objects.filter(team__in=teams).count()
            
        return self.invoiceItem(f"{namePrefix}{division.name}", description, quantity, unitCost, unit)

    def competitionInvoiceItems(self):

        invoiceItems = []

        # Special rate entries
        numberSpecialRateTeams = self.specialRateTeams().count()
        if numberSpecialRateTeams:

            # Get values
            quantity = numberSpecialRateTeams
            unitCost = self.event.competition_specialRateFee

            maxNumberSpecialRateTeams = self.event.competition_specialRateNumber
            name = f"First {maxNumberSpecialRateTeams} {'team' if maxNumberSpecialRateTeams <= 1 else 'teams'}"
            description = 'This is measured across all campuses from this school'

            invoiceItems.append(self.invoiceItem(name, description, quantity, unitCost, 'team'))

        # Standard rate entries
        for division in self.standardRateDivisions():
            teams = self.standardRateTeams().filter(division=division)
        
            invoiceItems.append(self.competitionDivisionInvoiceItem(teams, division))

        return invoiceItems

    def overrideInvoiceItems(self):
        from teams.models import Team
        from events.models import Division
        from workshops.models import WorkshopAttendee

        invoiceItems = []

        teams = Team.objects.filter(invoiceOverride=self)
        divisions = Division.objects.filter(baseeventattendance__in=teams).distinct()

        for division in divisions:
            divisionTeams = teams.filter(division=division)
            teamNames = ", ".join(map(lambda team: team.strNameAndSchool(), divisionTeams))
            invoiceItems.append(self.competitionDivisionInvoiceItem(divisionTeams, division, namePrefix="Other teams - ", description=teamNames))

        attendees = WorkshopAttendee.objects.filter(invoiceOverride=self)
        invoiceItems += self.workshopInvoiceItems(attendees, override=True)

        return invoiceItems

    def invoiceItems(self):
        from workshops.models import WorkshopAttendee
        invoiceItems = []

        if self.event.eventType == 'workshop':
            # All workshop attendees for this invoice        
            attendees = WorkshopAttendee.objects.filter(**self.allItemsFilterFields())
            invoiceItems += self.workshopInvoiceItems(attendees)

        elif self.event.eventType == 'competition':
            invoiceItems += self.competitionInvoiceItems()

        invoiceItems += self.overrideInvoiceItems()

        # Add surcharge if not $0
        surchargeQuantity = sum([item['surchargeQuantity'] for item in invoiceItems])
        if self.event.eventSurchargeAmount > 0 and surchargeQuantity > 0:
            invoiceItems.append(self.surchargeInvoiceItem(surchargeQuantity))

        return invoiceItems

    # Calculate and save cached totals
    def calculateAndSaveAllTotals(self):
        self.cache_amountGST_unrounded = self.calculate_amountGST_unrounded()
        self.cache_totalQuantity = self.calculate_totalQuantity()
        self.cache_invoiceAmountExclGST_unrounded = self.calculate_invoiceAmountExclGST_unrounded()
        self.cache_invoiceAmountInclGST_unrounded = self.calculate_invoiceAmountInclGST_unrounded()

        self.save(skipPrePostSave=True, update_fields=[
            'cache_amountGST_unrounded',
            'cache_totalQuantity',
            'cache_invoiceAmountExclGST_unrounded',
            'cache_invoiceAmountInclGST_unrounded',
        ])

    # Totals

    def amountPaid_unrounded(self):
        try:
            return self._sumPayments if self._sumPayments is not None else 0
        except AttributeError:
            return sum(self.invoicepayment_set.values_list('amountPaid', flat=True))

    def amountPaid(self):
        return round(self.amountPaid_unrounded(), 2)
    amountPaid.short_description = 'Amount paid'
    amountPaid.admin_order_field = '_sumPayments'

    def calculate_amountGST_unrounded(self):
        return sum([item['gst'] for item in self.invoiceItems()])

    def amountGST_unrounded(self):
        if self.cache_amountGST_unrounded is None:
            self.calculateAndSaveAllTotals()
        return self.cache_amountGST_unrounded

    def amountGST(self):
        return round(self.amountGST_unrounded(), 2)
    amountGST.short_description = 'GST'

    def calculate_totalQuantity(self):
        return sum([item['quantity'] for item in self.invoiceItems()])

    def totalQuantity(self):
        if self.cache_totalQuantity is None:
            self.calculateAndSaveAllTotals()
        return self.cache_totalQuantity

    # Invoice amount

    def calculate_invoiceAmountExclGST_unrounded(self):
        return sum([item['totalExclGST'] for item in self.invoiceItems()])

    def invoiceAmountExclGST_unrounded(self):
        if self.cache_invoiceAmountExclGST_unrounded is None:
            self.calculateAndSaveAllTotals()
        return self.cache_invoiceAmountExclGST_unrounded

    def invoiceAmountExclGST(self):
        return round(self.invoiceAmountExclGST_unrounded(), 2)
    invoiceAmountExclGST.short_description = 'Invoice amount (ex GST)'

    def calculate_invoiceAmountInclGST_unrounded(self):
        return sum([item['totalInclGST'] for item in self.invoiceItems()])

    def invoiceAmountInclGST_unrounded(self):
        if self.cache_invoiceAmountInclGST_unrounded is None:
            self.calculateAndSaveAllTotals()
        return self.cache_invoiceAmountInclGST_unrounded

    def invoiceAmountInclGST(self):
        return round(self.invoiceAmountInclGST_unrounded(), 2)
    invoiceAmountInclGST.short_description = 'Invoice amount (incl GST)'
    invoiceAmountInclGST.admin_order_field = 'cache_invoiceAmountInclGST_unrounded'

    # Amount due

    def amountDueInclGST_unrounded(self):
        amountDue = self.invoiceAmountInclGST_unrounded() - self.amountPaid_unrounded()
        if amountDue < 0:
            return 0
        return amountDue

    def amountDueInclGST(self):
        return round(self.amountDueInclGST_unrounded(), 2)
    amountDueInclGST.short_description = 'Amount due (incl GST)'
    amountDueInclGST.admin_order_field = '_amountDueUnrounded'

    def amountDuePaypal(self):
        if self.amountDueInclGST_unrounded() < 0.05: # 0.05 to avoid tiny sum edge caes
            return 0
        return round(self.amountDueInclGST_unrounded() * 1.0275 + 0.3, 2)
    amountDuePaypal.short_description = 'Amount due (PayPal)'

    def paypalAvailable(self):
        return bool(self.event.state.paypalEmail) and self.amountDueInclGST_unrounded() >= 0.05 # 0.05 to avoid tiny sum edge caes

    def __str__(self):
        if self.campus:
            return f'Invoice {self.invoiceNumber}: {self.school}, {self.campus}'
        elif self.school:
            return f'Invoice {self.invoiceNumber}: {self.school}'
        else:
            return f'Invoice {self.invoiceNumber}: {self.invoiceToUser.fullname_or_email()}'

    # *****CSV export methods*****

    # *****Email methods*****

class InvoicePayment(models.Model):
    # Foreign keys
    invoice = models.ForeignKey(Invoice, verbose_name='Invoice', on_delete=models.PROTECT)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    amountPaid = models.FloatField('Amount paid')
    datePaid = models.DateField('Date paid')

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Payment'
        ordering = ['invoice', 'datePaid']

    # *****Permissions*****
    @classmethod
    def stateCoordinatorPermissions(cls, level):
        return Invoice.stateCoordinatorPermissions(level)

    # Used in state coordinator permission checking
    def getState(self):
        return self.invoice.event.state

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return f'{self.invoice}: {self.datePaid}'

    # *****CSV export methods*****

    # *****Email methods*****
