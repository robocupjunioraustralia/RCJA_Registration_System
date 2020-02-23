from django.test import TestCase
from .models import InvoiceGlobalSettings, Invoice, InvoicePayment
from django.core.exceptions import ValidationError

class TestInvoiceGlobalSettings(TestCase):
    def setUp(self):
        pass

    def testStr(self):
        settingsObj = InvoiceGlobalSettings.objects.create(invoiceFromName='1', invoiceFromDetails='1')
        self.assertEqual(str(settingsObj), 'Invoice settings')

    def testObject1Limit(self):
        ob1 = InvoiceGlobalSettings.objects.create(invoiceFromName='1', invoiceFromDetails='1')
        self.assertEqual(str(ob1), 'Invoice settings')

        obj2 = InvoiceGlobalSettings(invoiceFromName='2', invoiceFromDetails='2')
        self.assertRaises(ValidationError, obj2.clean)
