from django.test import TestCase

class DummyTest(TestCase):
    def testEquality(self):
        self.assertEqual('foo','foo')
    def testTruth(self):
        self.assertTrue(True,True)

# Create your tests here.
