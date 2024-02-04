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
from django.conf import settings

from . import models
from django.db.models import Count, Case, When, FloatField

from textblob import TextBlob
from collections import Counter
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import nltk
nltk.download('stopwords')
nltk.download('punkt')

import spacy


from .forms import DashboardFilterForm

openai_api_key='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'
openai.api_key=openai_api_key
#     if not openai.api_key:
#     raise ValueError("No OpenAI API key found")
# openai.api_key=openai_api_key

# Create your views here.
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
        category, sentiment=categorize_and_analyze_sentiment(message)


        chat=Chat(user=request.user, message=message, response=response, created_at=timezone.now(), category=category, sentiment_score=sentiment)
        for chat in Chat.objects.all():
            chat.classification = sentiment_status(chat.sentiment_score)
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

# def overall_sentiment_score(request):
#     total_score=0
#     count=0
#     messages=Chat.objects.exclude(sentiment_score=None)

#     for message in messages:
#         total_score+=message.sentiment_score
#         count +=1

#     if count >0:
#         average_score=round(total_score/count,2)
#         if average_score > 0.1:
#             overall_sentiment= 'Positive'
#         elif average_score < -0.1:
#             overall_sentiment ='Negative'
#         else:
#             overall_sentiment='Neutral'
#     else:
#         overall_sentiment='No data'
#         average_score=None


#     context={
#         'overall_sentiment':overall_sentiment,
#         'average_score':average_score if count > 0 else None,
#     }    
#     return render(request, 'overallsentiments.html', context)

# def sentiment_over_time(request):
#     end_date=datetime.now()
#     start_date=end_date-timedelta(days=7)

#     data=(Chat.objects.filter(created_at__range=(start_date, end_date))
#           .annotate(date=TruncDay('created_at'))
#           .values('date')
#           .annotate(average_score=Avg('sentiment_score'))
#           .order_by('date'))
    
#     if not data:
#        dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)]
#        scores = [0 for _ in range(8)]
    
#     else:
#         dates = [item['date'].strftime('%Y-%m-%d') for item in data]
#         scores = [item['average_score'] for item in data]

#     context={
#         'dates':json.dumps(dates),
#         'scores':json.dumps(scores),
#     }
#     print(dates)
#     print(scores)
#     return render(request, 'overallsentiments.html', context)

# def sentiment_distribution(request):
#     sentiments=Chat.objects.aggregate(
#         positive=Count(Case(When(sentiment_score__gt=0.1, then=1), output_field=FloatField())),
#         negative=Count(Case(When(sentiment_score__lt=-0.1, then=1), output_field=FloatField())),
#         neutral=Count(Case(When(sentiment_score__lte=0.1, sentiment_score__gte=-0.1, then=1), output_field=FloatField())),
#     )
#     context={
#         'sentiments':sentiments,
#     }
#     return render(request, 'overallsentiments.html', context)
def analyze_keywords(messages):
    positive_keywords=[]
    negative_keywords=[]

    stop_words=set(stopwords.words('english'))

    messages=Chat.objects.all()

    for message in messages:
        analysis=TextBlob(message.message)
        keywords=[word for word in analysis.words.lower() if word not in stop_words]

        if analysis.sentiment.polarity>0:
            positive_keywords.extend(keywords)
        elif analysis.sentiment.polarity<0:
            negative_keywords.extend(keywords)

    positive_freq= Counter(positive_keywords)
    negative_freq=Counter(negative_keywords)

    top_positive=positive_freq.most_common(10)
    top_negative=negative_freq.most_common(10)

    return top_positive, top_negative

def matching_keywords(messages):
    #stemming
    stemmer=PorterStemmer()
    stop_words=set(stopwords.words('english'))
    tokens=word_tokenize(messages.lower())
    filtered_tokens=[stemmer.stem(word) for word in tokens if word not in stop_words and word.isalpha()]
    
    #lemmatization - bringing words to their dictionary form
    nlp=spacy.load("en_core_web_sm")
    doc=nlp(messages.lower())
    lemmas=[token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    
    return filtered_tokens, lemmas
def categorize_keywords(messages):
    categories={
        'Transport':['roads', 'road', 'potholes','pothole', 'accidents', 'accident'],
        'Health':['hospital', 'hospitals', 'doctors', 'nurses'],
        'Education':['schools', 'school', 'teacher','teachers', 'student', 'students', 'bursary', 'bursaries'],
    }

    for category, keywords in categories.items(matching_keywords):
        if any(keyword in messages.lower() for keyword in keywords):
            return category
    return 'general'

def categorize_and_analyze_sentiment(messages):
    category=categorize_keywords(messages)
    sentiment=TextBlob(messages).sentiment.polarity

    return category, sentiment    


def sentiment_analysis(request):
    # Sentiment over time
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    time_data = (Chat.objects.filter(created_at__range=(start_date, end_date))
                 .annotate(date=TruncDay('created_at'))
                 .values('date')
                 .annotate(average_score=Avg('sentiment_score'))
                 .order_by('date'))

    dates = [item['date'].strftime('%Y-%m-%d') for item in time_data] if time_data else []
    scores = [item['average_score'] for item in time_data] if time_data else []

    # Sentiment distribution
    sentiments = Chat.objects.aggregate(
        positive=Count(Case(When(sentiment_score__gt=0.1, then=1), output_field=FloatField())),
        negative=Count(Case(When(sentiment_score__lt=-0.1, then=1), output_field=FloatField())),
        neutral=Count(Case(When(sentiment_score__lte=0.1, sentiment_score__gte=-0.1, then=1), output_field=FloatField())),
    )

    # Overall sentiment score
    total_score = 0
    count = 0
    messages = Chat.objects.exclude(sentiment_score=None)
    for message in messages:
        total_score += message.sentiment_score
        count += 1

    if count > 0:
        average_score = round(total_score / count, 2)
        if average_score > 0.1:
            overall_sentiment = 'Positive'
        elif average_score < -0.1:
            overall_sentiment = 'Negative'
        else:
            overall_sentiment = 'Neutral'
    else:
        overall_sentiment = 'No data'
        average_score = None

    #Analyze keywords
    messages=Chat.objects.all()
    top_positive, top_negative=analyze_keywords(messages)
    
    #sentiments by category
    category_sentiments=Chat.objects.values('category').annotate(average_sentiment=Avg('sentiment_score')).order_by('category')
    
    #list of users and their chats
    chats=Chat.objects.all().order_by('-created_at') #newest chats first

    #filter by user, category and time    
    form=DashboardFilterForm(request.GET)
    chats_category=Chat.objects.all()

    if form.is_valid():
        start_date=form.cleaned_data.get('start_date')
        end_date=form.cleaned_data.get('end_date')
        sentiment_category=form.cleaned_data.get('sentiment_category')
        user=form.cleaned_data.get('user')

        if start_date and end_date:
            chats_category=chats_category.filter(created_at__range=(start_date, end_date))
        if sentiment_category and sentiment_category !='All':
            chats_category=chats_category.filter(classification=sentiment_category)
        if user:
            chats_category=chats_category.filter(user=user)    


    context = {
        'dates': json.dumps(dates),
        'scores': json.dumps(scores),
        'sentiments': sentiments,
        'overall_sentiment': overall_sentiment,
        'average_score': average_score,
        'top_positive':top_positive,
        'top_negative':top_negative,
        'category_sentiments':category_sentiments,
        'chats':chats,
        'chats_category':chats_category,
        'form':form
    }
    return render(request, 'overallsentiments.html', context)
