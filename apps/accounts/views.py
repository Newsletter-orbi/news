from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str 
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.views.generic import View
from django.views.generic.edit import CreateView, UpdateView
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ProfileUpdateForm
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.views.generic.edit import  FormView
from django.utils.crypto import get_random_string
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import  VerifyEmailForm
from django.conf import settings
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView
from django import forms
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.utils import timezone
from apps.newsletters.models import *
from apps.newsletters.forms import *
from collections import defaultdict
from apps.subscriptions.models import  UserSubscription
from django.views import View
import logging
from django.contrib.auth.mixins import UserPassesTestMixin
import os
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.sessions.models import Session
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.generic import UpdateView
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives

User = get_user_model()

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'environment.env')

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def dispatch(self, request, *args, **kwargs):
        # Si l'utilisateur est déjà connecté, le rediriger vers la page d'accueil
        if request.user.is_authenticated:
            return redirect(reverse_lazy('home'))  # Assurez-vous que 'home' est le nom de votre URL de page d'accueil
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        user = self.request.user
        logger = logging.getLogger(__name__)

        if user.is_authenticated:
            # Journaliser la connexion de l'utilisateur
            logger.info(f"Utilisateur {user.username} connecté avec succès.")

            # Stocker des informations importantes dans la session
            self.request.session['user_id'] = user.id
            self.request.session['is_staff'] = user.is_staff
            self.request.session['is_superuser'] = user.is_superuser

            # Redirection en fonction des autorisations de l'utilisateur
            if user.is_staff or user.is_superuser:
                logger.info(f"Admin {user.username} connecté.")
                return reverse_lazy('custom_admin:dashboard')  # Redirection admin
            else:
                logger.info(f"Utilisateur {user.username} connecté.")
                return reverse_lazy('accounts:dashboard')  # Redirection utilisateur normal
        else:
            logger.warning("Tentative de connexion échouée.")
            return reverse_lazy('accounts:login')  # Redirection vers la page de login si non authentifié

    # Optionnel : Déconnexion de l'utilisateur si la session expire ou si non valide
    def handle_no_permission(self):
        return redirect(reverse_lazy('accounts:login'))
   
class CustomDashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:  # Si l'utilisateur est un admin
            return HttpResponseRedirect(reverse_lazy('custom_admin:dashboard'))
        else:  # Utilisateur normal
            return HttpResponseRedirect(reverse_lazy('accounts:dashboard'))
 
class RegisterView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = True
        user.save()
        # Ajouter 10 crédits de bienvenue
        UserCredit.objects.create(user=user, credits=10)
        messages.success(self.request, 'Votre compte a été créé avec succès et vous avez reçu 10 crédits de bienvenue.')
        return super().form_valid(form)
 
class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))  # Modifier ici
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None
        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            login(request, user)
            messages.success(request, 'Your account has been confirmed.')
            return redirect('dashboard')
        else:
            messages.error(request, 'The confirmation link was invalid, possibly because it has already been used.')
            return redirect('home')

