from django.http import HttpResponseRedirect
from django.urls import reverse

class RedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            # Only want to redirect on logged in pages

            # Check redirect conditions in this order
            redirectTo = None
            from schools.models import School
            try:
                if request.user.forcePasswordChange:
                    redirectTo = reverse('password_change')
                elif request.user.forceDetailsUpdate:
                    redirectTo = reverse('users:details')
                elif request.user.currentlySelectedSchool and request.user.currentlySelectedSchool.forceSchoolDetailsUpdate:
                    redirectTo = reverse('schools:details')
            except School.DoesNotExist:
                pass # If school just deleted don't attempt redirection

            neverRedirect = [
                reverse('users:termsAndConditions'),
            ]

            if redirectTo and request.path != redirectTo and request.path not in neverRedirect:
                return HttpResponseRedirect(redirectTo)

        return response
