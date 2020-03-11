from django.db import models
from common.models import *
from django.conf import settings

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

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Invoice settings'

    # Allow only one instance of model
    def clean(self):
        if InvoiceGlobalSettings.objects.exclude(pk=self.pk).exists():
            raise(ValidationError('May only be one global settings object'))

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return 'Invoice settings'

class Invoice(CustomSaveDeleteModel):
    # Foreign keys
    event = models.ForeignKey('events.Event', verbose_name = 'Event', on_delete=models.CASCADE, editable=False)

    # User and school foreign keys
    invoiceToUser = models.ForeignKey('users.User', verbose_name='Invoice to', on_delete=models.PROTECT, editable=False)
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
    def coordinatorPermissions(cls, level):
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
        if self.invoiceNumber is None:
            try:
                self.invoiceNumber = Invoice.objects.latest('invoiceNumber').invoiceNumber + 1
            except Invoice.DoesNotExist:
                try:
                    self.invoiceNumber = InvoiceGlobalSettings.objects.get().firstInvoiceNumber
                except InvoiceGlobalSettings.DoesNotExist:
                    self.invoiceNumber = 1

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

    # Queryset of teams covered by this invoice
    def allTeams(self):
        from teams.models import Team
        if self.campusInvoicingEnabled():
            # Filter by school and campus
            return Team.objects.filter(event=self.event, school=self.school, campus=self.campus)

        elif self.school:
            # If school but campuses not enableed filter by school
            return Team.objects.filter(event=self.event, school=self.school)

        else:
            # If no school filter by user
            return Team.objects.filter(event=self.event, mentorUser=self.invoiceToUser, school=None)

    # Special rate teams

    # All special rate teams for this school/ mentor if independent
    def specialRateTeamsForSchool(self):
        from teams.models import Team

        numberSpecialRateTeams = self.event.event_specialRateNumber

        # Check for special rate enabled
        if not numberSpecialRateTeams:
            return Team.objects.none()

        # Get filter dict for teams for this school or mentor if independent
        if self.school:
            # If school
            teamFilterDict = {
                'event': self.event,
                'school': self.school,
            }

        else:
            # If no school filter by user
            teamFilterDict = {
                'event': self.event,
                'mentorUser': self.invoiceToUser,
                'school': None,
            }

        # Get special rate teams for this school for this invoice
        specialRateTeams = Team.objects.filter(**teamFilterDict).order_by('creationDateTime')[:numberSpecialRateTeams]

        return specialRateTeams

    # Special rate teams for this invoice
    def specialRateTeams(self):
        # Filter teams for this invoice to those that receive special rate
        return self.allTeams().filter(pk__in=self.specialRateTeamsForSchool().values_list('pk', flat=True))

    # Standard rate teams for this invoice - teams that don't receive the special rate
    def standardRateTeams(self):
        # Filter teams for this invoice to those that receive special rate
        return self.allTeams().exclude(pk__in=self.specialRateTeamsForSchool().values_list('pk', flat=True))

    # Need methods to calculate teams or students that get special rate and teams that don't
    # Maybe just make special rate require teams

    # Invoice items

    def standardRateDivisions(self):
        from events.models import Division
        return Division.objects.filter(team__in=self.standardRateTeams()).distinct()

    def invoiceItems(self):
        from events.models import AvailableDivision
        from teams.models import Student
        invoiceItems = []

        # Special rate entries
        numberSpecialRateTeams = self.specialRateTeams().count()
        maxNumberSpecialRateTeams = self.event.event_specialRateNumber
        if numberSpecialRateTeams:

            # Get values
            quantity = numberSpecialRateTeams
            quantityString = f"{quantity} {'team' if quantity <= 1 else 'teams'}"
            unitCost = self.event.event_specialRateFee

            # Calculate totals
            if self.event.entryFeeIncludesGST:
                totalInclGST = quantity * unitCost
                totalExclGST = totalInclGST / 1.1
                gst = totalInclGST - totalExclGST

            else:
                totalExclGST = quantity * unitCost
                gst = 0.1 * totalExclGST
                totalInclGST = totalExclGST * 1.1

            invoiceItems.append({
                'name': f"First {maxNumberSpecialRateTeams} {'team' if maxNumberSpecialRateTeams <= 1 else 'teams'}",
                'description': 'This is measured across all campuses from this school',
                'quantity': quantity,
                'quantityString': quantityString,
                'unitCost': unitCost,
                'totalExclGST': totalExclGST,
                'gst': gst,
                'totalInclGST': totalInclGST,
            })

        # Standard rate entries
        for division in self.standardRateDivisions():
            # Get available division
            try:
                availableDivision = self.event.availabledivision_set.get(division=division)
            except AvailableDivision.DoesNotExist:
                availableDivision = None

            teams = self.standardRateTeams().filter(division=division)

            # Get unit cost, use availableDivision value if present, otherwise use value from event
            unitCost = self.event.event_defaultEntryFee
            quantityMethod = self.event.event_billingType
            if availableDivision and availableDivision.division_entryFee is not None:
                unitCost = availableDivision.division_entryFee
                quantityMethod = availableDivision.division_billingType

            # Get quantity
            quantity = 0
            if quantityMethod == 'team':
                quantity = teams.count()

            elif quantityMethod == 'student':
                quantity = Student.objects.filter(team__in=teams).count()

            # Calculate totals
            if self.event.entryFeeIncludesGST:
                totalInclGST = quantity * unitCost
                totalExclGST = totalInclGST / 1.1
                gst = totalInclGST - totalExclGST

            else:
                totalExclGST = quantity * unitCost
                gst = 0.1 * totalExclGST
                totalInclGST = totalExclGST * 1.1

            # Quantity string
            quantityString = f"{quantity} {quantityMethod if quantity <= 1 else quantityMethod + 's'}"

            invoiceItems.append({
                'name': division.name,
                'description': '',
                'quantity': quantity,
                'quantityString': quantityString,
                'unitCost': unitCost,
                'totalExclGST': totalExclGST,
                'gst': gst,
                'totalInclGST': totalInclGST,
            })
        
        return invoiceItems

    # Totals

    def amountPaid(self):
        return round(sum(self.invoicepayment_set.values_list('amountPaid', flat=True)), 2)
    amountPaid.short_description = 'Amount paid'

    def amountGST(self):
        return round(sum([item['gst'] for item in self.invoiceItems()]), 2)
    amountGST.short_description = 'GST'

    # Invoice amount

    def invoiceAmountExclGST(self):
        return round(sum([item['totalExclGST'] for item in self.invoiceItems()]), 2)
    invoiceAmountExclGST.short_description = 'Invoice amount (ex GST)'

    def invoiceAmountInclGST(self):
        return round(sum([item['totalInclGST'] for item in self.invoiceItems()]), 2)
    invoiceAmountInclGST.short_description = 'Invoice amount (incl GST)'

    # Amount due

    def amountDueExclGST(self):
        return round(self.invoiceAmountExclGST() - self.amountPaid(), 2)
    amountDueExclGST.short_description = 'Amount due (ex GST)'

    def amountDueInclGST(self):
        return round(self.invoiceAmountInclGST() - self.amountPaid(), 2)
    amountDueInclGST.short_description = 'Amount due (incl GST)'

    def amountDuePaypal(self):
        if self.amountDueInclGST() < 0.05: # 0.05 to avoid tiny sum edge caes
            return 0
        return round(self.amountDueInclGST() * 1.0275 + 0.3, 2)
    amountDueInclGST.short_description = 'Amount due (PayPal)'

    def paypalAvailable(self):
        return bool(self.event.state.paypalEmail) and self.amountDueInclGST() >= 0.05 # 0.05 to avoid tiny sum edge caes

    def __str__(self):
        if self.campus:
            return f'{self.event}: {self.school}, {self.campus}'
        elif self.school:
            return f'{self.event}: {self.school}'
        else:
            return f'{self.event}: {self.invoiceToUser.fullname_or_email()}'

    # *****CSV export methods*****

    # *****Email methods*****

class InvoicePayment(models.Model):
    # Foreign keys
    invoice = models.ForeignKey(Invoice, verbose_name='Invoice', on_delete=models.PROTECT)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    amountPaid = models.PositiveIntegerField('Amount paid')
    datePaid = models.DateField('Date paid')

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Payment'
        ordering = ['invoice', 'datePaid']

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return f'{self.invoice}: {self.datePaid}'

    # *****CSV export methods*****

    # *****Email methods*****
