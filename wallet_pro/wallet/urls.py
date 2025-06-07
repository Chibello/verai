from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import logout_view
from .views import send_to_bank
from .views import send_to_bank2
from .views import send
from .views import send2

# 
from django.urls import path
from .views import get_transfer_charges

urlpatterns = [

    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('transfer/', views.transfer_funds, name='transfer_funds'),
    path('generate/', views.generate_funds, name='generate_funds'),

    path('api/get-transfer-charges/', get_transfer_charges, name='get_transfer_charges'),
    #path('webhook/flutterwave/', views.flutterwave_webhook, name='flutterwave_webhook'),

    path('deposit/', views.deposit, name='deposit'),
    path('deposit/', views.deposit_view, name='deposit'),
    path('transfer/', views.transfer, name='transfer'),
    path('withdrawal/', views.withdrawal, name='withdrawal'),
    path('home/', views.home, name='home'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),

    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # Password Reset Views
    path('password_reset/', views.PasswordResetCustomView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.PasswordResetConfirmCustomView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('send-to-bank/', send_to_bank, name='send_to_bank'),
    path('send-to-bank2/', send_to_bank2, name='send_to_bank2'),
    path('transfer-callback/', views.transfer_callback, name='transfer_callback'),
    path('send_to_bank/', send_to_bank, name='send_to_bank'),
    path('send/', send, name='send'),
    path('send2/', send2, name='send2'),
    path('send2/', views.send2, name='send2'),
    
    
]
