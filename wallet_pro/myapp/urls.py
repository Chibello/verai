from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.contrib.auth.views import LogoutView
from .views import CustomLogoutView
from django.conf.urls.static import static
#from livereload import Server


urlpatterns = [
    path('', views.home, name='home'),
    #path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('like/<int:post_id>/', views.like_post, name='like_post'),
    path('comment/<int:post_id>/', views.comment_on_post, name='comment_on_post'),
    path('category/<int:category_id>/', views.category_page, name='category_page'),
    path('categories/', views.category_list, name='category_list'),
    path('search/', views.search_posts, name='search_posts'),
    path('post/edit/<int:post_id>/', views.edit_post, name='edit_post'),
    path('post/delete/<int:post_id>/', views.delete_post, name='delete_post'),
    path('post/create/', views.create_post, name='create_post'),  # Fixed the post creation route
    path('post/create/basic/', views.create_basic_post, name='create_basic_post'),
    path('post/create/media/', views.create_media_post, name='create_media_post'),
    # 
    path('logout/', CustomLogoutView.as_view(), name='logout'),

    path('create-media-post/', views.create_media_post, name='create_media_post'),
    path('logout/', views.logout_view, name='logout'),


    path('logout/', LogoutView.as_view(), name='logout'),

    path('post/create/basic/', views.create_basic_post, name='create_basic_post'),
    path('post/create/media/', views.create_media_post, name='create_media_post'),
    path('', views.home, name='home'),
    # ################################################################################################
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('approve-post/<int:post_id>/', views.approve_post, name='approve_post'),
    path('reject-post/<int:post_id>/', views.reject_post, name='reject_post'),
    path('activate-user/<int:user_id>/', views.activate_user, name='activate_user'),
    path('promote-user/<int:user_id>/', views.promote_user, name='promote_user'),
    path('toggle-moderation/', views.toggle_moderation, name='toggle_moderation'),

    #####################################################################################################
    
    # Authentication routes
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('wallet/', views.wallet_view, name='wallet_view'),
    path('wallet/add/', views.add_points, name='add_points'),
    path('wallet/deduct/', views.deduct_points, name='deduct_points'),
    path('tasks/', views.task_list, name='task_list'),
    path('complete-task/<int:task_id>/', views.complete_task, name='complete_task'),
    path('admin/send-rewards/', views.send_rewards, name='send_rewards'),
    # Post list route
    path('posts/', views.post_list, name='post_list'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('post/<int:post_id>/comment/', views.comment_on_post, name='comment_on_post'),

    # Wallet and rewards views
    path('wallet/', views.wallet_overview, name='wallet_overview'),
    #path('wallet/', views.wallet_view, name='wallet_overview'),

    path('request-withdrawal/', views.request_withdrawal, name='request_withdrawal'),
    path('withdraw-rewards/', views.withdraw_rewards, name='withdraw_rewards'),
    path('wallet-overview/', views.wallet_overview, name='wallet_overview'),
###########
    #path('process-withdrawal/', views.process_withdrawal, name='process_withdrawal'),
    # Admin views
    path('admin/manage-withdrawals/', views.manage_withdrawals, name='manage_withdrawals'),
    path('admin/approve-withdrawal/<int:withdrawal_id>/', views.approve_withdrawal, name='approve_withdrawal'),
    path('admin/reject-withdrawal/<int:withdrawal_id>/', views.reject_withdrawal, name='reject_withdrawal'),
    
    # Admin user management
    path('admin/user-management/', views.user_management, name='user_management'),
    
     #path('profile/<int:user_id>/', views.profile, name='view_profile'),
    
    # Edit profile
    #path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # View posts for a specific user
    #path('profile/<int:user_id>/posts/', views.user_posts, name='user_posts'),

    
    #path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('like_post/<int:post_id>/', views.like_post, name='like_post'),
    path('like_comment/<int:comment_id>/', views.like_comment, name='like_comment'),
    path('reply_comment/<int:comment_id>/', views.reply_comment, name='reply_comment'),
    #path('profile/<int:user_id>/', views.profile, name='profile'),
    path('profile/<int:user_id>/', views.profile, name='profile'),
    #path('profile/<int:user_id>/', views.profile, name='profile'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#################################################
#server = Server()
'''

# Create the server instance
server = Server()

# Watch the templates folder for changes (adjust the path based on your structure)
server.watch('myapptemplates/**/*.html')  # Watches all .html files in the templates folder

# Watch the static folder for changes (adjust the path based on your structure)
server.watch('myapp/static/**/*.*')  # Watches all files in the static folder (CSS, JS, Images)

# Start the server
server.serve()


#server.serve()
'''