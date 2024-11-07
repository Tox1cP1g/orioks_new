from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import VoteOption, Vote



@login_required
def index(request):
    return render(request, 'index.html', {'user': request.user})


def register(request):
    return render(request, 'register.html')


def phone_directory(request):
    return render(request, 'phone_directory.html')


def vote(request):
    options = VoteOption.objects.all()

    if request.method == "POST":
        option_id = request.POST.get("option")
        ip_address = request.META.get('REMOTE_ADDR')

        try:
            option = VoteOption.objects.get(id=option_id)
            Vote.objects.create(option=option, ip_address=ip_address)
            return render(request, 'vote_result.html', {'message': "Спасибо за ваш голос"})
        except VoteOption.DoesNotExist:
            return render(request, 'vote_result.html', {'message': "Неверный выбор"})

    return render(request, 'vote.html', {'options': options})