from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from .models import  *
from apps.subscriptions  .models import *
from apps.accounts.models import *
from apps.newsletters.models import *
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count
from django.utils.timezone import now
from django.db.models import Sum, IntegerField, Value
from django.db.models.functions import Cast
from django.db.models.functions import TruncMonth
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic.edit import CreateView
from .forms import *  # Import du formulaire
from apps.accounts.models import *
from django.views.generic.edit import UpdateView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.views.generic import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView
import csv
from io import TextIOWrapper
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import SubscriptionPlanForm
from apps.subscriptions.models import SubscriptionPlan
from apps.subscriptions.models import Payment
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import Group, Permission
from django.views.generic import DetailView
from django.shortcuts import render
from django.http import HttpResponse
import csv
import pdfkit  # Pour générer des rapports PDF
from django.contrib.sites.models import Site
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages


def is_admin(user):
    return user.is_admin

@user_passes_test(is_admin)
def dashboard(request):
    print('hi')
    return render(request, 'admin/dashboard.html')

@user_passes_test(is_admin)
def manage_users(request):
    # Logic for managing users
    return render(request, 'admin/manage_users.html')

@user_passes_test(is_admin)
def manage_credits(request):
    # Logic for managing credits
    return render(request, 'admin/manage_credits.html')
 
User = get_user_model()
 
