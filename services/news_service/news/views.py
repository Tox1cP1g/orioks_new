# news/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import News
from .forms import NewsForm

def news_list(request):
    source = request.GET.get('source', '')  # Get source parameter from URL
    role = request.GET.get('role', '')  # Get role parameter from URL
    news = News.objects.all().order_by('-created_at')
    return render(request, 'news/news_list.html', {
        'news': news,
        'source': source,
        'role': role,
        'is_teacher': role == 'TEACHER'  # Add is_teacher flag to template context
    })

def news_detail(request, news_id):
    source = request.GET.get('source', '')  # Get source parameter from URL
    role = request.GET.get('role', '')  # Get role parameter from URL
    news_item = get_object_or_404(News, id=news_id)
    return render(request, 'news/news_detail.html', {
        'news_item': news_item,
        'source': source,
        'role': role,
        'is_teacher': role == 'TEACHER'  # Add is_teacher flag to template context
    })

def add_news(request):
    if request.method == 'POST':
        form = NewsForm(request.POST)
        if form.is_valid():
            form.save()
            source = request.GET.get('source', '')
            role = request.GET.get('role', '')
            return redirect(f"{reverse('news_list')}?source={source}&role={role}")
    else:
        form = NewsForm()
    return render(request, 'news/news_form.html', {'form': form})