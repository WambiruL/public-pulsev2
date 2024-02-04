from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Chat(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    message=models.TextField()
    category=models.CharField(max_length=100, default='general')
    response=models.TextField(default="I am sorry. I dont understand your question") 
    created_at=models.DateTimeField(auto_now_add=True)
    sentiment_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username}:{self.message}:{self.sentiment_score}:{self.created_at}:{self.category}'
    
    def sentiment_status(self):
        if self.sentiment_score is not None:
            if self.sentiment_score>0.1:
                return "Positive"
            elif self.sentiment_score<-0.1:
                return "Negative"
            else:
                return "Neutral"
        return "Unknown"
    
# class Sentiment(models.Model):
#     chat = models.ForeignKey(Chat, related_name='sentiments', on_delete=models.CASCADE, null=True)
#     score=models.FloatField()
#     created_at=models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f'{self.chat.user.username} at {self.created_at}:{self.score}'