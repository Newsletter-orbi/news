from django import forms
from .models import Newsletter, News

class NewsletterForm(forms.ModelForm):
    title = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    type = forms.ChoiceField(choices=[('', 'All'), ('positive', 'Positive'), ('negative', 'Negative')], required=False)

    news_type = forms.ChoiceField(choices=[('', 'All')] + list(News.news_type.field.choices), required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    localisation = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    postal_code = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    content = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control'}))

    impact_real_estate = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    impact_technology = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    impact_finance = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    impact_construction = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    impact_retail = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    impact_transport_logistics = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    impact_education = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    selected_news = forms.ModelMultipleChoiceField(queryset=News.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = Newsletter
        fields = ['title', 'content']  # Assurez-vous que 'content' est bien inclus
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control'}),  # Widget pour le champ 'content'
        }

    def filter_news(self):
        queryset = News.objects.all()
        
        try:
            # Filtrage par type de nouvelles (positive/negative)
            if self.cleaned_data.get (    'type'  ):
                queryset = queryset.filter(type=self.cleaned_data['type'])

            # Filtrage par titre
            if self.cleaned_data.get(   'title'):
                queryset = queryset.filter(title__icontains=self.cleaned_data['title'])

            # Filtrage par dates
            if self.cleaned_data.get(  'start_date'    )  :
                queryset = queryset.filter(date__gte=self.cleaned_data['start_date'])
            if self.cleaned_data.get(  'end_date'   ) :
                queryset = queryset.filter(date__lte=self.cleaned_data['end_date'])

            # Filtrage par type de nouvelles spécifiques
            if self.cleaned_data.get  (    'news_type'   )  :
                queryset = queryset.filter(news_type=self.cleaned_data['news_type'])

            # Filtrage par localisation
            if self.cleaned_data.get   (  'localisation' ) :
                queryset = queryset.filter(localisation__icontains=self.cleaned_data['localisation'])

            # Filtrage par code postal
            if self.cleaned_data.get(   'postal_code'   ) :
                queryset = queryset.filter(postal_code=self.cleaned_data['postal_code'])

            # Filtrage basé sur les impacts
            for impact_field in [
                'impact_real_estate', 'impact_technology', 'impact_finance',
                'impact_construction', 'impact_retail', 'impact_transport_logistics', 'impact_education'
            ]:
                if self.cleaned_data.get(impact_field):
                    queryset = queryset.filter(**{impact_field: True})

        except KeyError:
            # Gérer les erreurs de clé si les champs ne sont pas dans cleaned_data
            pass

        return queryset
 