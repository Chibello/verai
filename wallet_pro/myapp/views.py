from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Like, Comment, Category, Reward, Payment
from .forms import BasicPostForm, MediaPostForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
import stripe
from django.conf import settings
from django.db.models import Q

###################
import stripe
import paystack
import requests
import uuid
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User, RewardTransaction

stripe.api_key = settings.STRIPE_SECRET_KEY

def withdraw_reward(request):
    if request.method == 'POST':
        user_id = request.POST['user']
        payment_method = request.POST['payment_method']
        amount = float(request.POST['amount'])

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('withdraw_reward')

        if user.wallet_balance < amount:
            messages.error(request, 'Insufficient balance.')
            return redirect('withdraw_reward')

        # Deduct funds before processing to avoid double spending
        user.wallet_balance -= amount
        user.save()

        reference = str(uuid.uuid4())

        transaction = RewardTransaction.objects.create(
            user=user,
            amount=amount,
            transaction_type='withdrawal',
            payment_method=payment_method,
            reference_id=reference,
            status='pending',
        )

        if payment_method == 'stripe':
            if not user.stripe_account_id:
                messages.error(request, 'User does not have a connected Stripe account.')
                return redirect('withdraw_reward')

            try:
                # Send a payout to user's connected Stripe account (must be verified)
                transfer = stripe.Transfer.create(
                    amount=int(amount * 100),  # in cents
                    currency="usd",
                    destination=user.stripe_account_id,
                    transfer_group=f"REWARD_WITHDRAWAL_{user.id}"
                )
                transaction.reference_id = transfer.id
                transaction.status = 'success'
                transaction.save()
                messages.success(request, 'Stripe payout successful.')

            except Exception as e:
                # Revert wallet balance
                user.wallet_balance += amount
                user.save()
                transaction.status = 'failed'
                transaction.save()
                messages.error(request, f'Stripe error: {str(e)}')

        elif payment_method == 'paystack':
            if not user.paystack_recipient_code:
                messages.error(request, 'User does not have a Paystack recipient code.')
                return redirect('withdraw_reward')

            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json"
            }

            data = {
                "source": "balance",
                "reason": "Reward withdrawal",
                "amount": int(amount * 100),  # kobo
                "recipient": user.paystack_recipient_code,
                "reference": reference
            }

            try:
                response = requests.post("https://api.paystack.co/transfer", json=data, headers=headers)
                res_data = response.json()

                if res_data.get('status') is True:
                    transfer_code = res_data['data']['transfer_code']
                    transaction.reference_id = transfer_code
                    transaction.status = 'success'
                    transaction.save()
                    messages.success(request, 'Paystack payout successful.')
                else:
                    user.wallet_balance += amount
                    user.save()
                    transaction.status = 'failed'
                    transaction.save()
                    messages.error(request, f"Paystack error: {res_data.get('message')}")

            except Exception as e:
                user.wallet_balance += amount
                user.save()
                transaction.status = 'failed'
                transaction.save()
                messages.error(request, f"Paystack error: {str(e)}")

        return redirect('wallet_overview')

    users = User.objects.all()
    return render(request, 'withdraw_reward.html', {'users': users})

def create_paystack_recipient(user):
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "type": "nuban",
        "name": user.name,
        "account_number": "0123456789",
        "bank_code": "058",  # GTBank for example
        "currency": "NGN"
    }

    response = requests.post("https://api.paystack.co/transferrecipient", json=data, headers=headers)
    result = response.json()

    if result.get('status') is True:
        user.paystack_recipient_code = result['data']['recipient_code']
        user.save()

#######################################################

def home(request):
    posts = Post.objects.all()  # Example query for posts
    return render(request, 'home.html', {'posts': posts})


# Post Detail View
from django.shortcuts import render, redirect, get_object_or_404
from .models import Post, Like, Comment
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Post, Like, Comment, Profile
from django.contrib import messages
from django.http import JsonResponse

# Post Detail View
#def post_detail(request, post_id):
 #   post = get_object_or_404(Post, id=post_id)
  #  has_liked = post.likes.filter(user=request.user).exists()  # Check if the user has liked the post
   # return render(request, 'post_detail.html', {'post': post, 'has_liked': has_liked})

