from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from .models import Post, Category, Like, Comment, Reward, RewardTransaction, Wallet

# Register RewardTransaction
@admin.register(RewardTransaction)
class RewardTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'points', 'created_at', 'description', 'transaction_type', 'amount')

# Register Wallet
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')

# Register Post
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'content', 'author__username')

# Register Category
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

# Register the rest using default admin
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Reward)

# Customize admin site
admin.site.site_header = "ZG Blog Admin"
admin.site.site_title = "ZG Blog Admin Portal"
admin.site.index_title = "Welcome to ZG Blog Dashboard"
