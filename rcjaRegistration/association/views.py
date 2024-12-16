from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

import datetime

from common.userInterface import render
from .forms import AssociationMemberForm
from .models import AssociationMember

@login_required
def membership(request):   
    try:
        associationMember = request.user.associationmember
    except AssociationMember.DoesNotExist:
        associationMember = None

    form = AssociationMemberForm(instance=associationMember)

    if request.method == 'POST':
        # Create Post versions of forms
        form = AssociationMemberForm(request.POST, instance=associationMember)

        if form.is_valid():
            # Save form
            associationMember = form.save(commit=False)
            associationMember.user = request.user
            if not associationMember.membershipStartDate:
                associationMember.membershipStartDate = datetime.date.today()
            
            associationMember.save()

            return redirect(reverse('association:membership'))

    return render(request, 'association/membership.html', {'form': form, 'associationMember': associationMember})