from django.shortcuts import render, get_object_or_404
from .models import Post

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)

    has_liked = False  # Default for anonymous users

    # Only check likes if the user is logged in
    if request.user.is_authenticated:
        has_liked = post.likes.filter(user=request.user).exists()

    return render(request, 'post_detail.html', {
        'post': post,
        'has_liked': has_liked,
    })


# Like Post View
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if not post.likes.filter(user=request.user).exists():
        Like.objects.create(post=post, user=request.user)
    return redirect('post_detail', post_id=post.id)

# Like Comment View
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    # Handle liking comment logic here (e.g., create a Like object for comments)
    return JsonResponse({'message': 'Comment liked successfully'})

# Reply to Comment View
def reply_comment(request, comment_id):
    parent_comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Comment.objects.create(post=parent_comment.post, user=request.user, content=content, parent=parent_comment)
            messages.success(request, "Your reply has been posted successfully.")
        else:
            messages.error(request, "Reply content cannot be empty.")
    return redirect('post_detail', post_id=parent_comment.post.id)

# User Profile View
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required

@login_required
def profile(request, user_id):
    user_profile = get_object_or_404(User, id=user_id)
    # Assuming you're also showing posts by this user or similar
    posts = user_profile.post_set.all()  # Adjust if using a related_name

    return render(request, 'profile.html', {
        'user_profile': user_profile,
        'posts': posts,
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Post, Like, Comment, Category
from .forms import BasicPostForm, MediaPostForm

# Like Post View
@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Check if the user has already liked the post
    if not post.likes.filter(user=request.user).exists():
        Like.objects.create(post=post, user=request.user)
    
    return redirect('post_detail', post_id=post.id)

# Unlike Post View
@login_required
def unlike_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Find the like object and delete it if it exists
    like = post.likes.filter(user=request.user).first()
    if like:
        like.delete()
    
    return redirect('post_detail', post_id=post.id)

# Comment on Post View
@login_required
def comment_on_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        
        # Check if content is empty
        if not content:
            messages.error(request, "Comment content cannot be empty.")
            return redirect('post_detail', post_id=post.id)
        
        # Create the comment
        Comment.objects.create(post=post, user=request.user, content=content)
        
        messages.success(request, "Your comment has been posted successfully.")
    
    return redirect('post_detail', post_id=post.id)

# Edit Post View
@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('post_detail', post_id=post.id)
    
    if request.method == 'POST':
        form = BasicPostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated successfully!')
            return redirect('post_detail', post_id=post.id)
    else:
        form = BasicPostForm(instance=post)

    return render(request, 'edit_post.html', {'form': form, 'post': post})

# Delete Post View
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('home')
    
    return render(request, 'delete_post.html', {'post': post})

# Create Post View (Basic & Media)
@login_required
def create_post(request):
    categories = Category.objects.all()  # Get all categories
    basic_form = BasicPostForm()
    media_form = MediaPostForm()

    if request.method == 'POST':
        post_type = request.POST.get('post_type')

        if post_type == 'basic':
            basic_form = BasicPostForm(request.POST)
            if basic_form.is_valid():
                post = basic_form.save(commit=False)
                post.author = request.user  # Assign the user as the author
                post.save()  # Save the post
                return redirect('home')

        elif post_type == 'media':
            media_form = MediaPostForm(request.POST, request.FILES)
            if media_form.is_valid():
                post = media_form.save(commit=False)
                post.author = request.user  # Assign the user as the author
                post.save()  # Save the post
                return redirect('home')

    return render(request, 'create_post.html', {
        'basic_form': basic_form,
        'media_form': media_form,
        'categories': categories,
    })

# Category Pages View
def category_page(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    posts = Post.objects.filter(category=category)
    return render(request, 'category_page.html', {'category': category, 'posts': posts})

# Category List View
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'category_list.html', {'categories': categories})

# Search Posts View
def search_posts(request):
    query = request.GET.get('q', '')
    posts = Post.objects.filter(
        Q(title__icontains=query) | Q(content__icontains=query)
    )
    return render(request, 'search_results.html', {'posts': posts, 'query': query})

# User Signup View
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

# Withdraw Rewards View
@login_required
def withdraw_rewards(request):
    reward = Reward.objects.get(user=request.user)
    amount_to_withdraw = reward.points * 0.1  # Example: 1 point = $0.1

    if request.method == 'POST':
        # Create a payment intent using Stripe
        intent = stripe.PaymentIntent.create(
            amount=int(amount_to_withdraw * 100),  # Convert dollars to cents
            currency='usd',
            payment_method=request.POST['payment_method'],
            confirm=True,
        )

        # Record the payment in the database
        payment = Payment.objects.create(
            user=request.user,
            amount=amount_to_withdraw,
            status="completed",
        )

        # Reset points after withdrawal
        reward.points = 0
        reward.save()

        return redirect('payment_success')

    return render(request, 'withdraw_rewards.html', {'amount': amount_to_withdraw})

# Payment Success View
def payment_success(request):
    return render(request, 'payment_success.html')

# User Profile View
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required

@login_required
def profile(request, user_id):
    user_profile = get_object_or_404(User, id=user_id)
    # Assuming you're also showing posts by this user or similar
    posts = user_profile.post_set.all()  # Adjust if using a related_name

    return render(request, 'profile.html', {
        'user_profile': user_profile,
        'posts': posts,
    })

# Post Detail View
#def post_detail(request, post_id):
 #   post = get_object_or_404(Post, id=post_id)
  #  has_liked = post.likes.filter(user=request.user).exists()  # Check if the user has liked the post
   # return render(request, 'post_detail.html', {'post': post, 'has_liked': has_liked})
from django.shortcuts import render, get_object_or_404
from .models import Post

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)

    # Default to False
    has_liked = False

    # Only check if user is authenticated
    if request.user.is_authenticated:
        has_liked = post.likes.filter(user=request.user).exists()

    return render(request, 'post_detail.html', {
        'post': post,
        'has_liked': has_liked,
    })

# Post List View
def post_list(request):
    posts = Post.objects.all()  # Fetch all posts from the database
    return render(request, 'post_list.html', {'posts': posts})

##########################

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Post, Like, Comment, Category
from .forms import BasicPostForm, MediaPostForm

# Like Post View
@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Check if the user has already liked the post
    if not post.likes.filter(user=request.user).exists():
        Like.objects.create(post=post, user=request.user)
    
    return redirect('post_detail', post_id=post.id)

# Unlike Post View
@login_required
def unlike_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Find the like object and delete it if it exists
    like = post.likes.filter(user=request.user).first()
    if like:
        like.delete()
    
    return redirect('post_detail', post_id=post.id)

# Comment on Post View
@login_required
def comment_on_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        
        # Check if content is empty
        if not content:
            messages.error(request, "Comment content cannot be empty.")
            return redirect('post_detail', post_id=post.id)
        
        # Create the comment
        Comment.objects.create(post=post, user=request.user, content=content)
        
        messages.success(request, "Your comment has been posted successfully.")
    
    return redirect('post_detail', post_id=post.id)

# Edit Post View
@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('post_detail', post_id=post.id)
    
    if request.method == 'POST':
        form = BasicPostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated successfully!')
            return redirect('post_detail', post_id=post.id)
    else:
        form = BasicPostForm(instance=post)

    return render(request, 'edit_post.html', {'form': form, 'post': post})

# Delete Post View
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('home')
    
    return render(request, 'delete_post.html', {'post': post})

# Create Post View (Basic & Media)
@login_required
def create_post(request):
    categories = Category.objects.all()  # Get all categories
    basic_form = BasicPostForm()
    media_form = MediaPostForm()

    if request.method == 'POST':
        post_type = request.POST.get('post_type')

        if post_type == 'basic':
            basic_form = BasicPostForm(request.POST)
            if basic_form.is_valid():
                post = basic_form.save(commit=False)
                post.author = request.user  # Assign the user as the author
                post.save()  # Save the post
                return redirect('home')

        elif post_type == 'media':
            media_form = MediaPostForm(request.POST, request.FILES)
            if media_form.is_valid():
                post = media_form.save(commit=False)
                post.author = request.user  # Assign the user as the author
                post.save()  # Save the post
                return redirect('home')

    return render(request, 'create_post.html', {
        'basic_form': basic_form,
        'media_form': media_form,
        'categories': categories,
    })

# Category Pages View
def category_page(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    posts = Post.objects.filter(category=category)
    return render(request, 'category_page.html', {'category': category, 'posts': posts})

# Category List View
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'category_list.html', {'categories': categories})

# Search Posts View
def search_posts(request):
    query = request.GET.get('q', '')
    posts = Post.objects.filter(
        Q(title__icontains=query) | Q(content__icontains=query)
    )
    return render(request, 'search_results.html', {'posts': posts, 'query': query})

# User Signup View
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .models import Post  # Make sure to import your Post model

@login_required
def profile(request, user_id):
    user_profile = get_object_or_404(User, id=user_id)

    # Get posts manually using filter
    posts = Post.objects.filter(author=user_profile)

    return render(request, 'profile.html', {
        'user_profile': user_profile,
        'posts': posts,
    })


# Post Detail View
#def post_detail(request, post_id):
  #  post = get_object_or_404(Post, id=post_id)
#    has_liked = post.likes.filter(user=request.user).exists()  # Check if the user has liked the post
 #   return render(request, 'post_detail.html', {'post': post, 'has_liked': has_liked})
from django.shortcuts import render, get_object_or_404
from .models import Post

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)

    # Default to False
    has_liked = False

    # Only check if user is authenticated
    if request.user.is_authenticated:
        has_liked = post.likes.filter(user=request.user).exists()

    return render(request, 'post_detail.html', {
        'post': post,
        'has_liked': has_liked,
    })

