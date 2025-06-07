from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .models import User, Transaction
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal
from .gateway import CustomPaymentGateway

######

from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.contrib.auth.models import User
from .models import Transaction

@login_required
def transfer_funds(request):
    if request.method == 'POST':
        receiver_username = request.POST.get('receiver_username')
        amount_str = request.POST.get('amount')
        currency = request.POST.get('currency', 'NGN').upper()

        if not receiver_username or not amount_str:
            return render(request, 'wallet/transfer_funds.html', {
                'error': 'Receiver and amount are required.'
            })

        # Validate amount
        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                raise ValueError("Amount must be greater than zero")
        except Exception:
            return render(request, 'wallet/transfer_funds.html', {
                'error': 'Invalid amount entered.'
            })

        # Validate receiver
        try:
            receiver = User.objects.get(username=receiver_username)
        except User.DoesNotExist:
            return render(request, 'wallet/transfer_funds.html', {
                'error': 'Receiver not found.'
            })

        sender = request.user
        currency_field = f"balance_{currency.lower()}"

        if not hasattr(sender, currency_field):
            return render(request, 'wallet/transfer_funds.html', {
                'error': f'Unsupported currency: {currency}'
            })

        sender_balance = getattr(sender, currency_field)

        if sender_balance < amount:
            return render(request, 'wallet/transfer_funds.html', {
                'error': f'Insufficient balance in {currency}'
            })

        # Check if receiver has the same currency field
        if not hasattr(receiver, currency_field):
            return render(request, 'wallet/transfer_funds.html', {
                'error': f'Receiver cannot accept {currency} transfers'
            })

        try:
            with transaction.atomic():
                # Perform balance update
                setattr(sender, currency_field, sender_balance - amount)
                setattr(receiver, currency_field, getattr(receiver, currency_field) + amount)
                sender.save()
                receiver.save()

                # Record transaction
                Transaction.objects.create(
                    user=sender,
                    sender=sender,
                    receiver=receiver,
                    #receiver_username=receiver.username,
                    amount=amount,
                    currency=currency,
                    transaction_type='TRANSFER',
                    status='COMPLETED'
                )

                return render(request, 'wallet/transfer_funds.html', {
                    'success': f'Transferred {currency} {amount} to {receiver.username} successfully.'
                })

        except Exception as e:
            return render(request, 'wallet/transfer_funds.html', {
                'error': f'Transfer failed: {str(e)}'
            })

    return render(request, 'wallet/transfer_funds.html')

#####################

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import User

@login_required
def user_dashboard(request):
    user = request.user  # Get the currently logged-in user
    return render(request, 'wallet/user_dashboard.html', {'user': user})

##########################

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from .models import User, Transaction

@staff_member_required
def dashboard(request):
    query = request.GET.get('q')
    users = User.objects.all()
    transactions = Transaction.objects.all()

    if query:
        users = users.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        )
        transactions = transactions.filter(
            Q(reference__icontains=query) | Q(user__username__icontains=query)
        )

    context = {
        'users': users,
        'transactions': transactions,
        'query': query,
    }
    return render(request, 'wallet/dashboard.html', context)
    

#################################################
from django.shortcuts import render
from django.contrib import messages


def deposit_view(request):
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        currency = request.POST['currency']
        try:
            gateway = CustomPaymentGateway(request.user)
            result = gateway.deposit(amount, currency)
            messages.success(request, result)
        except Exception as e:
            messages.error(request, str(e))
    return render(request, 'wallet/deposit.html')


#####################################################################
from decimal import Decimal
from uuid import uuid4
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .models import User, Transaction

@staff_member_required
@login_required
def generate_funds(request):
    if request.method == 'POST':
        user = request.user
        try:
            amount = Decimal(request.POST.get('amount'))
        except (TypeError, ValueError):
            return redirect('dashboard')  # Optionally add error message

        currency = request.POST.get('currency', '').upper()

        if currency not in ['USD', 'NGN', 'EUR', 'GBP']:
            return redirect('dashboard')  # Optionally add error message

        # Update user's wallet balance per currency
        if currency == 'USD':
            user.balance_usd += amount
        elif currency == 'NGN':
            user.balance_ngn += amount
        elif currency == 'EUR':
            user.balance_eur += amount
        elif currency == 'GBP':
            user.balance_gbp += amount

        user.wallet_balance += amount
        user.save()

        # ✅ Define reference
        reference = str(uuid4())

        # Create transaction record
        Transaction.objects.create(
            user=user,
            amount=amount,
            currency=currency,
            transaction_type='DEPOSIT',
            reference=reference,
            status='COMPLETED'
        )

        return redirect('dashboard')

    # Render the form for GET request
    return render(request, 'wallet/generate_funds.html')
