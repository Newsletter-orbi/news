from django.views.generic import ListView, CreateView, DetailView
from .models import Newsletter, News, UserCredit
from .forms import NewsletterForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView , CreateView, UpdateView , DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views import View
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic import View
from apps.newsletters.models import *
from apps.newsletters.forms import *
from groq import Groq
import json
from django.db import IntegrityError
import cloudscraper
from django.http import Http404
import os
import itertools
from dotenv import load_dotenv
import time
from django.urls import reverse  
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'environment.env')

class NewsletterListView(LoginRequiredMixin, ListView):
    model = Newsletter
    template_name = 'newsletters/list_newsletters.html'
    context_object_name = 'newsletters'
    ordering = ['-created_at']

class NewsListView(LoginRequiredMixin, ListView):
    model = News
    template_name = 'newsletters/list_news.html'
    context_object_name = 'news_list'
    ordering = ['-date']

class NewsletterDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            newsletter = Newsletter.objects.get(pk=pk)
            if request.user == newsletter.author:  # Assurez-vous que seul l'auteur peut supprimer
                newsletter.delete()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'error': 'Vous n\'êtes pas autorisé à supprimer cette newsletter.'}, status=403)
        except Newsletter.DoesNotExist:
            return JsonResponse({'error': 'Newsletter introuvable.'}, status=404)
   
class NewsletterEditView(LoginRequiredMixin, UpdateView):
    model = Newsletter
    form_class = NewsletterForm  # Utilisation du formulaire personnalisé
    template_name = 'newsletters/newsletter_edit.html'
    success_url = reverse_lazy('accounts:dashboard_redirect')

    def get_object(self, queryset=None):
        newsletter = super().get_object(queryset)
        # Assurez-vous que seul l'auteur puisse éditer la newsletter
        if newsletter.author != self.request.user:
            raise PermissionDenied("Vous n'êtes pas autorisé à modifier cette newsletter.")
        return newsletter

    def form_valid(self, form):
        newsletter = form.save(commit=False)
        # Remplacer les sauts de ligne par des balises <br> avant de sauvegarder
        newsletter.content = newsletter.content.replace("\n", "<br>")
        newsletter.save()
        messages.success(self.request, "La newsletter a été mise à jour avec succès.")
        return super().form_valid(form)

    def handle_no_permission(self):
        messages.error(self.request, "Vous n'êtes pas autorisé à modifier cette newsletter.")
        return redirect('Newsletter:list_newsletters')

 ###

if os.path.exists(dotenv_path):
        print(f"Le fichier .env est trouvé : {dotenv_path}")
else:
        print(f"Le fichier .env n'est pas trouvé : {dotenv_path}")

    # Charger les variables d'environnement
load_dotenv(dotenv_path)
 
API_KEYS_Groq = [
     os.getenv('GROQ_API_KEY_1'),
     os.getenv('GROQ_API_KEY_2'),
     os.getenv('GROQ_API_KEY_3'),
     os.getenv('GROQ_API_KEY_4'),
     os.getenv('GROQ_API_KEY_5'),
     os.getenv('GROQ_API_KEY_6'),
     os.getenv('GROQ_API_KEY_7'),
     os.getenv('GROQ_API_KEY_8'),
]

if not API_KEYS_Groq:
    raise ValueError("Aucune clé API Groq trouvée.")

api_key_iterator = itertools.cycle(API_KEYS_Groq)

def get_next_api_key():
    """Retourner la prochaine clé API disponible."""
    return next(api_key_iterator)
 
def call_groq_api(client, model, messages):
 
    """Appeler l'API Groq avec gestion de la limite d'API."""
    try:
 
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=1.17,
            max_tokens=8192,
            top_p=1,
            stream=False,
            response_format={"type": "json_object"},
            stop=None,

        )
 
        return response.choices[0].message.content
    except Exception as e:
        if hasattr(e, 'status_code') and e.status_code == 429:  # Code 429 pour "Trop de requêtes"
            print("Limite de requêtes atteinte. Passage à la clé suivante...")
            return None
        else:
            raise e
 
class PexelsAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://api.pexels.com/v1/'
    def search_images(self, query, per_page=10, orientation=None, size=None, color=None):
        scraper = cloudscraper.create_scraper()
        headers = {'Authorization': self.api_key}
        params  = {'query': query, 'per_page': per_page}
        # Ajouter les filtres si disponibles
        if orientation:
            params['orientation'] = orientation
        if size:
            params['size'] = size
        if color:
            params['color'] = color
        # Effectuer la requête en utilisant cloudscraper
        response = scraper.get(self.base_url + 'search', headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            return [photo['src']['original'] for photo in data['photos']]
        else:
            print(f"Failed to fetch the images, sorry :( - {response.status_code}")
            return []

def manage_groq_requests(messages):
 
    """Gérer les requêtes Groq en changeant de clé API si nécessaire."""
    for _ in range(len(API_KEYS_Groq)):  # Essayer chaque clé API une fois
        api_key = get_next_api_key()
        print(f"Utilisation de la clé API : {api_key}")
        client = Groq(api_key=api_key)
        
 
        # Appel de l'API Groq avec la clé courante
        result = call_groq_api(client, os.getenv('LLM_Text')  , messages)
 
        if result:  # Si la requête a fonctionné
            return result
        
        else:
            # Attendre un peu avant de passer à la clé suivante pour éviter de spammer
            time.sleep(.1)
    
    # Si toutes les API ont échoué
    print("Toutes les API ont atteint leur limite ou échoué.")
    return "Impossible de traiter la requête, veuillez réessayer plus tard."

def format_news_summaries(news_summaries):
                     
                    messages=[
                        {
                            "role": "system",
                            "content": """donner article en format json de structure suite :   

                                                {
                                                    "article": {
                                                        "titre": " ",
                                                        "introduction": " ",
                                                        "contents": [
                                                            {"paragraphe_1": ""},
                                                            {"paragraphe_2": ""},
                                                            {"paragraphe_3": ""}
                                                        ],
                                                        "conclusion": ""
                                                    }
                                                }
                                                    """ 
                        },
                        {
                            "role"   :     "user",
                             
                            "content":     """  
                                                    As a professional and skilled journalist, your objective is to create an advanced-level article in French focused on the real estate market, particularly recent developments. You will be provided with summarized news text regarding real estate in France. Your responsibility is to thoroughly analyze this text and prepare a detailed article presenting key facts and relevant details. The article should examine the impact of these developments on both the current and future landscape of the real estate market. If relevant, you may merge some summarized news coherently.

                                                    It is crucial that your article adheres to the following guidelines: an introduction, main body paragraphs, and a conclusion, with each main body paragraph containing a minimum of 6,000 words (tokens). The article should be written in French and include pertinent and recent statistics to support your analysis. Avoid using separate titles for paragraphs to maintain a cohesive flow. Ensure your writing style is analytical, targeting an audience well-versed in real estate and economic trends. Finally, craft a general title summarizing the content of the generated article to capture the reader's attention.

                                                    In the introduction, raise questions that will be addressed in the following paragraphs, avoiding any detailed information upfront. The conclusion should summarize the main points covered and reaffirm the importance of the real estate market's dynamics.

                                                    IMPORTANT: The quality of the article is paramount. In the content section, creatively and smoothly discuss all relevant news, linking related subjects together within the same frame in a sequential and cohesive manner.

                                                    Please adhere to the following structure:

                                                    Introduction:
                                                    {In one paragraph of 200 words, provide a general overview of the topic, emphasizing the significance of the key events. Ask 2 or 3 questions that will be addressed in the following paragraphs.}

                                                    Contents:
                                                    {Generate the article content in 3 different paragraphs, with each main body paragraph containing a minimum of 6,000 words (tokens). Discuss all relevant news in a smooth and sequential manner, connecting related subjects and linking them cohesively. Analyze overall market trends, economic and social factors, real estate prices, government policies, and provide both short-term and long-term projections, along with investment recommendations. }

                                                    Conclusion:
                                                    {Summarize the main points covered in the article, reaffirm the importance of the real estate market and its dynamics, and may include a call to action or suggestions for further research or monitoring of future developments in 200 words maximum.}

                        
                                                    The press article is as follows: """ +             news_summaries       
                        }
                    ]
                    
                    
             
                    return manage_groq_requests(messages)
 
def get_important_key_words(article):
    """Extraire les mots-clés importants d'un article en utilisant l'API Groq."""
    messages = [
        {
            "role": "system",
            "content": """donner la resultat  en format json de structure suite :
                        {
                            "important_key_words": [""]
                        }"""
        },
        {
            "role": "user",
            "content":  """ You will be provided with article of news real estate in France. Your responsibility is to thoroughly analyze this text and prepare a the top 3 important keywords  
                            Please adhere to the following structure:
 
                            important_key_words:
                            {a list of 3 top key words of the most relevant and recurring words or phrases in the article. These keywords summarize the key concepts discussed in the text, helping to quickly identify the main subject and facilitating search or content indexing. the list must be in english }
                             The press article is as follows: """ +  article 
        }
    ]

    # Appeler l'API via manage_groq_requests
    return manage_groq_requests(messages)
 
def verifier_structure(json_data):
    # Vérifier si la clé 'article' existe
    if "article" not in json_data:
        return False
    article = json_data["article"]
    # Vérifier les clés principales
    required_keys = ["titre", "introduction", "contents", "conclusion"]   #, "important_key_words"]
    for key in required_keys:
        if key not in article:
            return False
    # Vérifier si 'contents' est une liste et qu'elle contient des objets avec les bons paragraphes
    if not isinstance(article["contents"], list):
        return False
    for i, content in enumerate(article["contents"]):
        if not isinstance(content, dict) or not any(f"paragraphe_{i+1}" in content for i in range(3)):
            return False
    # Vérifier si 'important_key_words' est une liste et non vide
    # if not isinstance(article["important_key_words"], list) or not article["important_key_words"]:
    #     return False
    return True
    
class NewsletterDetailView(LoginRequiredMixin, DetailView):
    model = Newsletter
    template_name = 'newsletters/newsletter_detail.html'
    context_object_name = 'newsletter'

    def get_object(self, queryset=None):
        """
        Redéfinit la méthode pour vérifier si l'utilisateur connecté est bien l'auteur de la newsletter.
        Renvoie 404 si ce n'est pas le cas ou si l'ID est invalide.
        """
        # Utiliser get_object_or_404 pour gérer les cas où l'ID est invalide
        newsletter = get_object_or_404(Newsletter, pk=self.kwargs['pk'])

        # Vérifier si l'utilisateur connecté est bien l'auteur
        if newsletter.author != self.request.user:
            raise Http404("Vous n'avez pas accès à cette newsletter.")

        return newsletter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtenez l'objet Newsletter actuel
        newsletter = self.get_object()
        # Diviser le contenu de la newsletter en paragraphes
        context['paragraphs'] = newsletter.content.split('\n\n')
        # Ajouter l'image associée à la newsletter avec une valeur par défaut
        context['lien_img'] = newsletter.lien_img or 'default_image.png'

        # Sauvegarder l'URL précédente pour redirection après "Retour"
        previous_url = self.request.META.get('HTTP_REFERER')
        if previous_url:
            self.request.session['previous_url'] = previous_url
        else:
            # Si HTTP_REFERER n'est pas disponible, fallback à la page de création
            self.request.session['previous_url'] = reverse('Newsletter:newsletter_create')

        return context

    def handle_no_permission(self):
        """
        Redirige vers la page 404 si l'utilisateur n'a pas la permission.
        """
        raise Http404("Vous n'avez pas la permission d'accéder à cette page.")
  
class NewsletterDetailView(LoginRequiredMixin, DetailView):
    model = Newsletter
    template_name = 'newsletters/newsletter_detail.html'
    context_object_name = 'newsletter'

    def get_object(self, queryset=None):
        """
        Redéfinit la méthode pour vérifier si l'utilisateur connecté est bien l'auteur de la newsletter.
        Renvoie 404 si ce n'est pas le cas.
        """
        newsletter = super().get_object(queryset)
        if newsletter.author != self.request.user:
            raise Http404("Vous n'avez pas accès à cette newsletter.")
        return newsletter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtenez l'objet Newsletter actuel
        newsletter = self.get_object()
        # Diviser le contenu de la newsletter en paragraphes
        context['paragraphs'] = newsletter.content.split('\n\n')
        # Ajouter l'image associée à la newsletter avec une valeur par défaut
        context['lien_img'] = newsletter.lien_img

        # Sauvegarder l'URL précédente pour redirection après "Retour"
        previous_url = self.request.META.get('HTTP_REFERER')
        if previous_url:
            self.request.session['previous_url'] = previous_url
        else:
            # Si HTTP_REFERER n'est pas disponible, forcer un fallback à la page de création
            self.request.session['previous_url'] = reverse('Newsletter:newsletter_create')

        return context

    def post(self, request, *args, **kwargs):
        """
        Permettre la redirection vers la page de création si l'utilisateur décide de revenir.
        """
        # Utiliser la session pour obtenir l'URL précédente ou rediriger vers la page de création
        previous_url = request.session.get('previous_url', reverse('Newsletter:newsletter_create'))
        return redirect(previous_url)
 
class NewsletterCreateView(LoginRequiredMixin, CreateView):
    model = Newsletter
    form_class = NewsletterForm
    template_name = 'newsletters/create_newsletter.html'
    success_url = reverse_lazy('accounts:dashboard_redirect')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']
        filtered_news = News.objects.all()
        if self.request.GET:
            form = self.form_class(self.request.GET)
            if form.is_valid():
                filtered_news = form.filter_news()
        context['filtered_news'] = filtered_news
        return context

    def form_valid(self, form):
        try:
            user_credit, created = UserCredit.objects.get_or_create(
                user=self.request.user, defaults={'credits': 0, 'total_newsletters_created': 0}
            )
        except IntegrityError:
            messages.error(self.request, "An error occurred while checking user credits.")
            return self.form_invalid(form)

        if user_credit.credits > 0:
            form.instance.author = self.request.user
            self.object = form.save(commit=False)
            selected_news_ids = self.request.POST.getlist('selected_news')
            selected_news = News.objects.filter(id__in=selected_news_ids)
            self.object.save()
            self.object.news.set(selected_news)

            format_exact = False
            json_data = None
            for i in range(1, 4):
                try:
                    formatted_content = format_news_summaries("\n".join([news.summary for news in selected_news]))
                    json_data = json.loads(formatted_content)
                except Exception as err:
                    print(f"Une autre erreur s'est produite : {err}")
                    continue
                if verifier_structure(json_data):
                    format_exact = True
                    break

            if not format_exact:
                messages.error(self.request, 'There was an error creating your newsletter. Please try again.')
                return self.form_invalid(form)

            titre = json_data['article'].get('titre', "Default Newsletter Title")
            introduction = json_data['article'].get('introduction', "")
            paragraphes = [p.get(f'paragraphe_{i + 1}', "") for i, p in enumerate(json_data['article']['contents'])]
            conclusion = json_data['article'].get('conclusion', "")
            article = f"{introduction}\n\n" + "\n\n".join(paragraphes) + f"\n\n{conclusion}"

            if str(6000) in article or len(article) < 400:
                messages.error(self.request, 'There was an error creating your newsletter. Please try again.')

            form.instance.title = titre
            form.instance.content = article

            keywords = ["Real estate france"]
            try:
                formatted_content = get_important_key_words(article)
                json_data = json.loads(formatted_content)
                keywords = json_data.get('important_key_words', [])
            except Exception as err:
                keywords = ["Real estate france"]

            if not keywords:
                keywords = ["Real estate france"]

            api_key = os.getenv('PEXELS_API_KEY')
            pexels_api = PexelsAPI(api_key)
            num_images = 20
            orientation = "landscape"
            size = "large"

            for keyword in keywords:
                image_urls = pexels_api.search_images(keyword, num_images, orientation, size)
                if image_urls:
                    for url in image_urls:
                        if not Newsletter.objects.filter(lien_img=url).exists():
                            form.instance.lien_img = url
                            break
                    break

            if not form.instance.lien_img:
                print("Aucune nouvelle image trouvée. Utilisation de l'image par défaut.")

            self.object.save()

            user_credit.credits -= 1
            user_credit.total_newsletters_created += 1
            user_credit.save()

            self.request.session['from_generated'] = True

            return redirect('Newsletter:newsletter_detail', pk=self.object.pk)
        else:
            messages.error(self.request, 'You do not have enough credits to create a newsletter.')
            return redirect('Newsletter:newsletter_create')

    def form_invalid(self, form):
        print(form.errors)
        messages.error(self.request, 'There was an error creating your newsletter. Please try again.')
        return self.render_to_response(self.get_context_data(form=form))