@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the newsletters for the logged-in user
        newsletters = Newsletter.objects.filter(author=self.request.user).order_by('-created_at')

        # Paginate the newsletters, 5 per page
        paginator = Paginator(newsletters, 10)  # 5 newsletters per page
        page = self.request.GET.get('page')
        try:
            page_number = int(page) if page else 1
            if page_number < 1:
                page_number = 1
            paginated_newsletters = paginator.page(page_number)
        except (PageNotAnInteger, ValueError):
            # If page is not an integer or invalid, deliver the first page
            paginated_newsletters = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver the last page
            paginated_newsletters = paginator.page(paginator.num_pages)
        context['newsletters'] = paginated_newsletters

        # User credits and stats
        try:
            user_credit = UserCredit.objects.get(user=self.request.user)
            context['credits'] = user_credit.credits
            context['total_newsletters_created'] = user_credit.total_newsletters_created
        except UserCredit.DoesNotExist:
            context['credits'] = 0
            context['total_newsletters_created'] = 0

        # Calculate newsletters created per day for the current month
        today = timezone.now().date()
        start_date = today.replace(day=1)
        dates = [start_date + timezone.timedelta(days=i) for i in range((today - start_date).days + 1)]
        counts = defaultdict(int)

        for newsletter in Newsletter.objects.filter(author=self.request.user, created_at__gte=start_date):
            counts[newsletter.created_at.date()] += 1

        chart_data = [counts[date] if date in counts else 0 for date in dates]
        context['chart_labels'] = [date.strftime('%Y-%m-%d') for date in dates]
        context['chart_data'] = chart_data

        # Calculate the most used news types in newsletters
        news_type_counts = defaultdict(int)
        for newsletter in Newsletter.objects.filter(author=self.request.user):
            for news in newsletter.news.all():
                news_type_counts[news.news_type] += 1

        news_type_labels = []
        for news_type in news_type_counts.keys():
            human_readable_label = dict(News._meta.get_field('news_type').choices)[news_type]
            news_type_labels.append(human_readable_label)

        context['news_type_labels'] = news_type_labels


        context['news_type_data'] = list(news_type_counts.values())

        # Calculate the most frequent impacts in newsletters
        impact_counts = defaultdict(int)
        for newsletter in Newsletter.objects.filter(author=self.request.user):
            for news in newsletter.news.all():
                if news.impact_real_estate:
                    impact_counts['Real Estate'] += 1
                if news.impact_technology:
                    impact_counts['Technology'] += 1
                if news.impact_finance:
                    impact_counts['Finance'] += 1
                if news.impact_construction:
                    impact_counts['Construction'] += 1
                if news.impact_retail:
                    impact_counts['Retail'] += 1
                if news.impact_transport_logistics:
                    impact_counts['Transport & Logistics'] += 1
                if news.impact_education:
                    impact_counts['Education'] += 1

        context['impact_labels'] = list(impact_counts.keys())
        context['impact_data'] = list(impact_counts.values())

        # Get the subscription details
        try:
            user_subscription = UserSubscription.objects.filter(user=self.request.user, active=True).order_by('-end_date').first()
            if user_subscription:
                context['subscription_plan'] = user_subscription.plan.name
                context['subscription_start_date'] = user_subscription.start_date
                context['subscription_end_date'] = user_subscription.end_date
            else:
                context['subscription_plan'] = "No active subscription"
                context['subscription_start_date'] = "N/A"
                context['subscription_end_date'] = "N/A"
        except UserSubscription.DoesNotExist:
            context['subscription_plan'] = "No active subscription"
            context['subscription_start_date'] = "N/A"
            context['subscription_end_date'] = "N/A"
        return context
  
class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:dashboard')
    
    def form_valid(self, form):
        # Validation de l'image
        profile_image = self.request.FILES.get('profile_image')
        if profile_image:
            if not profile_image.content_type.startswith('image/'):
                messages.error(self.request, 'Please upload a valid image file.')
                return self.form_invalid(form)
            elif profile_image.size > 5 * 1024 * 1024:  # Limite de 5 MB pour les fichiers
                messages.error(self.request, 'The image file is too large (limit is 5 MB).')
                return self.form_invalid(form)
            form.instance.profile_image = profile_image
        
        # Message de succès
        messages.success(self.request, 'Your profile was successfully updated!')
        return super().form_valid(form)

    def get_object(self):
        return self.request.user
    
    def form_invalid(self, form):
        # Gestion des erreurs et retour sur le formulaire
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
 
class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy( 'password_change_done')
 
class CustomPasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'
  
