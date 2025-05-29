'''
from django import forms
from .models import Post

# Form for creating a basic post (without any media)
class BasicPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'category', 'image']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }

# Form for creating a post with media (image, video URL, video file, reel)
class MediaPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'category', 'image', 'video_url', 'video_file', 'reel']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }

    # Optional fields
    #image = forms.ImageField(required=False)
    #video_url = forms.URLField(required=False)
    #video_file = forms.FileField(required=False)
    #reel = forms.FileField(required=False)
'''
# forms.py
from django import forms
from .models import Post, Category

class BasicPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'category', 'image']

# forms.py
class MediaPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'video_file',  'category']
##########################################################################################################

from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class SignUpForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'image']

    password = forms.CharField(widget=forms.PasswordInput)
    
    # Image input field for profile picture
    image = forms.ImageField(required=False)

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()

        # Save user profile image if provided
        if self.cleaned_data.get('image'):
            profile = UserProfile.objects.create(user=user, image=self.cleaned_data.get('image'))
        return user