class AdminDashboardView(UserPassesTestMixin, TemplateView):
    template_name = 'admin/dashboard.html'
    # This method ensures only admins or staff members can access this view
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    # This method will gather the statistics for the dashboard
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Total statistics
        context['total_users'] = User.objects.count()
        context['total_news'] = News.objects.count()
        context['total_newsletters'] = Newsletter.objects.count()
        context['total_credits'] = UserCredit.objects.aggregate(total=Sum('credits'))['total'] or 0
        context['total_subscriptions'] = UserSubscription.objects.filter(active=True).count()
        context['total_payments'] = Payment.objects.filter(paid=True).count()
        context['total_revenue'] = Payment.objects.filter(paid=True).aggregate(total=Sum('amount'))['total'] or 0
        # Monthly statistics
        current_month = now().month
        current_year = now().year
        context['monthly_revenue'] = Payment.objects.filter(
            paid=True, created_at__year=current_year, created_at__month=current_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        # User-specific statistics
        context['top_users_by_credits'] = UserCredit.objects.order_by('-credits')[:5]  # Top 5 users with most credits
        context['users_with_active_subscriptions'] = UserSubscription.objects.filter(active=True).values('user__username').annotate(total_subscriptions=Count('id'))        
        # News and Newsletter usage
        context['news_by_type'] = News.objects.values('news_type').annotate(count=Count('id')).order_by('-count')  # News categorized by type
        context['popular_news_in_newsletters'] = Newsletter.objects.values('news__news_type').annotate(count=Count('news__id')).order_by('-count')  # Most used news in newsletters
        # Impact statistics with Cast to IntegerField
        context['news_by_impact'] = News.objects.aggregate(
            impact_real_estate=Sum(Cast('impact_real_estate', IntegerField())),
            impact_technology=Sum(Cast('impact_technology', IntegerField())),
            impact_finance=Sum(Cast('impact_finance', IntegerField())),
            impact_construction=Sum(Cast('impact_construction', IntegerField())),
            impact_retail=Sum(Cast('impact_retail', IntegerField())),
            impact_transport_logistics=Sum(Cast('impact_transport_logistics', IntegerField())),
        )
        # Credits usage
        context['credits_used_this_month'] = UserCredit.objects.filter(
            user__newsletter__created_at__month=current_month
        ).aggregate(total=Sum('credits'))['total'] or 0
        # Active payments and subscriptions
        context['active_subscriptions'] = UserSubscription.objects.filter(active=True).count()
        context['pending_payments'] = Payment.objects.filter(paid=False).count()
        context['subscriptions_by_plan'] = UserSubscription.objects.filter(active=True).values('plan__name', 'plan__plan_type').annotate(count=Count('id')).order_by('-count')
        context['revenue_by_month'] = Payment.objects.filter(paid=True).annotate(month=TruncMonth('created_at')).values('month').annotate(total_revenue=Sum('amount')).order_by('month')
        context['news_by_type'] = News.objects.values('news_type').annotate(count=Count('id')).order_by('-count')
        context['newsletters_by_month'] = Newsletter.objects.annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')
        # Top utilisateurs par nombre de newsletters créées
        context['top_users_by_newsletters'] = User.objects.annotate(
            total_newsletters=Count('newsletter')
        ).order_by('-total_newsletters')[:5]  # Les 5 utilisateurs les plus actifs

        # Engagement des utilisateurs (nombre de connexions ou d'interactions)
        context['user_engagement'] = User.objects.annotate(
            total_logins=Count('last_login')
        ).order_by('-total_logins')[:5]  # Top 5 utilisateurs les plus engagés
        # Répartition géographique des utilisateurs
        context['user_distribution_by_country'] = User.objects.values('country').annotate(total=Count('id')).order_by('-total')
        # Paiements par méthode de paiement
        context['payments_by_method'] = Payment.objects.values('payment_method').annotate(total=Count('id')).order_by('-total')
        # Revenus par utilisateur
        context['revenue_by_user'] = Payment.objects.filter(paid=True).values('user_subscription__user__username').annotate(
            total_revenue=Sum('amount')
        ).order_by('-total_revenue')[:5]  # Top 5 utilisateurs générant le plus de revenus
        # Churn des abonnements
        context['churn_rate'] = UserSubscription.objects.filter(active=False).count()
        context['total_subscriptions'] = UserSubscription.objects.filter(active=True).count()
        if context['total_subscriptions'] > 0:
            context['churn_percentage'] = (context['churn_rate'] / (context['churn_rate'] + context['total_subscriptions'])) * 100
        else:
            context['churn_percentage'] = 0
        # Utilisation des crédits par utilisateur
        context['credits_by_user'] = UserCredit.objects.values('user__username').annotate(
            total_credits_used=Sum('total_newsletters_created')
        ).order_by('-total_credits_used')[:5]  # Top 5 utilisateurs par crédits utilisés
        # Evolution des abonnés (nouveaux abonnements et désabonnements)
        context['subscriptions_by_month'] = UserSubscription.objects.annotate(month=TruncMonth('start_date')).values('month').annotate(
            total=Count('id')
        ).order_by('month')
        context['subscriptions_by_plan'] = UserSubscription.objects.filter(active=True).values('plan__name', 'plan__plan_type').annotate(count=Count('id')).order_by('-count')
        online_threshold = timezone.now() - timedelta(minutes=5)  # Considérer un utilisateur en ligne s'il a été actif dans les 5 dernières minutes
        users = User.objects.all()
        sessions = Session.objects.filter(expire_date__gte=timezone.now())  # Obtenir les sessions actives
        user_data = []
        for user in users:
            last_login = user.last_login         
            # Vérifier si l'utilisateur a une session active
            is_online = False
            for session in sessions:
                session_data = session.get_decoded()
                if str(user.id) == session_data.get('_auth_user_id'):
                    is_online = True
                    break      
            # Si une session est active ou si le dernier login est récent, l'utilisateur est en ligne
            if is_online:
                status = 'En ligne'
            else:
                status = 'Déconnecté' if last_login and last_login < online_threshold else 'En ligne'
            date_last_login = last_login.strftime('%Y-%m-%d') if last_login else 'N/A'
            time_last_login = last_login.strftime('%H:%M:%S') if last_login else 'N/A'
            user_data.append({
                'username': user.username,
                'email': user.email,
                'status': status,
                'date_last_login': date_last_login,
                'time_last_login': time_last_login,
            })
        context['user_data'] = user_data
        return context

def site_list_view(request):
    sites = Site.objects.all()
    return render(request, 'admin/sites_list.html', {'sites': sites})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.sites.models import Site

def site_edit_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if request.method == 'POST':
        site.domain = request.POST.get('domain')
        site.name = request.POST.get('name')
        site.save()
        return redirect('site_list')
    return render(request, 'admin/edit_site.html', {'site': site})



from allauth.socialaccount.models import SocialApp

def social_app_list_view(request):
    social_apps = SocialApp.objects.all()
    return render(request, 'admin/social_app_list.html', {'social_apps': social_apps})

def social_app_edit_view(request, app_id):
    app = get_object_or_404(SocialApp, id=app_id)
    if request.method == 'POST':
        app.name = request.POST.get('name')
        app.client_id = request.POST.get('client_id')
        app.secret = request.POST.get('secret')
        app.save()
        return redirect('social_app_list')
    return render(request, 'admin/edit_social_app.html', {'app': app})


from allauth.socialaccount.models import SocialToken

def social_token_list_view(request):
    social_tokens = SocialToken.objects.all()
    return render(request, 'admin/social_token_list.html', {'social_tokens': social_tokens})

def social_token_edit_view(request, token_id):
    token = get_object_or_404(SocialToken, id=token_id)
    if request.method == 'POST':
        token.token = request.POST.get('token')
        token.save()
        return redirect('social_token_list')
    return render(request, 'admin/edit_social_token.html', {'token': token})




from allauth.socialaccount.models import SocialAccount
from django.shortcuts import render, get_object_or_404, redirect

def social_account_list_view(request):
    social_accounts = SocialAccount.objects.all()
    return render(request, 'admin/social_account_list.html', {'social_accounts': social_accounts})

def social_account_edit_view(request, account_id):
    account = get_object_or_404(SocialAccount, id=account_id)
    if request.method == 'POST':
        account.provider = request.POST.get('provider')
        account.uid = request.POST.get('uid')
        account.save()
        return redirect('social_account_list')
    return render(request, 'admin/edit_social_account.html', {'account': account})




















 




from django.contrib.auth.models import Group, Permission
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth import get_user_model

User = get_user_model()

def is_admin(user):
    return user.is_staff or user.is_superuser

# Vue pour lister les groupes d'utilisateurs
@user_passes_test(is_admin)
def manage_groups(request):
    groups = Group.objects.all()
    return render(request, 'admin/manage_groups.html', {'groups': groups})

# Vue pour mettre à jour un groupe (ajouter/supprimer des utilisateurs)
@user_passes_test(is_admin)
def update_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    users = User.objects.all()

    if request.method == 'POST':
        # Ajouter des utilisateurs au groupe
        selected_users = request.POST.getlist('users')
        group.user_set.clear()  # Effacer tous les utilisateurs actuels du groupe
        for user_id in selected_users:
            user = get_object_or_404(User, id=user_id)
            group.user_set.add(user)

        return redirect('custom_admin:manage_groups')

    context = {
        'group': group,
        'users': users,
    }
    return render(request, 'admin/update_group.html', context)

# Vue pour gérer les permissions
@user_passes_test(is_admin)
def manage_permissions(request):
    groups = Group.objects.all()
    permissions = Permission.objects.all()

    if request.method == 'POST':
        # Assigner des permissions à un groupe
        group_id = request.POST.get('group')
        selected_permissions = request.POST.getlist('permissions')
        group = get_object_or_404(Group, id=group_id)
        group.permissions.clear()  # Supprimer toutes les permissions actuelles du groupe
        for perm_id in selected_permissions:
            permission = get_object_or_404(Permission, id=perm_id)
            group.permissions.add(permission)

        return redirect('custom_admin:manage_permissions')

    context = {
        'groups': groups,
        'permissions': permissions,
    }
    return render(request, 'admin/manage_permissions.html', context)






from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount

def social_account_create_view(request):
    if request.method == 'POST':
        user = User.objects.get(id=request.POST.get('user_id'))
        provider = request.POST.get('provider')
        uid = request.POST.get('uid')
        SocialAccount.objects.create(user=user, provider=provider, uid=uid)
        return redirect('social_account_list')
    users = User.objects.all()
    return render(request, 'admin/create_social_account.html', {'users': users})



from allauth.socialaccount.models import SocialToken, SocialAccount

def social_token_create_view(request):
    if request.method == 'POST':
        account = SocialAccount.objects.get(id=request.POST.get('account_id'))
        token = request.POST.get('token')
        SocialToken.objects.create(account=account, token=token)
        return redirect('social_token_list')
    social_accounts = SocialAccount.objects.all()
    return render(request, 'admin/create_social_token.html', {'social_accounts': social_accounts})


from allauth.socialaccount.models import SocialApp

def social_app_create_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        client_id = request.POST.get('client_id')
        secret = request.POST.get('secret')
        SocialApp.objects.create(name=name, client_id=client_id, secret=secret)
        return redirect('social_app_list')
    return render(request, 'admin/create_social_app.html')



from django.contrib.sites.models import Site
from django.shortcuts import render, redirect

def site_create_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        domain = request.POST.get('domain')
        Site.objects.create(name=name, domain=domain)
        return redirect('site_list')
    return render(request, 'admin/create_site.html')








 



































# Rapports d'activité des utilisateurs
class UserActivityReportView(UserPassesTestMixin, TemplateView):
    template_name = 'admin/user_activity_report.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_activities'] = User.objects.annotate(
            total_logins=Count('last_login'),
            total_newsletters=Count('newsletter'),
            total_credits_used=Sum('usercredit__total_newsletters_created')
        )
        return context


