from django.shortcuts import render, redirect
from django.contrib import auth
import json
from chatbot.models import Chat
from chatbot.forms import UpdateChatStatusForm
from django.db.models import Avg
from django.utils.timezone import datetime, timedelta
from django.utils import timezone
from django.db.models.functions import TruncDay
from django.db.models import Count, Case, When, FloatField

from textblob import TextBlob
from collections import Counter
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import nltk
nltk.download('stopwords')
nltk.download('punkt')

from django.db.models import Avg, F, ExpressionWrapper, fields
import spacy
from chatbot.forms import DashboardFilterForm
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
import joblib

from chatbot.forms import ChatFilterForm
from chatbot.models import UserProfile
from django.contrib.auth.models import User
# Create your views here.
# def view_sentiments(request):
#     messages=Chat.objects.all()
#     return render(request, 'sentiments.html', {'messages':messages})

def admin_dashboard(request):
    total_complaints=Chat.objects.count()
    new_complaints=Chat.objects.filter(status='new').count()
    resolved_complaints=Chat.objects.filter(status='resolved').count()
    pending_complaints=Chat.objects.filter(status='pending').count()

    resolved_complaints_times = Chat.objects.filter(status='resolved').exclude(resolved_at=None)
    response_times = resolved_complaints_times.annotate(
        response_time=ExpressionWrapper(
            F('resolved_at') - F('created_at'),
            output_field=fields.DurationField()
        )
    )
    avg_response_time = response_times.aggregate(avg_time=Avg('response_time'))['avg_time']

    # Convert avg_response_time to a total number of seconds, if it's not None
    avg_response_time_seconds = avg_response_time.total_seconds() if avg_response_time else 0

    # avg_rating = Feedback.objects.aggregate(models.Avg('rating'))['rating__avg'] or 0
    
    context = {
        'total_complaints': total_complaints,
        'new_complaints': new_complaints,
        'resolved_complaints': resolved_complaints,
        'pending_complaints': pending_complaints,
        'avg_response_time_seconds': avg_response_time_seconds
        # 'avg_rating': avg_rating,
    }


    return render(request, 'admin/admin_dashboard.html', context)

def interaction_management(request):
    #filter status, user, category
    filter_form=ChatFilterForm(request.GET or None)
    chats=Chat.objects.select_related('user').all()
       

    if filter_form.is_valid():
        if filter_form.cleaned_data.get('user'):
            chats=chats.filter(user=filter_form.cleaned_data['user'])
        if filter_form.cleaned_data.get('category'):
            chats=chats.filter(category=filter_form.cleaned_data['category'])
        if filter_form.cleaned_data.get('status'):
            chats=chats.filter(status=filter_form.cleaned_data['status'])

    # form=UpdateChatStatusForm()
    if request.method == 'POST':
        # form = UpdateChatStatusForm(request.POST)
        chat_id = request.POST.get('chat_id')
        chat = Chat.objects.get(pk=chat_id)
        if 'update_status' in request.POST:
            form = UpdateChatStatusForm(request.POST, instance=chat)
            if form.is_valid():
                updated_chat = form.save(commit=False)
                if updated_chat.status == 'resolved' and not updated_chat.resolved_at:
                    updated_chat.resolved_at = timezone.now()
                updated_chat.save()
                messages.success(request, "Status updated successfully.")
            else:
                messages.error(request, 'Error Updating status')
                return redirect('interaction_management')
        
        elif 'delete_chat' in request.POST:
            chat_id = request.POST.get('chat_id_delete')
            chat = get_object_or_404(Chat, pk=chat_id)
            chat.delete()
            messages.success(request, "Chat deleted successfully.")
            return redirect('interaction_management')  # Redirect to avoid re-posting form data
        
    # chats=Chat.objects.all()
    chat_forms = [UpdateChatStatusForm(instance=chat) for chat in chats]

    # Use zip to combine chats and forms
    chats_and_forms = zip(chats, chat_forms)

    context = {
        'chats_and_forms': chats_and_forms,
        'filter_form':filter_form
    }
    return render(request, 'admin/interactions.html', context)
 

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

def logout(request):
    auth.logout(request)
    return redirect('/')

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
    return render(request, 'admin/overallsentiments.html', context)

def user_management(request):
    profiles=UserProfile.objects.all()
    return render(request, 'admin/user_management.html', {'profiles':profiles})

def user_detail(request, user_id):
    profile=get_object_or_404(UserProfile, user__id=user_id)
    chats=Chat.objects.filter(user_id=user_id).order_by('-created_at')
    #delete users
    if request.method=='POST':
        user=get_object_or_404(User, pk=user_id)
        user.delete()
        messages.success(request, "User deleted Successfully")
        return redirect('user_management')
    else:
        messages.error(request, "Invalid request")
        
    
    return render(request, 'admin/user_detail.html', {'profile':profile, 'chats':chats})


#load model and vectorizer
# model=joblib.load('sentiment_model.pkl')
# vectorizer=joblib.load('tfidf_vectorizer.pkl')

# def classify_message(request):
#     message=request.GET.get('message', '')
#     vectorized_message=vectorizer.transform([message])
#     prediction=model.predict(vectorized_message)
#     sentiment="Positive" if prediction[0] else "Negative"

#     return JsonResponse({'message':message, 'sentiment':sentiment})