class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(max_length=254, required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label='New password', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'}))
    new_password2 = forms.CharField(label='New password confirmation', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'}))
    
class VerifyEmailView(FormView):
    template_name = 'accounts/verify_email.html'
    form_class = VerifyEmailForm
    success_url = reverse_lazy('login')
    def form_valid(self, form):
        code = form.cleaned_data.get('code')
        user = get_object_or_404(CustomUser, verification_code=code)
        if user:
            user.is_active = True
            user.verification_code = ''
            user.save()
            messages.success(self.request, 'Your email has been verified. You can now log in.')
        else:
            messages.error(self.request, 'Invalid verification code.')
        return super().form_valid(form)
 
def generate_unique_username(base_username):
    """Generates a unique username by appending a random string if necessary."""
    username = base_username
    counter = 1
    while CustomUser.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    return username

def verify_user(request):
    # Obtenir les clés et valeurs des paramètres
    email = request.GET.get('email')
    key = request.GET.get('key')

    # Gestion des paramètres non nommés
    unnamed_params = [param for param in request.GET if request.GET.get(param) == '']
    if not email and unnamed_params:
        email = unnamed_params[0]
    if not key and len(unnamed_params) >= 2:
        key = unnamed_params[1]
    
    # Clé valide dans l'environnement (dans la vraie application, utilisez os.getenv)
    env_key = os.getenv('connect_key')  # Remove the trailing comma
    print(  env_key )
    if key == env_key  : 
        try:
            # Récupérer l'utilisateur via l'email dans le modèle CustomUser
            user = CustomUser.objects.get(email=email)

            # Ajouter 10 crédits de bienvenue s'ils n'ont pas déjà été donnés
            if not UserCredit.objects.filter(user=user).exists():
                UserCredit.objects.create(user=user, credits=10)

            # Vérifier s'il a déjà une session active et le connecter
            sessions = Session.objects.filter(expire_date__gte=timezone.now())
            for session in sessions:
                session_data = session.get_decoded()
                if session_data.get('_auth_user_id') == str(user.id):
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    messages.success(request, 'Vous êtes connecté avec succès.')
                    return redirect('accounts:dashboard')

            # Si aucune session n'est trouvée, connecter l'utilisateur
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Vous êtes connecté avec succès.')
            return redirect('accounts:dashboard')

        except CustomUser.DoesNotExist:
            # Si l'utilisateur n'existe pas, générer un nom d'utilisateur unique et le créer
            username = generate_unique_username(email.split('@')[0])
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=get_random_string(length=8)  # Générer un mot de passe aléatoire
            )
            # Ajouter 10 crédits de bienvenue
            UserCredit.objects.create(user=user, credits=10)
            # Connecter l'utilisateur nouvellement créé
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Votre compte a été créé et vous êtes connecté avec succès.')
            return redirect('accounts:dashboard')
    else:
        messages.error(request, 'Invalid')
        return redirect('accounts:login')

class CustomPasswordResetView(View):
    template_name = 'accounts/password_reset_form.html'
 
    def get(self, request):
        form = PasswordResetForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        print("Formulaire de réinitialisation soumis")
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            print("Formulaire valide, envoi de l'e-mail...")
            email = form.cleaned_data['email']
            print(f"Email fourni : {email}")
            users = form.get_users(email)
            user = next(users, None)  # Utilisez 'next()' pour obtenir le premier utilisateur ou None

            if user:
                print(f"Utilisateur trouvé : {user}")
                # Générer un token et envoyer l'e-mail de réinitialisation
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                domain = get_current_site(request).domain
                reset_link = f"http://{domain}/reset/{uid}/{token}/"

                # Envoyer l'e-mail
                subject = "Réinitialisez votre mot de passe"
                message = render_to_string('accounts/password_reset_email.html', {
                    'user': user,
                    'uid': uid,
                    'token': token,
                    'protocol': 'https' if request.is_secure() else 'http',
                    'domain': domain,
                })

                sent_mail_count = send_mail(subject, message, settings.SENDER_EMAIL, [email] ,  html_message=message  )


                if sent_mail_count == 1:
                    print("E-mail envoyé avec succès")
                    messages.success(request, "L'e-mail de réinitialisation de mot de passe a été envoyé avec succès.")
                else:
                    print("Échec de l'envoi de l'e-mail")
                    messages.error(request, "L'envoi de l'e-mail a échoué. Veuillez réessayer plus tard.")

                # Redirection vers 'password_reset_done'
                return redirect(reverse_lazy('accounts:password_reset_done'))
            else:
                print("Aucun utilisateur trouvé pour cet email")
                messages.error(request, "Aucun utilisateur n'est associé à cet e-mail.")
        else:
            print("Formulaire invalide")

        return render(request, self.template_name, {'form': form})
    
class CustomPasswordResetConfirmView(View):
    template_name = 'accounts/password_reset_confirm.html'  # Assurez-vous que ce template existe

    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            form = SetPasswordForm(user)
            return render(request, self.template_name, {'form': form, 'validlink': True})
        else:
            return render(request, self.template_name, {'validlink': False})

    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                return redirect(reverse_lazy('password_reset_complete'))
        return render(request, self.template_name, {'form': form, 'validlink': True})
