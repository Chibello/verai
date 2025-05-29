from django.db import models
from django.conf import settings
from django.utils import timezone

# Use the built-in User model via settings.AUTH_USER_MODEL for flexibility:
User = settings.AUTH_USER_MODEL

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Post(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    POST_STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]

    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    video_url = models.URLField(max_length=200, null=True, blank=True)
    video_file = models.FileField(upload_to='videos/', null=True, blank=True)
    reel = models.FileField(upload_to='reels/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=POST_STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('post', 'user')

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Be cautious: user may not have username if custom user model differs
        return f"Comment by {getattr(self.user, 'username', str(self.user))} on {self.post.title}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    whatsapp_number = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return f"{getattr(self.user, 'username', str(self.user))}'s Profile"

class Reward(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    last_withdrawal = models.DateTimeField(null=True, blank=True)

    def add_points(self, points):
        self.points += points
        self.save()

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{getattr(self.user, 'username', str(self.user))}'s Wallet"

    def add_points(self, points):
        self.balance += points
        self.save()

    def deduct_points(self, points):
        if self.balance >= points:
            self.balance -= points
            self.save()
        else:
            raise ValueError("Insufficient balance")

class RewardTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [('withdrawal', 'Withdrawal'), ('add', 'Add'), ('deduct', 'Deduct')]
    PAYMENT_METHOD_CHOICES = [('stripe', 'Stripe'), ('paystack', 'Paystack')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    reference_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, default='pending')
    points = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type.capitalize()} {self.points} points for {getattr(self.user, 'username', str(self.user))}"

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{getattr(self.user, 'username', str(self.user))} - {self.amount} ({self.status})"

class WithdrawalRequest(models.Model):
    user = models.ForeignKey(User, related_name='withdrawal_requests', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Withdrawal Request by {getattr(self.user, 'username', str(self.user))} for {self.amount}"

class SiteSettings(models.Model):
    moderation_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"Moderation Enabled: {self.moderation_enabled}"

from django.contrib.auth.models import User
from django.db import models
from django.conf import settings

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_pics/', default='default.jpg')

    def __str__(self):
        return self.user.username

from django.db import models

class Task(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.name
