from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
 
class News(models.Model):
    title = models.CharField(max_length=255)
    summary = models.TextField()
    date = models.DateField()
    type = models.CharField(max_length=50, choices=[
        ('positive', 'Positive'),
        ('negative', 'Negative')
    ])

    localisation = models.CharField(max_length=255)  
    postal_code = models.CharField(max_length=10)  
    news_type = models.CharField(max_length=50, choices=[
        ('price_trends', 'Tendances des prix'),
        ('mortgages', 'Crédits immobiliers'),
        ('sales_purchases', 'Ventes et achats'),
        ('housing_availability', 'Disponibilité du logement'),
        ('interest_rate_impact', 'Impact des taux d’intérêt'),
        ('innovation_technology', 'Innovation et technologie'),
        ('demographic_trends', 'Tendances démographiques')
    ]) 
    
    impact_real_estate = models.BooleanField(default=False)  # Impact sur l'immobilier
    impact_technology = models.BooleanField(default=False)  # Impact sur la technologie
    impact_finance = models.BooleanField(default=False)  # Impact sur la finance
    impact_construction = models.BooleanField(default=False)  # Impact sur la construction
    impact_retail = models.BooleanField(default=False)  # Impact sur le commerce de détail
    impact_transport_logistics = models.BooleanField(default=False)  # Impact sur le transport et la logistique
    impact_education = models.BooleanField(default=False)  # Impact sur l'éducation

    def __str__(self):
        return self.title
 
class Newsletter(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    news = models.ManyToManyField(News)
    
    # Ajout de la valeur par défaut pour le champ lien_img
    lien_img = models.URLField(max_length=500, blank=True, null=True, default='https://images.pexels.com/photos/2695680/pexels-photo-2695680.jpeg')

    def __str__(self):
        return self.title
 
class UserCredit(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    credits = models.IntegerField(default=10)   
    total_newsletters_created = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} - {self.credits} credits" 