from django.test import TestCase

class TestNonTest(TestCase):
    def testEquality(self):
        self.assertEqual('foo','foo')
    def test_truth(self):
        self.assertTrue(True,True)
    def test_failure(self):
        self.assertTrue(False)
        self.assertFalse(True)


if __name__ == '__main__':
    unittest.main()
# Create your tests here.