# Post List View
def post_list(request):
    posts = Post.objects.all()  # Fetch all posts from the database
    return render(request, 'post_list.html', {'posts': posts})

#############################################

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import BasicPostForm, MediaPostForm
from .models import Category

@login_required
def create_media_post(request):
    categories = Category.objects.all()  # Get all categories (optional)
    media_form = MediaPostForm()  # Initialize the media form

    if request.method == 'POST':
        # Handle form submission
        media_form = MediaPostForm(request.POST, request.FILES)
        if media_form.is_valid():
            post = media_form.save(commit=False)
            post.author = request.user  # Assign the current user as the author
            post.save()  # Save the post to the database
            return redirect('home')  # Redirect to home page after saving

    return render(request, 'create_media_post.html', {
        'media_form': media_form,  # Pass the media form to the template
        'categories': categories  # Optional, for category dropdown if needed
    })


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import BasicPostForm, MediaPostForm  # Ensure both forms are imported
from .models import Category  # Assuming you are using categories

@login_required
def create_basic_post(request):
    categories = Category.objects.all() 
    basic_form = BasicPostForm()

    if request.method == 'POST':
        form = BasicPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_list')  # Redirect after saving
    else:
        form = BasicPostForm()

    return render(request, 'create_basic_post.html', {
        'form': form,
        'basic_form': basic_form,
        'categories': categories
    })

