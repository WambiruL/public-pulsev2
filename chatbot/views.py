from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib.auth.models import User
import os
import json
from .models import Chat
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import openai
from openai import OpenAI
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg
from django.utils.timezone import datetime, timedelta
from django.db.models.functions import TruncDay

# Create your views here.
from django.conf import settings

from . import models

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

# def view_sentiments(request):
#     messages=Chat.objects.all()
#     return render(request, 'sentiments.html', {'messages':messages})

def sentiment_status(request):
    messages=Chat.objects.all()
    for message in messages:
        print(message.message, message.sentiment_status())

def overall_sentiment_score(request):
    total_score=0
    count=0
    messages=Chat.objects.exclude(sentiment_score=None)

    for message in messages:
        total_score+=message.sentiment_score
        count +=1

    if count >0:
        average_score=round(total_score/count,2)
        if average_score > 0.1:
            overall_sentiment= 'Positive'
        elif average_score < -0.1:
            overall_sentiment ='Negative'
        else:
            overall_sentiment='Neutral'
    else:
        overall_sentiment='No data'
        average_score=None


    context={
        'overall_sentiment':overall_sentiment,
        'average_score':average_score if count > 0 else None,
    }    
    return render(request, 'overallsentiments.html', context)

def sentiment_over_time(request):
    end_date=datetime.now()
    start_date=end_date-timedelta(days=7)

    data=(Chat.objects.filter(created_at__range=(start_date, end_date))
          .annotate(date=TruncDay('created_at'))
          .values('date')
          .annotate(average_score=Avg('sentiment_score'))
          .order_by('date'))
    
    if not data:
       dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)]
       scores = [0 for _ in range(8)]
    
    else:
        dates = [item['date'].strftime('%Y-%m-%d') for item in data]
        scores = [item['average_score'] for item in data]

    context={
        'dates':json.dumps(dates),
        'scores':json.dumps(scores),
    }
    print(dates)
    print(scores)
    return JsonResponse(request, 'overallsentiments.html', context)
