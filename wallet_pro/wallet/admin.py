from django.contrib import admin
from .models import User

class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'wallet_balance']
    search_fields = ['usename', 'email']

    def wallet_balance(self, obj):
        # Logic to calculate or fetch the wallet balance
        return obj.wallet.bankdetails.account_number  # Example field
    wallet_balance.short_description = 'Wallet Balance'

admin.site.register(User, UserAdmin)

###################

from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'currency', 'transaction_type', 'status', 'reference', 'timestamp')
    search_fields = ('user__username', 'reference', 'status')
    list_filter = ('currency', 'status', 'transaction_type', 'timestamp')

#####################

from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Transaction

User = get_user_model()

# ✅ Toggle: Set to True to show transactions inline under users
ENABLE_INLINE_TRANSACTIONS = True

class TransactionInline(admin.TabularInline):
    model = Transaction
    fk_name = 'user'  # Or 'recipient' — depending on use case
    extra = 0

from django.contrib import admin
from .models import FlutterwaveWalletBalance

@admin.register(FlutterwaveWalletBalance)
class FlutterwaveWalletAdmin(admin.ModelAdmin):
    list_display = ("currency", "balance", "updated_at")


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'is_staff')
    search_fields = ('username', 'email')
    list_filter = ('is_active', 'is_staff')
    ordering = ('username',)

    if ENABLE_INLINE_TRANSACTIONS:
        inlines = [TransactionInline]


admin.site.unregister(User)  # Unregister if previously registered
admin.site.register(User, CustomUserAdmin)

