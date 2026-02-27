from django.shortcuts import render

def render_app(request):
    return render(request, 'index.html')
