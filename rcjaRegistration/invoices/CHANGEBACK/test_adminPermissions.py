from common.baseTests import Base_Test_NotStaff, Base_Test_SuperUser, Base_Test_FullCoordinator, Base_Test_ViewCoordinator, createEvents, createTeams, createInvoices, POST_VALIDATION_FAILURE, POST_SUCCESS

from django.test import TestCase
from django.urls import reverse

import datetime

# Team

class Invoice_Base:
    modelName = 'Invoice'
    modelURLName = 'invoices_invoice'
    state1Obj = 'state1_event1_invoice1'
    state2Obj = 'state2_event1_invoice2'
    validPayload = {
        'purchaseOrderNumber': 'PONum',
        'notes': 'Notes',
        'invoicepayment_set-TOTAL_FORMS': 0,
        'invoicepayment_set-INITIAL_FORMS': 0,
        'invoicepayment_set-MIN_NUM_FORMS': 0,
        'invoicepayment_set-MAX_NUM_FORMS': 1000,
    }

    @classmethod
    def additionalSetup(cls):
        createEvents(cls)
        createInvoices(cls)
        createTeams(cls)

class Test_Invoice_NotStaff(Invoice_Base, Base_Test_NotStaff, TestCase):
    pass

class Test_Invoice_SuperUser(Invoice_Base, Base_Test_SuperUser, TestCase):
    addLoadsCode = 403
    addPostCode = 403

    expectedListItems = 2
    expectedStrings = [
        'State 1 Open Competition',
        'State 2 Open Competition',
    ]
    expectedMissingStrings = []

class Invoice_Coordinators_Base(Invoice_Base):
    addLoadsCode = 403
    addPostCode = 403

    expectedListItems = 1
    expectedStrings = [
        'State 1 Open Competition',
    ]
    expectedMissingStrings = [
        'State 2 Open Competition',
    ]

class Test_Invoice_FullCoordinator(Invoice_Coordinators_Base, Base_Test_FullCoordinator, TestCase):
    pass

class Test_Invoice_ViewCoordinator(Invoice_Coordinators_Base, Base_Test_ViewCoordinator, TestCase):
    pass
