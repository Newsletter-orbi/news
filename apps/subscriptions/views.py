from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from .models import SubscriptionPlan, UserSubscription, Payment
from apps.newsletters.models import *
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
import stripe
from apps.newsletters.models import UserCredit
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import io
 
stripe.api_key = settings.STRIPE_SECRET_KEY

def SubscriptionListView(request):
    plans = SubscriptionPlan.objects.all()
    return render(request, 'subscriptions/subscription_list.html', {'plans': plans})
 
@login_required
@require_POST
def CreateCheckoutSession(request, plan_id):
    try:
        print(f"Plan ID: {plan_id}")
        # Ensure that the plan exists
        try:
            plan = SubscriptionPlan.objects.get(stripe_plan_id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            messages.error(request, "Subscription plan not found.")
            return redirect('subscription_list')

        # Create or get the user's subscription plan
        user_subscription, created = UserSubscription.objects.get_or_create(
            user=request.user,
            plan=plan
        )
        # Log the Stripe price ID for debugging
        print(f"Creating checkout session with price ID: {plan.stripe_plan_id}")

        # Create a Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=request.user.email,
            line_items=[{
                'price': plan.stripe_plan_id,  # Stripe price ID
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.build_absolute_uri(reverse('payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('payment_failed')),
            client_reference_id=user_subscription.id,  # Optional reference for your internal tracking
        )
        print(f"Checkout session URL: {checkout_session.url}")
        # Redirect to the Stripe checkout page
        return redirect(checkout_session.url)
    except Exception as e:
        # Log the error for debugging
        print(f"Error: {str(e)}")
        # Display the error to the user
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('subscription_list')

def add_credits_after_payment(user, plan ,subscription_id ):
    # Ajouter des crédits selon le plan d'abonnement
    user_credits, created = UserCredit.objects.get_or_create(user=user)
    user_credits.credits += plan.credit  # Ajouter les crédits du plan au total actuel
    user_credits.save()
    # Mettre à jour l'abonnement
    user_subscription = UserSubscription.objects.get(user=user, plan=plan, active=True)
    user_subscription.start_date = datetime.now()
    if plan.plan_type == 'monthly':
        # Calculer la nouvelle end_date pour un abonnement mensuel
        user_subscription.end_date = user_subscription.start_date + timedelta(days=30)
    elif plan.plan_type == 'yearly':
        # Calculer la nouvelle end_date pour un abonnement annuel
        user_subscription.end_date = user_subscription.start_date + timedelta(days=365)
    user_subscription.stripe_subscription_id=subscription_id
    user_subscription.save()
 
def reset_credits(user):
    user_subscription = UserSubscription.objects.filter(user=user, active=True).first()
    if user_subscription:
        now = datetime.now()
        if user_subscription.end_date and user_subscription.end_date <= now:
            # Réinitialiser les crédits selon le plan
            if user_subscription.plan:
                user_credits = UserCredit.objects.get(user=user)
                user_credits.credits = user_subscription.plan.credit  # Assigner les crédits en fonction du plan
                user_credits.save()

            # Désactiver l'abonnement ou créer un nouveau pour le prochain cycle
            user_subscription.active = False
            user_subscription.save()

def reset_credits_if_subscription_ended():
    # Récupérer les abonnements actifs dont la date de fin est aujourd'hui ou avant
    today = datetime.now()
    expired_subscriptions = UserSubscription.objects.filter(end_date__lte=today, active=True)
    for subscription in expired_subscriptions:
        # Reset des crédits de l'utilisateur
        user_credit, created = UserCredit.objects.get_or_create(user=subscription.user)
        user_credit.credits = 0  # Réinitialiser à zéro
        user_credit.save()
        # Désactiver l'abonnement
        subscription.active = False
        subscription.save()
        # Optionnel: envoyer un email à l'utilisateur pour l'informer que son abonnement est terminé
        print(f"Crédits réinitialisés pour l'utilisateur: {subscription.user.username}")

@login_required
def PaymentSuccessView(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        messages.error(request, "Session ID is missing. Unable to retrieve payment details.")
        return redirect('subscription_list')

    try:
        # Retrieve the session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        subscription_id = session.subscription
        user_subscription = UserSubscription.objects.get(id=session.client_reference_id)

        # Initialize variables
        payment_intent = None
        payment_method = "Unknown"
        transaction_id = "Unknown"
        paid_at = datetime.utcfromtimestamp(session.created)

        # Check if the session has a payment intent (this may not exist for subscription-based sessions)
        if session.payment_intent:
            # Only retrieve payment intent if it exists
            payment_intent = stripe.PaymentIntent.retrieve(session.payment_intent)
            payment_method = payment_intent.payment_method_types[0] if payment_intent else "Unknown"
            transaction_id = payment_intent.id if payment_intent else "Unknown"

        # Create a payment record with available fields
        Payment.objects.create(
            user_subscription=user_subscription,
            amount=session.amount_total / 100,  # Stripe stores amounts in cents
            stripe_subscription_id=subscription_id,
            payment_method=payment_method,
            transaction_id=transaction_id,
            paid=True,
            paid_at=paid_at
        )

        # Activate the user's subscription
        user_subscription.active = True
        user_subscription.save()

        # Add credits to the user's account based on their subscription plan
        add_credits_after_payment(request.user, user_subscription.plan, subscription_id)

        # Prepare payment details for invoice generation
        payment_details = {
            'name_customer': user_subscription.user.get_full_name(),
            'email': user_subscription.user.email,
            'invoice_number': session_id,
            'date': paid_at,  # Formatted date
            'amount_paid': session.amount_total / 100,
            'payment_status': session.payment_status,
            'plan_name': user_subscription.plan.name,
            'plan_type': "Monthly" if user_subscription.plan.plan_type == 'monthly' else "Annual",
            'plan_description': user_subscription.plan.description
        }

        # Render the template with payment details and user_subscription
        return render(request, 'subscriptions/payment_success.html', {
            'payment_details': payment_details,
            'user_subscription': user_subscription
        })

    except stripe.error.StripeError as e:
        messages.error(request, f"An error occurred while processing payment: {str(e)}")
        return redirect('subscription_list')

    except UserSubscription.DoesNotExist:
        messages.error(request, "Subscription not found.")
        return redirect('subscription_list')

@login_required
def generate_invoice_pdf(request, subscription_id):
    try:
        # Log the subscription ID for debugging
        print(f"Generating invoice for subscription ID: {subscription_id}")

        # Retrieve the subscription from Stripe using the subscription_id
        subscription = stripe.Subscription.retrieve(subscription_id)
        if not subscription:
            raise ValueError("No subscription found for the provided subscription ID")

        # Get the UserSubscription from your database
        user_subscription = UserSubscription.objects.get(stripe_subscription_id=subscription_id)

        # Access the first item in the subscription's items
        subscription_item = subscription['items']['data'][0]
        plan = subscription_item['plan']
        amount = plan['amount'] / 100  # Amount in dollars (Stripe stores amounts in cents)

        # Prepare the invoice details
        payment_details = {
            'name_customer': user_subscription.user.get_full_name(),
            'email': user_subscription.user.email,
            'invoice_number': subscription.id,
            'date': datetime.utcfromtimestamp(subscription.created),
            'amount_paid': amount,  # Corrected amount
            'payment_status': 'Paid' if subscription.status == 'active' else 'Unpaid',
            'plan_name': plan['nickname'],  # Name or nickname of the plan
            'plan_type': "Monthly" if plan['interval'] == 'month' else "Annual",
            'plan_description': plan.get('description', 'No description available'),
        }

        # Render the HTML to PDF
        html = render_to_string('subscriptions/invoice_pdf_template.html', {'payment_details': payment_details})
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{payment_details["invoice_number"]}.pdf"'

        result = io.BytesIO()
        pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)

        if pdf.err:
            print(f"PDF generation error: {pdf.err}")
            return HttpResponse('An error occurred while generating the PDF.')

        response.write(result.getvalue())
        return response

    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        messages.error(request, f"An error occurred with Stripe: {e}")
        return redirect('subscription_list')

    except UserSubscription.DoesNotExist:
        print("Subscription not found in the database.")
        messages.error(request, "Subscription not found.")
        return redirect('subscription_list')

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        messages.error(request, f"An unexpected error occurred: {e}")
        return redirect('subscription_list')

@login_required
def PaymentFailedView(request):
    # Récupérer le message d'erreur de la session
    error_message = request.session.get('payment_error', 'An unknown error occurred during the payment process.')

    # Récupérer les détails du paiement échoué (si disponibles)
    payment_details = {
        'name_customer': request.session.get('name_customer', 'N/A'),
        'email': request.session.get('email', 'N/A'),
        'invoice_number': request.session.get('invoice_number', 'N/A'),
        'date': request.session.get('date', 'N/A'),
        'amount_paid': request.session.get('amount_paid', '0.00'),
        'payment_status': request.session.get('payment_status', 'Failed')
    }

    print(  payment_details['date']   )
 
    # Supprimer les détails du paiement et le message d'erreur après les avoir affichés
    if 'payment_error' in request.session:
        del request.session['payment_error']
    if 'name_customer' in request.session:
        del request.session['name_customer']
    if 'email' in request.session:
        del request.session['email']
    if 'invoice_number' in request.session:
        del request.session['invoice_number']
    if 'date' in request.session:
        del request.session['date']
    if 'amount_paid' in request.session:
        del request.session['amount_paid']
    if 'payment_status' in request.session:
        del request.session['payment_status']

    # Rendre le template avec le message d'erreur et les détails du paiement
    return render(request, 'subscriptions/payment_failed.html', {
        'error_message': error_message,
        'payment_details': payment_details
    })
 