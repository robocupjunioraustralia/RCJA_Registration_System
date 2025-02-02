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
            from association.models import AssociationMember
            try:
                if request.user.forcePasswordChange:
                    redirectTo = reverse('password_change')
                elif request.user.forceDetailsUpdate:
                    redirectTo = reverse('users:details')
                elif request.user.currentlySelectedSchool and request.user.currentlySelectedSchool.forceSchoolDetailsUpdate:
                    redirectTo = reverse('schools:details')
                elif request.user.is_staff and request.user.adminChangelogVersionShown != request.user.ADMIN_CHANGELOG_CURRENT_VERSION:
                    redirectTo = reverse('users:adminChangelog')
                    request.user.adminChangelogVersionShown = request.user.ADMIN_CHANGELOG_CURRENT_VERSION
                    request.user.save(update_fields=['adminChangelogVersionShown'])
                elif not request.user.is_superuser and request.user.is_staff:
                    try:
                        if not request.user.associationmember.rulesAcceptedDate:
                            redirectTo = reverse('association:membership')
                    except AssociationMember.DoesNotExist:
                        redirectTo = reverse('association:membership')
                elif not request.user.associationPageShown:
                    redirectTo = reverse('association:membership')

            except School.DoesNotExist:
                pass # If school just deleted don't attempt redirection

            neverRedirect = [
                reverse('users:termsAndConditions'),
            ]

            if redirectTo and request.path != redirectTo and request.path not in neverRedirect:
                return HttpResponseRedirect(redirectTo)

        return response
