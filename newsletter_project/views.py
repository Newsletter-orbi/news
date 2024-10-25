from django.views import View
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
import os
from django.conf import settings
from django.templatetags.static import static
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMessage
 
class HomeView(View):
    template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
 
class faqView(View):
    template_name = 'faq.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

class contactView(View):

    template_name = 'contact.html'

    def get(self, request, *args, **kwargs):
        # Get the path of the logo
        logo_path = os.path.join(settings.STATIC_ROOT, 'assets/img/logo1.png')

        # Check if the logo exists
        logo_exists = os.path.exists(logo_path)
        print(  logo_path  )

        print(  logo_exists  )
 
        return render(request, self.template_name, {
            'logo_exists': logo_exists,
        })

    def post(self, request, *args, **kwargs):
        # Récupérer les données du formulaire
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
  
        # Optionnel: Validation des champs
        if not name or not email or not subject or not message:
            messages.error(request, 'All fields are required.')
            return render(request, self.template_name)

        # Render the email HTML template with context
        email_content = render_to_string('email/contact_email.html', {
            'name': name,
            'email': email,
            'subject': subject,
            'message': message,
        })

        try:
            # Envoi de l'e-mail avec le template HTML


            email_message = EmailMessage(
                subject=subject,
                body=email_content,
                from_email=settings.SENDER_EMAIL,  # L'email de l'expéditeur
                to=[   settings.SENDER_EMAIL   ],  # L'email du destinataire
            )
 
            email_message.content_subtype = 'html'  # This is important to send HTML email
            email_message.send()

            print('Email envoyé avec succès')
     
            messages.success(request, 'Your message has been sent successfully!')
        except Exception as e:

            print(f'Erreur lors de l\'envoi de l\'email: {e}')
            messages.error(request, 'Failed to send your message. Please try again later.')

        return redirect('contact')  # Redirige vers la page de contact après soumission