from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib.auth.models import User
import os
from .models import Chat
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import openai
from openai import OpenAI
from django.views.decorators.csrf import csrf_exempt



# Create your views here.
from django.conf import settings

openai_api_key='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'
openai.api_key=openai_api_key
#     if not openai.api_key:
#     raise ValueError("No OpenAI API key found")
# openai.api_key=openai_api_key

def ask_openai(message):
    # try:
        response=openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {'role':"system", 'content':"You are a helpful government assistant"},
                {'role':"user", 'content':message},
            ]
        )
        print(response)
        answer=response.choices[0].message.content.strip()
        return answer
    # except Exception as e:
    #     print(f"An unexpected error occurred: {e}")
    #     return None

# @login_required
# @csrf_exempt
def chatbot(request):
    chats=Chat.objects.filter(user=request.user.id)

    if request.method=='POST':
        message=request.POST.get('message')
        response=ask_openai(message)

        chat=Chat(user=request.user, message=message, response=response, created_at=timezone.now())
        chat.save()
        return JsonResponse({'message':message, 'response':response})
    return render(request, 'chatbot.html', {'chats':chats})

def login(request):
    if request.method=='POST':
        username=request.POST['username']
        password=request.POST['password']
        user=auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request,user)
            return redirect('chatbot')
        else:
            error_message='Invalid username or password'
            return render(request, 'login.html',{'error_message':error_message})
    else:
        return render(request, 'login.html')

def register(request):
    if request.method=='POST':
        username=request.POST['username']
        email=request.POST['email']
        password1=request.POST['password1']
        password2=request.POST['password2']

        if password1 == password2:
            try:
                user=User.objects.create_user(username, email,password1)
                user.save()
                auth.login(request,user)
                return redirect('chatbot')
            except:
                error_message='Error creating account'
                return render(request, 'register.html',{'error_message':error_message})
        else:
            error_message='Passwords dont match'
            return render(request, 'register.html', {'error_message':error_message})
    return render(request, 'register.html')


    
def logout(request):
    auth.logout(request)
    return redirect('/')