from django.core.management import call_command
from django.test import TestCase
from io import StringIO


from regions.models import State

class Test_createexampledata_command(TestCase):
    def test_createexampledata(self):
        self.assertEqual(State.objects.count(), 0)

        out = StringIO()
        call_command(
            'createexampledata',
            stdout=out,
            stderr=StringIO()
        )
        self.assertEqual(out.getvalue(), 'Successfully created example data\n')

        self.assertEqual(State.objects.count(), 2)
