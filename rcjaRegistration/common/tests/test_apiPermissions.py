from django.test import TestCase

from common.apiPermissions import IsSuperUser, AuthenticatedReadOnly, ReadOnly

class RequestObj:
    def __init__(self, user, method):
        self.user = user
        self.method = method

class UserObj:
    def __init__(self, is_authenticated, is_active, is_superuser):
        self.is_authenticated = is_authenticated
        self.is_active = is_active
        self.is_superuser = is_superuser

class TestIsSuperUser(TestCase):
    def testNoUserDenied(self):
        request = RequestObj(None, 'GET')

        self.assertFalse(IsSuperUser.has_permission(None, request, None))

    def testActiveSuperuserAllowed(self):
        request = RequestObj(UserObj(True, True, True), 'GET')

        self.assertTrue(IsSuperUser.has_permission(None, request, None))

    def testInactiveSuperuserDenied(self):
        request = RequestObj(UserObj(True, False, True), 'GET')

        self.assertFalse(IsSuperUser.has_permission(None, request, None))

    def testNotSuperuserDenied(self):
        request = RequestObj(UserObj(True, True, False), 'GET')

        self.assertFalse(IsSuperUser.has_permission(None, request, None))

class TestAuthenticatedReadOnly(TestCase):
    def testNoUserDenied(self):
        request = RequestObj(None, 'GET')

        self.assertFalse(AuthenticatedReadOnly.has_permission(None, request, None))

    def testActiveUserGetAllowed(self):
        request = RequestObj(UserObj(True, True, False), 'GET')

        self.assertTrue(AuthenticatedReadOnly.has_permission(None, request, None))

    def testActiveUserPostDenied(self):
        request = RequestObj(UserObj(True, True, False), 'POST')

        self.assertFalse(AuthenticatedReadOnly.has_permission(None, request, None))

    def testInactiveUserGetDenied(self):
        request = RequestObj(UserObj(True, False, False), 'GET')

        self.assertFalse(AuthenticatedReadOnly.has_permission(None, request, None))

    def testUnathenticatedUserDenied(self):
        request = RequestObj(UserObj(False, True, False), 'GET')

        self.assertFalse(AuthenticatedReadOnly.has_permission(None, request, None))

class TestReadOnly(TestCase):
    def testNoUserGetAllowed(self):
        request = RequestObj(None, 'GET')

        self.assertTrue(ReadOnly.has_permission(None, request, None))

    def testNoUserPostDenied(self):
        request = RequestObj(None, 'POST')

        self.assertFalse(ReadOnly.has_permission(None, request, None))