#########################################################################################################
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import Post, SiteSettings

User = get_user_model()

@login_required
def admin_dashboard(request):
    pending_posts = Post.objects.filter(status=Post.PENDING)
    users = User.objects.all()
    settings = SiteSettings.objects.first()
    
    return render(request, 'admin_dashboard.html', {
        'pending_posts': pending_posts,
        'users': users,
        'settings': settings
    })

@login_required
def approve_post(request, post_id):
    post = Post.objects.get(id=post_id)
    post.status = Post.APPROVED
    post.save()
    return redirect('admin_dashboard')

@login_required
def reject_post(request, post_id):
    post = Post.objects.get(id=post_id)
    post.status = Post.REJECTED
    post.save()
    return redirect('admin_dashboard')

@login_required
def activate_user(request, user_id):
    user = User.objects.get(id=user_id)
    user.is_active = True
    user.save()
    return redirect('admin_dashboard')

@login_required
def promote_user(request, user_id):
    user = User.objects.get(id=user_id)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    return redirect('admin_dashboard')

@login_required
def toggle_moderation(request):
    settings = SiteSettings.objects.first()
    settings.moderation_enabled = not settings.moderation_enabled
    settings.save()
    return redirect('admin_dashboard')
################################################
#user.is_active = False  # requires admin to activate
# Only show approved posts
def post_list(request):
    return render(request, 'post_list.html', {
        'posts': Post.objects.filter(status='approved')
    })
###########################################################################

from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('home')  # or 'login', or a custom page
#############################################################################

# myapp/views.py
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views import View
from django.http import HttpResponseRedirect