##########

from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from .models import Transaction  # adjust if needed

@login_required
def deposit(request):
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount'))
            currency = request.POST.get('currency')
        except (TypeError, InvalidOperation):
            messages.error(request, "Invalid amount.")
            return redirect('deposit')  # Replace with your actual deposit URL name

        user = request.user

        if not currency:
            messages.error(request, "Currency is required.")
            return redirect('deposit')

        with transaction.atomic():
            user.wallet_balance += amount
            user.save()

            Transaction.objects.create(
                user=request.user,
                sender=request.user,
                receiver=user,
                amount=amount,
                transaction_type='Deposit',
                status='Completed',
                currency=currency
            )

            messages.success(request, f"Deposited {amount} {currency} successfully.")
            return redirect('deposit')  # Redirect to prevent form resubmission

    return render(request, 'wallet/deposit.html')

def withdraw(request):
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        currency = request.POST.get('currency')
        user = request.user

        if user.wallet_balance >= amount:
            with transaction.atomic():
                user.wallet_balance -= amount
                user.save()
                Transaction.objects.create(
                    sender=user,
                    receiver=user,
                    amount=amount,
                    transaction_type='Withdraw',
                    status='Completed',
                    currency=currency
                )
                messages.success(request, f"Withdrew {amount} {currency} successfully.")
        else:
            messages.error(request, "Insufficient balance.")
    return render(request, 'wallet/withdraw.html')

############################################
def withdrawal(request):
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        currency = request.POST.get('currency')
        user = request.user

        if user.wallet_balance >= amount:
            with transaction.atomic():
                user.wallet_balance -= amount
                user.save()
                Transaction.objects.create(
                    user=request.user,
                    sender=request.user,
                    receiver=user,
                    amount=amount,
                    transaction_type='Withdraw',
                    status='Completed',
                    currency=currency
                )
                messages.success(request, f"Withdrew {amount} {currency} successfully.")
        else:
            messages.error(request, "Insufficient balance.")
    return render(request, 'wallet/withdraw.html')


