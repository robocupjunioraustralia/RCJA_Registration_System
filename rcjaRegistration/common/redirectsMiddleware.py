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
            if request.user.forcePasswordChange:
                redirectTo = reverse('password_change')
            elif request.user.forceDetailsUpdate:
                redirectTo = reverse('users:details')

            if redirectTo and request.path != redirectTo:
                return HttpResponseRedirect(redirectTo)

        return response
