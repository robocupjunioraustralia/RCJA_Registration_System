from django.test import TestCase

from .fields import UUIDFileField

# Create your tests here.

class FileObj:
    def __init__(self):
        pass

class Test_generateUUIDFilename(TestCase):
    def setUp(self):
        self.fileObj = FileObj()

    def testBothDefinedWithExtension(self):
        fieldInstance = UUIDFileField('File', upload_prefix="TestPrefix", original_filename_field="originalFilename")
        filename = fieldInstance.generateUUIDFilename(self.fileObj, 'newFile.txt')

        self.assertIn("TestPrefixs/TestPrefix_", filename)
        self.assertIn(".txt", filename)
        self.assertEqual(self.fileObj.originalFilename, 'newFile.txt')

    def testNoPrefixWithExtension(self):
        fieldInstance = UUIDFileField('File', original_filename_field="originalFilename")
        filename = fieldInstance.generateUUIDFilename(self.fileObj, 'newFile.txt')

        self.assertEqual(filename, 'newFile.txt')
        self.assertEqual(self.fileObj.originalFilename, 'newFile.txt')

    def testNoOriginalFilenameWithExtension(self):
        self.fileObj.originalFilename = 'existingName'

        fieldInstance = UUIDFileField('File', upload_prefix="TestPrefix")
        filename = fieldInstance.generateUUIDFilename(self.fileObj, 'newFile.txt')

        self.assertIn("TestPrefixs/TestPrefix_", filename)
        self.assertIn(".txt", filename)
        self.assertEqual(self.fileObj.originalFilename, 'existingName')

    def testBothDefinedNoExtension(self):
        fieldInstance = UUIDFileField('File', upload_prefix="TestPrefix", original_filename_field="originalFilename")
        filename = fieldInstance.generateUUIDFilename(self.fileObj, 'newFile')

        self.assertIn("TestPrefixs/TestPrefix_", filename)
        self.assertEqual(self.fileObj.originalFilename, 'newFile')
