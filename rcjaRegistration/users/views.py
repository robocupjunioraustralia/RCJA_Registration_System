from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from .forms import UserEditForm
from django.http import JsonResponse
from django.http import HttpResponseForbidden

from .models import User
from userquestions.models import Question, QuestionResponse
from userquestions.forms import QuestionResponseForm

@login_required
def editProfile(request):
    # Questions formset
    questions = Question.object.all()
    numberQuestions = questions.count()

    QuestionReponseFormSet = inlineformset_factory(
        User,
        QuestionResponse,
        form=QuestionResponseForm,
        extra=numberQuestions,
        max_num=numberQuestions,
        can_delete=False
    )

    questionResponseInitials = []

    for question in questions:
        questionResponseInitials.append({
            'question': question.id,
        })

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=request.user)
        questionFormset = QuestionReponseFormSet(request.POST, instance=request.user, initial=questionResponseInitials)

        if form.is_valid() and questionFormset.is_valid():
            # Save user
            user = form.save()

            # Save question response questionFormset
            questionFormset.save() 

            return redirect('/')
    else:
        form = UserEditForm(instance=request.user)
        questionFormset = QuestionReponseFormSet(request.POST, instance=request.user)
    return render(request, 'registration/profile.html', {'form': form, 'questionFormset': questionFormset})






    # if request.method == 'POST':
    #     formset = StudentInLineFormSet(request.POST, instance=team)
    #     form = TeamForm(request.POST, instance=team, user=request.user, event=event)
    #     form.mentorUser = request.user # Needed in form validation to check number of teams for independents not exceeded

    #     if form.is_valid() and formset.is_valid():
    #         # Create team object but don't save so can set foreign keys
    #         team = form.save(commit=False)
    #         team.mentorUser = request.user

    #         # Save team
    #         team.save()

    #         # Save student formset
    #         formset.save() 

    #         return redirect(reverse('events:summary', kwargs = {"eventID":event.id}))
    # else:
    #     form = TeamForm(instance=team, user=request.user, event=event)
    #     formset = StudentInLineFormSet(instance=team)
    # return render(request, 'teams/addTeam.html', {'form': form, 'formset':formset, 'event':event, 'team':team})