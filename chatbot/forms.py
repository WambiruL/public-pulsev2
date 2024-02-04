from django import forms
from django.contrib.auth.models import User
from .models import Chat

class DashboardFilterForm(forms.Form):
 start_date=forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date'}))
 end_date=forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date'}))
 sentiment_category=forms.ChoiceField(required=False, choices=[('', 'All'), ('Positive', 'Positive'), ('Negative', 'Negative'), ('Neutral', 'Neutral')])
 user = forms.ModelChoiceField(required=False, queryset=User.objects.all(), empty_label="All Users")