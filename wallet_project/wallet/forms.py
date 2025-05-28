from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django.contrib.auth.models import User

'''
# Signup form using UserCreationForm
class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
'''

# Login form using AuthenticationForm
class LoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']

# Password reset form
class PasswordResetCustomForm(PasswordResetForm):
    email = forms.EmailField(required=True)
#########################################

# wallet/forms.py

from django import forms

class PaymentForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2)
    currency = forms.ChoiceField(choices=[('USD', 'USD'), ('EUR', 'EUR'), ('NGN', 'NGN')])
    # You can add more fields as needed (like card number, expiry, etc.)

#####################
# wallet/forms.py

from django import forms
from payments.forms import PaymentForm

class MyPaymentForm(PaymentForm):
    # Add any custom fields you need here
    amount = forms.DecimalField(max_digits=10, decimal_places=2)
    currency = forms.ChoiceField(choices=[('USD', 'USD'), ('EUR', 'EUR'), ('NGN', 'NGN')])
    order_number = forms.CharField(max_length=100)

# wallet/forms.py

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