############################################
def transfer(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        currency = request.POST.get('currency')
        receiver_username = request.POST.get('receiver')
        user = request.user

        try:
            receiver = User.objects.get(username=receiver_username)
            if user.wallet_balance >= amount:
                with transaction.atomic():
                    user.wallet_balance -= amount
                    receiver.wallet_balance += amount
                    user.save()
                    receiver.save()
                    Transaction.objects.create(
                        user=request.user,
                        sender=request.user,
                        receiver=receiver,
                        amount=amount,
                        transaction_type='Transfer',
                        status='Completed',
                        currency=currency
                    )
                    messages.success(request, f"Transferred {amount} {currency} to {receiver.username} successfully.")
            else:
                messages.error(request, "Insufficient balance.")
        except User.DoesNotExist:
            messages.error(request, "Receiver not found.")
    return render(request, 'wallet/transfer.html')

###############################
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirect to login or home page
    else:
        form = CustomUserCreationForm()

    return render(request, 'wallet/signup.html', {'form': form})

###############################

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from .forms import LoginForm, PasswordResetCustomForm

'''
# Signup view
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            # Automatically log the user in after signup
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('user_dashboard')  # Redirect to the user dashboard after login
    else:
        form = SignupForm()
    
    return render(request, 'wallet/signup.html', {'form': form})
'''

# Login view
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('user_dashboard')  # Redirect to the user dashboard after login
    else:
        form = LoginForm()

    return render(request, 'wallet/login.html', {'form': form})

# Password reset view (using Django's built-in PasswordResetView)
class PasswordResetCustomView(PasswordResetView):
    form_class = PasswordResetCustomForm
    success_url = reverse_lazy('password_reset_done')

# Password reset confirm view (using Django's built-in PasswordResetConfirmView)
class PasswordResetConfirmCustomView(PasswordResetConfirmView):
    success_url = reverse_lazy('login')
######################
from django.shortcuts import render
from .forms import PaymentForm
#from payment_app.gateway import CustomPaymentGateway
from .gateway import CustomPaymentGateway


def make_payment(request):
    form = PaymentForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        amount = form.cleaned_data['amount']
        currency = form.cleaned_data['currency']

        payment_gateway = CustomPaymentGateway(
            api_key="your_api_key", secret_key="your_secret_key"
        )

        payment_response = payment_gateway.process_payment(
            amount, currency, request.user
        )

        if payment_response.get("status") == "success":
            return render(request, 'wallet/payment_success.html', {
                'payment_response': payment_response
            })
        else:
            return render(request, 'wallet/payment_failed.html', {
                'error': 'Payment failed'
            })

    return render(request, 'wallet/make_payment.html', {'form': form})

############################################################

def payment_success(request):
    return render(request, 'wallet/payment_success.html')

# 

def payment_failed(request):
    return render(request, 'wallet/payment_failed.html')

###########
import uuid
import logging
from decimal import Decimal
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from .models import Transaction
from .flutterwave import initiate_flutterwave_transfer

logger = logging.getLogger(__name__)

@csrf_exempt
@login_required
def send_to_bank(request):
    user = request.user

    if request.method == 'GET':
        return render(request, 'wallet/send_to_bank.html')

    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount'))
            currency = request.POST.get('currency', 'NGN').upper()
            account_bank = request.POST.get('account_bank')
            account_number = request.POST.get('account_number')
            narration = request.POST.get('narration', 'Wallet payout')
        except Exception as e:
            logger.error(f"Invalid input: {e}")
            return render(request, 'wallet/send_to_bank.html', {'error': 'Invalid input data'})

        wallet = user.wallet
        currency_field = f'balance_{currency.lower()}'
        if not hasattr(wallet, currency_field):
            return render(request, 'wallet/send_to_bank.html', {'error': 'Unsupported currency'})

        balance = getattr(wallet, currency_field)
        if balance < amount:
            return render(request, 'wallet/send_to_bank.html', {'error': f'Insufficient {currency} balance'})

        # Call Flutterwave
        result = initiate_flutterwave_transfer(amount, currency, account_bank, account_number, narration)
        if result and result.get('status') == 'success':
            reference = result['data']['reference']
            with db_transaction.atomic():
                setattr(wallet, currency_field, balance - amount)
                wallet.save()

                Transaction.objects.create(
                    user=user,
                    sender=user,
                    amount=amount,
                    currency=currency,
                    transaction_type='TRANSFER',
                    status='PENDING',
                    reference=reference,
                    narration=narration
                )

            return render(request, 'wallet/send_to_bank.html', {
                'success': 'Transfer initiated',
                'reference': reference
            })

        error_msg = result.get('message', 'Transfer failed') if result else 'Network error'
        return render(request, 'wallet/send_to_bank.html', {'error': error_msg})

    return JsonResponse({'error': 'Invalid request method'}, status=405)

###########
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Transaction
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def transfer_callback(request):
    if request.method == 'POST':
        auth = request.headers.get('Authorization')
        if auth != f'Bearer {settings.FLW_SECRET_KEY}':
            logger.warning('Unauthorized webhook attempt')
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        try:
            data = json.loads(request.body)
            reference = data.get('data', {}).get('reference')
            status = data.get('status')

            if not reference:
                return JsonResponse({'error': 'Missing reference'}, status=400)

            transaction = Transaction.objects.filter(reference=reference).first()
            if not transaction:
                return JsonResponse({'error': 'Transaction not found'}, status=404)

            transaction.status = 'COMPLETED' if status == 'success' else 'FAILED'
            transaction.save()

            logger.info(f"Transaction {reference} updated to {transaction.status}")
            return JsonResponse({'message': 'Webhook processed'})

        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)

    return JsonResponse({'error': 'Invalid method'}, status=405)

