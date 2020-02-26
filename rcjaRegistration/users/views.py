from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from .forms import UserEditForm
from django.http import JsonResponse
from django.http import HttpResponseForbidden
from django.forms import modelformset_factory, inlineformset_factory

from .models import User
from userquestions.models import Question, QuestionResponse
from userquestions.forms import QuestionResponseForm

@login_required
def editProfile(request):
    # Questions formset
    questions = Question.objects.all()
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
            'user': request.user.id,
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
        questionFormset = QuestionReponseFormSet(instance=request.user, initial=questionResponseInitials)
    return render(request, 'registration/profile.html', {'form': form, 'questionFormset': questionFormset})
