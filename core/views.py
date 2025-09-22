from django.shortcuts import render, redirect

def landing_page(request):
    """Landing page com marketing e opções de cadastro"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    return render(request, 'core/landing_page.html')