######################
###################
from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('login')  # Or redirect to homepage or login page

############################

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Transaction, BankDetails

@login_required
def home(request):
    # Get the logged-in user
    user = request.user

    # Fetch the user's wallet balance in their preferred currency
    balance = getattr(user, f'balance_{user.currency.lower()}', 0)

    # Fetch the latest 5 transactions of the user
    transactions = Transaction.objects.filter(user=user).order_by('-timestamp')[:5]

    # Fetch the user's bank details (if available)
    try:
        bank_details = BankDetails.objects.get(user=user)
    except BankDetails.DoesNotExist:
        bank_details = None

    # Pass the data to the template
    return render(request, 'wallet/home.html', {
        'user': user,
        'balance': balance,
        'currency': user.currency,
        'transactions': transactions,
        'bank_details': bank_details
    })

##############
from django.shortcuts import render
from .models import Transaction, BankDetails

def home(request):
    user = request.user
    transactions = Transaction.objects.filter(user=user).order_by('-timestamp')[:5]
    bank_details = BankDetails.objects.filter(user=user).first()

    context = {
        'currency': user.currency,
        'balance': user.wallet_balance,
        'balance_usd': user.balance_usd,
        'balance_ngn': user.balance_ngn,
        'balance_eur': user.balance_eur,
        'balance_gbp': user.balance_gbp,
        'transactions': transactions,
        'bank_details': bank_details,
    }

    return render(request, 'wallet/home.html', context)

###############

import uuid
from decimal import Decimal
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Transaction
from .paystack import initiate_paystack_bank_transfer  # ← REPLACED flutterwave

##@csrf_exempt  # Only for dev/testing; remove in production
@login_required
def send(request):
    if request.method == 'GET':
        return render(request, 'wallet/send.html')

    if request.method == 'POST':
        user = request.user
        try:
            amount = Decimal(request.POST.get('amount'))
            currency = request.POST.get('currency', 'NGN').upper()
            account_bank = request.POST.get('account_bank')
            account_number = request.POST.get('account_number')
            narration = request.POST.get('narration', 'Wallet payout')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid input data')
            return redirect('send')

        # Validate balance
        currency_field = f'balance_{currency.lower()}'
        if not hasattr(user, currency_field):
            messages.error(request, f'Unsupported currency: {currency}')
            return redirect('send')

        user_balance = getattr(user, currency_field)
        if user_balance < amount:
            messages.error(request, f'Insufficient balance in {currency}')
            return redirect('send')

        # Initiate Paystack transfer
        result = initiate_paystack_bank_transfer(
            user, amount, currency, account_bank, account_number, narration
        )

        if result.get('status') == 'success':
            # Deduct balance
            setattr(user, currency_field, user_balance - amount)
            user.save()

            # Record transaction
            Transaction.objects.create(
                user=user,
                sender=user,
                amount=amount,
                currency=currency,
                transaction_type='TRANSFER',
                status='PENDING',  # Until webhook confirms
                reference=result['reference'],
                narration=narration
            )

            messages.success(request, 'Transfer initiated successfully!')
            return redirect('send')

        messages.error(request, result.get('message', 'Transfer failed'))
        return redirect('send')

    return JsonResponse({'error': 'Invalid request method'}, status=405)

####################

import uuid
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Transaction
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY  # Set your Stripe secret key