class CustomLogoutView(View):
    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect('login')  # or wherever you want to send them
############################################################################

def home(request):
    all_posts = Post.objects.all().order_by('-created_at')
    featured_posts = all_posts[:3]  # Top 3 as featured
    latest_posts = all_posts[3:]   # The rest

    return render(request, 'home.html', {
        'featured_posts': featured_posts,
        'posts': latest_posts,
    })
##################################################################################

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from .forms import SignUpForm

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST, request.FILES)  # Remember to include request.FILES for handling image uploads
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirect to login page after successful sign-up
    else:
        form = SignUpForm()

    return render(request, 'signup.html', {'form': form})

# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Wallet, RewardTransaction
from django.http import JsonResponse

@login_required
def wallet_view(request):
    """View to display the user's wallet balance and transaction history"""
    wallet, created = Wallet.objects.get_or_create(user=request.user)

    transactions = RewardTransaction.objects.filter(wallet=wallet).order_by('-created_at')

    return render(request, 'wallet/wallet.html', {
        'wallet': wallet,
        'transactions': transactions
    })

@login_required
def add_points(request):
    """View to add points to the user's wallet"""
    if request.method == 'POST':
        points = request.POST.get('points')
        try:
            points = float(points)
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            wallet.add_points(points)

            # Create a record of the transaction
            RewardTransaction.objects.create(
                wallet=wallet,
                points=points,
                transaction_type='add',
                description=f'Added {points} points'
            )
            
            messages.success(request, f'You have successfully added {points} points!')
        except ValueError:
            messages.error(request, 'Invalid points entered.')
    return redirect('wallet_view')

@login_required
def deduct_points(request):
    """View to deduct points from the user's wallet"""
    if request.method == 'POST':
        points = request.POST.get('points')
        try:
            points = float(points)
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            wallet.deduct_points(points)

            # Create a record of the transaction
            RewardTransaction.objects.create(
                wallet=wallet,
                points=points,
                transaction_type='deduct',
                description=f'Deducted {points} points'
            )
            
            messages.success(request, f'You have successfully deducted {points} points!')
        except ValueError:
            messages.error(request, 'Invalid points entered.')
        except Exception as e:
            messages.error(request, str(e))

    return redirect('wallet_view')
# admin.py
#from django.contrib import admin
#from .models import Wallet, RewardTransaction

#@admin.register(Wallet)
#class WalletAdmin(admin.ModelAdmin):
#    list_display = ('user', 'balance')

#@admin.register(RewardTransaction)
#class RewardTransactionAdmin(admin.ModelAdmin):
#    list_display = ('wallet', 'transaction_type', 'points', 'created_at', 'description')

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Wallet, RewardTransaction, Task
from django.contrib.auth.models import User

# Check if the user is an admin
def is_admin(user):
    return user.is_superuser