# Historique de facturation
class BillingHistoryView(UserPassesTestMixin, TemplateView):
    template_name = 'admin/billing_history.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['billing_records'] = Payment.objects.filter(paid=True).order_by('-created_at')
        return context


  



































User = get_user_model()

class UserListView(UserPassesTestMixin, ListView):
    model = User
    template_name = 'admin/user_list.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class UserCreateView(UserPassesTestMixin, CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm  # Utilisation du formulaire qui inclut les champs password1 et password2
    template_name = 'admin/user_form.html'
    success_url = reverse_lazy('custom_admin:user_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class UserUpdateView(UserPassesTestMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserUpdateForm
    template_name = 'admin/user_form.html'
    success_url = reverse_lazy('custom_admin:user_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
 
class UserDeleteView(UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'admin/user_confirm_delete.html'
    success_url = reverse_lazy('custom_admin:user_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
 
class CreditListView(UserPassesTestMixin, ListView):
    model = UserCredit
    template_name = 'admin/credit_list.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class CreditUpdateView(UserPassesTestMixin, UpdateView):
    model = UserCredit
    fields = ['credits']
    template_name = 'admin/credit_form.html'
    success_url = reverse_lazy('custom_admin:credit_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object.user  # L'utilisateur associé à ces crédits
        
        # Récupération des informations supplémentaires
        user_plan = UserSubscription.objects.filter(user=user, active=True).first()
        total_newsletters = Newsletter.objects.filter(author=user).count()
        
        # Ajout des informations au contexte
        context['user_details'] = user
        context['user_plan'] = user_plan
        context['total_newsletters'] = total_newsletters
        
        return context
 
class NewsListView(UserPassesTestMixin, ListView):
    model = News
    template_name = 'admin/news_list.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        # Gérer l'importation du fichier CSV
        if 'csv_file' in request.FILES:
            csv_file = request.FILES['csv_file']
            try:
                data = TextIOWrapper(csv_file.file, encoding='utf-8')
                reader = csv.DictReader(data)
                for row in reader:
                    News.objects.create(
                        title=row.get('title', ''),
                        summary=row.get('summary', ''),
                        date=row.get('date', ''),
                        type=row.get('type', ''),
                        localisation=row.get('localisation', ''),
                        postal_code=row.get('postal_code', ''),
                        news_type=row.get('news_type', ''),
                        impact_real_estate=row.get('impact_real_estate', 0),
                        impact_technology=row.get('impact_technology', 0),
                        impact_finance=row.get('impact_finance', 0),
                        impact_construction=row.get('impact_construction', 0),
                        impact_retail=row.get('impact_retail', 0),
                        impact_transport_logistics=row.get('impact_transport_logistics', 0),
                        impact_education=row.get('impact_education', 0),
                    )
                messages.success(request, 'Importation réussie!')
            except Exception as e:
                messages.error(request, f"Erreur lors de l'importation: {str(e)}")
        
        return redirect('custom_admin:news_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class NewsCreateView(UserPassesTestMixin, CreateView):
    model = News
    fields = ['title', 'summary', 'date', 'type', 'localisation', 'postal_code', 'news_type', 
              'impact_real_estate', 'impact_technology', 'impact_finance', 'impact_construction', 
              'impact_retail', 'impact_transport_logistics', 'impact_education']
    template_name = 'admin/news_form.html'
    success_url = reverse_lazy('custom_admin:news_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class NewsUpdateView(UserPassesTestMixin, UpdateView):
    model = News
    fields = ['title', 'summary', 'date', 'type', 'localisation', 'postal_code', 'news_type', 
              'impact_real_estate', 'impact_technology', 'impact_finance', 'impact_construction', 
              'impact_retail', 'impact_transport_logistics', 'impact_education']
    template_name = 'admin/news_form.html'
    success_url = reverse_lazy('custom_admin:news_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class NewsDeleteView(UserPassesTestMixin, DeleteView):
    model = News
    template_name = 'admin/news_confirm_delete.html'
    success_url = reverse_lazy('custom_admin:news_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
 
class NewsletterListView(UserPassesTestMixin, ListView):
    model = Newsletter
    template_name = 'admin/newsletter_list.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class NewsletterCreateView(UserPassesTestMixin, CreateView):
    model = Newsletter
    fields = ['title', 'content', 'news']
    template_name = 'admin/newsletter_form.html'
    success_url = reverse_lazy('custom_admin:newsletter_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class NewsletterUpdateView(UserPassesTestMixin, UpdateView):
    model = Newsletter
    fields = ['title', 'content', 'news']
    template_name = 'admin/newsletter_form.html'
    success_url = reverse_lazy('custom_admin:newsletter_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class NewsletterDeleteView(UserPassesTestMixin, DeleteView):
    model = Newsletter
    template_name = 'admin/newsletter_confirm_delete.html'
    success_url = reverse_lazy('custom_admin:newsletter_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
     
class SubscriptionListView(UserPassesTestMixin, ListView):
    model = SubscriptionPlan
    template_name = 'admin/subscription_list.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class SubscriptionUpdateView(UserPassesTestMixin, UpdateView):
    model = SubscriptionPlan
    fields = ['name', 'stripe_plan_id', 'plan_type', 'price', 'description', 'credit']
    template_name = 'admin/subscription_form.html'
    success_url = reverse_lazy('custom_admin:subscription_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
  
User = get_user_model()

class AddCreditToUserView(UserPassesTestMixin, View):
    template_name = 'admin/add_credit.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        # Sélectionner les utilisateurs sans crédits
        users_without_credits = User.objects.filter(usercredit__isnull=True)
        return render(request, self.template_name, {'users_without_credits': users_without_credits})

    def post(self, request, *args, **kwargs):
        user_id = request.POST.get('user_id')
        credits = request.POST.get('credits')
        user = get_object_or_404(User, id=user_id)
        
        # Créer un crédit pour cet utilisateur
        UserCredit.objects.create(user=user, credits=credits)
        
        return redirect('custom_admin:credit_list')
 
class SubscriptionCreateView(UserPassesTestMixin, CreateView):
    model = SubscriptionPlan
    form_class = SubscriptionPlanForm
    template_name = 'admin/subscription_form.html'
    success_url = reverse_lazy('custom_admin:subscription_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
     
class PaymentListView(UserPassesTestMixin, ListView):
    model = Payment
    template_name = 'admin/paiement_list.html'
    context_object_name = 'payments'
    paginate_by = 10  # Example of pagination

    def get_queryset(self):
        return Payment.objects.all().order_by('-created_at')  # Order by created_at field

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
 