@csrf_exempt  # Only for testing — remove in production
@login_required
def send2(request):
    if request.method == 'GET':
        return render(request, 'wallet/send2.html')

    if request.method == 'POST':
        user = request.user
        try:
            amount = Decimal(request.POST.get('amount'))
            currency = request.POST.get('currency', 'usd').lower()
            narration = request.POST.get('narration', 'Wallet payout')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid input data')
            return redirect('send2')

        currency_field = f'balance_{currency}'
        if not hasattr(user, currency_field):
            messages.error(request, f'Unsupported currency: {currency.upper()}')
            return redirect('send2')

        balance = getattr(user, currency_field)
        if balance < amount:
            messages.error(request, f'Insufficient balance in {currency.upper()}')
            return redirect('send2')

        # Stripe: Payouts go to connected accounts
        stripe_account_id = getattr(user, 'stripe_account_id', None)
        if not stripe_account_id:
            messages.error(request, 'User is not connected to Stripe.')
            return redirect('send2')

        try:
            # Create a payout to the connected account
            payout = stripe.Payout.create(
                amount=int(amount * 100),  # in cents
                currency=currency,
                statement_descriptor=narration[:22],
                metadata={'user_id': user.id, 'narration': narration},
                stripe_account=stripe_account_id  # ✅ connected account
            )

            # Deduct from wallet
            setattr(user, currency_field, balance - amount)
            user.save()

            # Record transaction
            Transaction.objects.create(
                user=user,
                sender=user,
                amount=amount,
                currency=currency.upper(),
                transaction_type='TRANSFER',
                status='PENDING',
                reference=payout.id,
                narration=narration
            )

            messages.success(request, 'Stripe payout initiated successfully.')
            return redirect('send2')

        except stripe.error.StripeError as e:
            messages.error(request, f'Stripe Error: {str(e)}')
            return redirect('send2')

    return JsonResponse({'error': 'Invalid request method'}, status=405)

###########
# views.py
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .utils import FEES, VATS