# Admin: Send Rewards or Money to Users' Wallet
@user_passes_test(is_admin)
@login_required
def send_rewards(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        points = float(request.POST.get('points'))
        user = get_object_or_404(User, id=user_id)
        
        wallet, created = Wallet.objects.get_or_create(user=user)
        
        # Add points to the user's wallet
        wallet.add_points(points)
        
        # Log the transaction
        RewardTransaction.objects.create(
            wallet=wallet,
            points=points,
            transaction_type='add',
            description=f'Admin sent {points} points to {user.username}'
        )
        
        messages.success(request, f'Successfully sent {points} points to {user.username}!')
        return redirect('admin_dashboard')  # Redirect to admin dashboard or relevant page

    users = User.objects.all()
    return render(request, 'send_rewards.html', {'users': users})


# User completes a task
@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    # Check if task is active
    if task.is_active:
        # Get or create the user's wallet
        wallet, created = Wallet.objects.get_or_create(user=request.user)

        # Add points to the wallet
        wallet.add_points(task.points)

        # Log the transaction
        RewardTransaction.objects.create(
            wallet=wallet,
            points=task.points,
            transaction_type='add',
            description=f'Earned {task.points} points for completing task: {task.title}'
        )

        messages.success(request, f'You earned {task.points} points for completing the task: {task.title}')
    else:
        messages.error(request, 'This task is no longer active.')

    return redirect('task_list')  # Redirect to task list or homepage

# Display tasks for users to complete
@login_required
def task_list(request):
    tasks = Task.objects.filter(is_active=True)  # Only show active tasks
    return render(request, 'task_list.html', {'tasks': tasks})

from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Like, Comment
from .models import Wallet

def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user

    # Check if user already liked the post
    if Like.objects.filter(user=user, post=post).exists():
        return redirect('post_detail', post_id=post.id)

    # Create like
    like = Like(user=user, post=post)
    like.save()

    # Reward the post author with points
    post_author_wallet, created = Wallet.objects.get_or_create(user=post.author)
    post_author_wallet.add_points(5)  # Reward 5 points for a like

    return redirect('post_detail', post_id=post.id)

def comment_on_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user

    if request.method == 'POST':
        content = request.POST.get('content')

        # Create comment
        comment = Comment(user=user, post=post, content=content)
        comment.save()

        # Reward the post author with points for the comment
        post_author_wallet, created = Wallet.objects.get_or_create(user=post.author)
        post_author_wallet.add_points(10)  # Reward 10 points for a comment

    return redirect('post_detail', post_id=post.id)

@login_required
def request_withdrawal(request):
    if request.method == 'POST':
        amount = float(request.POST.get('amount'))

        # Get the user's wallet
        wallet = Wallet.objects.get(user=request.user)

        # Check if the user has enough balance
        if wallet.balance >= amount:
            # Create withdrawal request
            WithdrawalRequest.objects.create(user=request.user, amount=amount)
            messages.success(request, 'Your withdrawal request has been submitted.')
        else:
            messages.error(request, 'Insufficient balance for withdrawal.')

    return render(request, 'request_withdrawal.html')

@user_passes_test(is_admin)
@login_required
def manage_withdrawals(request):
    withdrawal_requests = WithdrawalRequest.objects.filter(status='pending')
    return render(request, 'manage_withdrawals.html', {'requests': withdrawal_requests})

@user_passes_test(is_admin)
@login_required
def approve_withdrawal(request, withdrawal_id):
    withdrawal_request = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
    
    # Deduct from user's wallet
    wallet = Wallet.objects.get(user=withdrawal_request.user)
    wallet.deduct_points(withdrawal_request.amount)
    
    # Approve the withdrawal
    withdrawal_request.status = 'approved'
    withdrawal_request.save()
    
    messages.success(request, f"Withdrawal of {withdrawal_request.amount} approved.")
    return redirect('manage_withdrawals')

@user_passes_test(is_admin)
@login_required
def reject_withdrawal(request, withdrawal_id):
    withdrawal_request = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
    
    # Reject the withdrawal
    withdrawal_request.status = 'rejected'
    withdrawal_request.save()
    
    messages.success(request, f"Withdrawal of {withdrawal_request.amount} rejected.")
    return redirect('manage_withdrawals')

from django.shortcuts import render
from .models import Wallet

def wallet_overview(request):
    # Assuming the user has a wallet, we get it here
    wallet = Wallet.objects.get(user=request.user)
    
    return render(request, 'wallet_overview.html', {'wallet': wallet})
#########################################################################
# views.py

from django.shortcuts import render

def user_management(request):
    # Your logic for user management goes here
    return render(request, 'user_management.html')



from django.contrib.auth.models import User
from myapp.models import Wallet
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def wallet(request):
    for user in User.objects.all():
          Wallet.objects.get_or_create(user=user)
    return render(request, 'wallet.html')

@login_required
def wallet_overview(request):
    return render(request, 'wallet_overview.html')

@login_required
def withdraw_rewards(request):
    return render(request, 'withdraw_rewards.html')

def wallet_overview(request):
    user = request.user
    transactions = Transaction.objects.filter(user=user)
    return render(request, 'wallet_overview.html', {'user': user, 'transactions': transactions})

#####################################################

from django.shortcuts import get_object_or_404, redirect
from .models import Comment

@login_required
def reply_comment(request, comment_id):
    if request.method == 'POST':
        content = request.POST.get('content')
        parent_comment = get_object_or_404(Comment, id=comment_id)
        
        Comment.objects.create(
            post=parent_comment.post,
            user=request.user,
            content=content,
            parent=parent_comment  # This now works
        )
        return redirect('post_detail', post_id=parent_comment.post.id)
