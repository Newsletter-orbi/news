from django.contrib.auth.forms import UserCreationForm
from django import forms
from apps.accounts.models import CustomUser  # Assurez-vous d'importer votre modèle CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'profile_image', 'country', 'phone', 'password1', 'password2')



from django import forms
from django.contrib.auth.forms import UserChangeForm

from django import forms
from django.contrib.auth.forms import UserChangeForm
from apps.accounts.models import CustomUser

class CustomUserUpdateForm(UserChangeForm):
    password1 = forms.CharField(
        required=False,
        label="Nouveau mot de passe",
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        required=False,
        label="Confirmer le nouveau mot de passe",
        widget=forms.PasswordInput
    )
    is_superuser = forms.BooleanField(
        required=False,
        label="Super utilisateur (superuser)"
    )
    is_staff = forms.BooleanField(
        required=False,
        label="Administrateur (staff)"
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'profile_image', 'country', 'phone', 'is_superuser', 'is_staff']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password1 = self.cleaned_data.get('password1')

        # Si un mot de passe est renseigné, on l'applique à l'utilisateur
        if password1:
            user.set_password(password1)

        if commit:
            user.save()
        
        return user



from django import forms
from apps.subscriptions.models import SubscriptionPlan

class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = ['name', 'stripe_plan_id', 'plan_type', 'price', 'description', 'credit']

        widgets = {
            'plan_type': forms.Select(attrs={'class': 'form-control'}),
        }