@require_GET
def get_transfer_charges(request):
    try:
        amount = Decimal(request.GET.get('amount', '0'))
        currency = request.GET.get('currency', 'NGN').upper()

        fee = FEES.get(currency, Decimal("0.00"))
        vat = VATS.get(currency, Decimal("0.00"))
        total = amount + fee + vat

        return JsonResponse({
            'fee': str(fee),
            'vat': str(vat),
            'total': str(total),
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

##########

import uuid
import logging
import requests
from decimal import Decimal
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction as db_transaction
from .models import Transaction
from .utils import initiate_flutterwave_transfer
from django.conf import settings

# Set up logging
logger = logging.getLogger(__name__)

# Define fees and VAT per currency (match with frontend)
FEES = {
    "NGN": Decimal("10.00"),
    "USD": Decimal("0.50"),
    "EUR": Decimal("0.45"),
    "GBP": Decimal("0.40"),
}

VATS = {
    "NGN": Decimal("0.75"),
    "USD": Decimal("0.05"),
    "EUR": Decimal("0.045"),
    "GBP": Decimal("0.04"),
}

@login_required
def send_to_bank2(request):
    if request.method == 'GET':
        return render(request, 'wallet/send_to_bank2.html')

    elif request.method == 'POST':
        user = request.user
        try:
            amount = Decimal(request.POST.get('amount'))
            currency = request.POST.get('currency', 'NGN').upper()
            account_bank = request.POST.get('account_bank')
            account_number = request.POST.get('account_number')
            narration = request.POST.get('narration', 'Wallet payout')
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid input data: {str(e)}")
            return render(request, 'wallet/send_to_bank2.html', {'error': 'Invalid input data'})

        # Validate currency supported
        currency_field = f'balance_{currency.lower()}'
        if not hasattr(user, currency_field):
            return render(request, 'wallet/send_to_bank2.html', {'error': 'Unsupported currency'})

        user_balance = getattr(user, currency_field)

        fee = FEES.get(currency, Decimal("0.00"))
        vat = VATS.get(currency, Decimal("0.00"))
        total_deduction = amount + fee + vat

        if user_balance < total_deduction:
            return render(request, 'wallet/send_to_bank2.html', {
                'error': f'Insufficient {currency} balance to cover amount + fees. Required: {total_deduction}'
            })

        # Initiate transfer to Flutterwave with the actual amount (not fees)
        reference = str(uuid.uuid4())
        response = initiate_flutterwave_transfer(amount, currency, account_bank, account_number, narration)

        if response and response.get('status') == 'success':
            # Deduct total from user balance atomically and log transaction
            with db_transaction.atomic():
                setattr(user, currency_field, user_balance - total_deduction)
                user.save()

                Transaction.objects.create(
                    user=user,
                    sender=user,
                    amount=amount,
                    currency=currency,
                    transaction_type='TRANSFER',
                    status='PENDING',
                    reference=reference,
                    narration=narration,
                    fee=fee,
                    vat=vat
                )

            return render(request, 'wallet/send_to_bank2.html', {
                'success': 'Transfer initiated successfully',
                'reference': reference
            })
        else:
            error_message = response.get('message', 'Transfer failed') if response else 'Error contacting Flutterwave API.'
            logger.error(f"Flutterwave API error: {error_message}")
            return render(request, 'wallet/send_to_bank2.html', {'error': error_message})

    return JsonResponse({'error': 'Invalid request method'}, status=405)

'''
import uuid
import logging
from decimal import Decimal, InvalidOperation
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from .models import Transaction
from .utils import initiate_flutterwave_transfer  # adjust if utils path differs

logger = logging.getLogger(__name__)

FEES = {
    "NGN": Decimal("10.00"),
    "USD": Decimal("0.50"),
    "EUR": Decimal("0.45"),
    "GBP": Decimal("0.40"),
}

VATS = {
    "NGN": Decimal("0.75"),
    "USD": Decimal("0.05"),
    "EUR": Decimal("0.045"),
    "GBP": Decimal("0.04"),
}

@login_required
def send_to_bank2(request):
    if request.method == 'GET':
        return render(request, 'wallet/send_to_bank2.html')

    elif request.method == 'POST':
        user = request.user
        try:
            amount_str = request.POST.get('amount', '0')
            amount = Decimal(amount_str)
            if amount <= 0:
                return render(request, 'wallet/send_to_bank2.html', {'error': 'Amount must be greater than zero'})

            currency = request.POST.get('currency', 'NGN').upper()
            account_bank = request.POST.get('account_bank')
            account_number = request.POST.get('account_number')
            narration = request.POST.get('narration', 'Wallet payout')

            if not account_bank or not account_number:
                return render(request, 'wallet/send_to_bank2.html', {'error': 'Bank code and account number are required'})

        except (InvalidOperation, TypeError) as e:
            logger.error(f"Invalid input data: {e}")
            return render(request, 'wallet/send_to_bank2.html', {'error': 'Invalid input data'})

        currency_field = f'balance_{currency.lower()}'
        if not hasattr(user, currency_field):
            return render(request, 'wallet/send_to_bank2.html', {'error': f'Unsupported currency: {currency}'})

        user_balance = getattr(user, currency_field)
        fee = FEES.get(currency, Decimal("0.00"))
        vat = VATS.get(currency, Decimal("0.00"))
        total_deduction = amount + fee + vat

        if user_balance < total_deduction:
            return render(request, 'wallet/send_to_bank2.html', {
                'error': f'Insufficient {currency} balance to cover amount + fees (Total required: {total_deduction})'
            })

        # Generate unique reference
        reference = str(uuid.uuid4())

        # Call Flutterwave API to initiate transfer of 'amount' (fees deducted locally)
        response = initiate_flutterwave_transfer(amount, currency, account_bank, account_number, narration)

        if response and response.get('status') == 'success':
            try:
                with db_transaction.atomic():
                    # Deduct total (amount + fee + vat) from user balance atomically
                    setattr(user, currency_field, user_balance - total_deduction)
                    user.save(update_fields=[currency_field])

                    # Create transaction record
                    Transaction.objects.create(
                        user=user,
                        sender=user,
                        amount=amount,
                        currency=currency,
                        transaction_type='TRANSFER',
                        status='PENDING',
                        reference=reference,
                        narration=narration,
                        fee=fee,
                        vat=vat
                    )
            except Exception as e:
                logger.error(f"DB error during transfer transaction creation: {e}")
                return render(request, 'wallet/send_to_bank2.html', {'error': 'Internal error. Please try again later.'})

            return render(request, 'wallet/send_to_bank2.html', {
                'success': 'Transfer initiated successfully',
                'reference': reference
            })
        else:
            error_message = response.get('message', 'Transfer failed') if response else 'Error contacting Flutterwave API.'
            logger.error(f"Flutterwave API error: {error_message}")
            return render(request, 'wallet/send_to_bank2.html', {'error': error_message})

    # For methods other than GET or POST
    return JsonResponse({'error': 'Invalid request method'}, status=405)


import uuid
import logging
from decimal import Decimal, InvalidOperation
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from .models import Transaction
from .utils import initiate_flutterwave_transfer  # adjust if utils path differs

logger = logging.getLogger(__name__)

FEES = {
    "NGN": Decimal("10.00"),
    "USD": Decimal("0.50"),
    "EUR": Decimal("0.45"),
    "GBP": Decimal("0.40"),
}

VATS = {
    "NGN": Decimal("0.75"),
    "USD": Decimal("0.05"),
    "EUR": Decimal("0.045"),
    "GBP": Decimal("0.04"),
}

@login_required
def send_to_bank2(request):
    if request.method == 'GET':
        return render(request, 'wallet/send_to_bank2.html')

    elif request.method == 'POST':
        user = request.user
        try:
            amount_str = request.POST.get('amount', '0')
            amount = Decimal(amount_str)
            if amount <= 0:
                return render(request, 'wallet/send_to_bank2.html', {'error': 'Amount must be greater than zero'})

            currency = request.POST.get('currency', 'NGN').upper()
            account_bank = request.POST.get('account_bank')
            account_number = request.POST.get('account_number')
            narration = request.POST.get('narration', 'Wallet payout')

            if not account_bank or not account_number:
                return render(request, 'wallet/send_to_bank2.html', {'error': 'Bank code and account number are required'})

        except (InvalidOperation, TypeError) as e:
            logger.error(f"Invalid input data: {e}")
            return render(request, 'wallet/send_to_bank2.html', {'error': 'Invalid input data'})

        currency_field = f'balance_{currency.lower()}'
        if not hasattr(user, currency_field):
            return render(request, 'wallet/send_to_bank2.html', {'error': f'Unsupported currency: {currency}'})

        user_balance = getattr(user, currency_field)
        fee = FEES.get(currency, Decimal("0.00"))
        vat = VATS.get(currency, Decimal("0.00"))
        total_deduction = amount + fee + vat

        if user_balance < total_deduction:
            return render(request, 'wallet/send_to_bank2.html', {
                'error': f'Insufficient {currency} balance to cover amount + fees (Total required: {total_deduction})'
            })

        # Generate unique reference
        reference = str(uuid.uuid4())

        # Call Flutterwave API to initiate transfer of 'amount' (fees deducted locally)
        response = initiate_flutterwave_transfer(amount, currency, account_bank, account_number, reference, narration)

        if response and response.get('status') == 'success':
            try:
                with db_transaction.atomic():
                    # Deduct total (amount + fee + vat) from user balance atomically
                    setattr(user, currency_field, user_balance - total_deduction)
                    user.save(update_fields=[currency_field])

                    # Create transaction record
                    Transaction.objects.create(
                        user=user,
                        sender=user,
                        amount=amount,
                        currency=currency,
                        transaction_type='TRANSFER',
                        status='PENDING',
                        reference=reference,
                        narration=narration,
                        fee=fee,
                        vat=vat
                    )
            except Exception as e:
                logger.error(f"DB error during transfer transaction creation: {e}")
                return render(request, 'wallet/send_to_bank2.html', {'error': 'Internal error. Please try again later.'})

            return render(request, 'wallet/send_to_bank2.html', {
                'success': 'Transfer initiated successfully',
                'reference': reference
            })
        else:
            error_message = response.get('message', 'Transfer failed') if response else 'Error contacting Flutterwave API.'
            logger.error(f"Flutterwave API error: {error_message}")
            return render(request, 'wallet/send_to_bank2.html', {'error': error_message})

    # For methods other than GET or POST
    return JsonResponse({'error': 'Invalid request method'}, status=405)

'''
##########
import uuid
import logging
from decimal import Decimal, InvalidOperation
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from .models import Transaction
from .utils import initiate_flutterwave_transfer

logger = logging.getLogger(__name__)

FEES = {
    "NGN": Decimal("10.00"),
    "USD": Decimal("0.50"),
    "EUR": Decimal("0.45"),
    "GBP": Decimal("0.40"),
}

VATS = {
    "NGN": Decimal("0.75"),
    "USD": Decimal("0.05"),
    "EUR": Decimal("0.045"),
    "GBP": Decimal("0.04"),
}

@login_required
def send_to_bank2(request):
    if request.method == 'GET':
        return render(request, 'wallet/send_to_bank2.html')

    elif request.method == 'POST':
        user = request.user
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            if amount <= 0:
                return render(request, 'wallet/send_to_bank2.html', {'error': 'Amount must be greater than zero'})

            currency = request.POST.get('currency', 'NGN').upper()
            account_bank = request.POST.get('account_bank')
            account_number = request.POST.get('account_number')
            narration = request.POST.get('narration', 'Wallet payout')

            if not account_bank or not account_number:
                return render(request, 'wallet/send_to_bank2.html', {'error': 'Bank code and account number are required'})

        except (InvalidOperation, TypeError) as e:
            logger.error(f"Invalid input data: {e}")
            return render(request, 'wallet/send_to_bank2.html', {'error': 'Invalid input data'})

        currency_field = f'balance_{currency.lower()}'
        if not hasattr(user, currency_field):
            return render(request, 'wallet/send_to_bank2.html', {'error': f'Unsupported currency: {currency}'})

        user_balance = getattr(user, currency_field)
        fee = FEES.get(currency, Decimal("0.00"))
        vat = VATS.get(currency, Decimal("0.00"))
        total_deduction = amount + fee + vat

        if user_balance < total_deduction:
            return render(request, 'wallet/send_to_bank2.html', {
                'error': f'Insufficient {currency} balance to cover amount + fees (Total required: {total_deduction})'
            })

        reference = str(uuid.uuid4())

        try:
            with db_transaction.atomic():
                # Deduct wallet
                setattr(user, currency_field, user_balance - total_deduction)
                user.save(update_fields=[currency_field])

                # Create transaction with pending status
                Transaction.objects.create(
                    user=user,
                    sender=user,
                    amount=amount,
                    currency=currency,
                    transaction_type='TRANSFER',
                    status='PENDING',
                    reference=reference,
                    narration=narration,
                    fee=fee,
                    vat=vat
                )

            # Initiate transfer outside atomic block
            response = initiate_flutterwave_transfer(
                amount=amount,
                currency=currency,
                account_bank=account_bank,
                account_number=account_number,
                reference=reference,
                narration=narration
            )

            if not response or response.get('status') != 'success':
                logger.error(f"Flutterwave transfer failed for {reference}: {response}")
                return render(request, 'wallet/send_to_bank2.html', {
                    'error': f"Flutterwave transfer failed: {response.get('message', 'Unknown error')}",
                    'reference': reference
                })

            return render(request, 'wallet/send_to_bank2.html', {
                'success': 'Transfer request submitted successfully. Awaiting confirmation.',
                'reference': reference
            })

        except Exception as e:
            logger.exception(f"Transfer failed: {e}")
            return render(request, 'wallet/send_to_bank2.html', {'error': 'Internal error. Please try again later.'})

##########

#############
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Transaction
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def flutterwave_webhook(request):
    try:
        payload = json.loads(request.body)
        data = payload.get('data', {})
        reference = data.get('reference')
        status = data.get('status')  # "SUCCESSFUL", "FAILED", etc.

        logger.info(f"Webhook received for reference {reference}: {status}")

        if not reference:
            return JsonResponse({'error': 'No reference provided'}, status=400)

        transaction = Transaction.objects.filter(reference=reference).first()
        if not transaction:
            return JsonResponse({'error': 'Transaction not found'}, status=404)

        if status == 'SUCCESSFUL':
            transaction.status = 'SUCCESSFUL'
            transaction.save(update_fields=['status'])

        elif status == 'FAILED':
            transaction.status = 'FAILED'
            transaction.save(update_fields=['status'])

            # Optional refund logic if wallet was debited
            user = transaction.user
            currency_field = f'balance_{transaction.currency.lower()}'
            refund_amount = transaction.amount + transaction.fee + transaction.vat
            setattr(user, currency_field, getattr(user, currency_field) + refund_amount)
            user.save(update_fields=[currency_field])

        return JsonResponse({'status': 'success'})

    except Exception as e:
        logger.exception("Webhook processing failed")
        return JsonResponse({'error': 'Webhook processing failed'}, status=500)

############
