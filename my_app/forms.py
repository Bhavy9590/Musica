from django import forms
from .models import *


class CustomHtmlUserCreationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'password']


class ArtistForm(forms.ModelForm):
    class Meta:
        model = Artist
        fields = ['name', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['name', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class GenreForm(forms.ModelForm):
    class Meta:
        model = Genre
        fields = ['name', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = ['name', 'image', 'song_url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter song name'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'song_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter song URL'}),

        }

# class VideoForm(forms.ModelForm):
#     class Meta:
#         model=Videos
#         fields=['videos_name','videos_image','videos_url','videos_file','videos_artist_name','videos_description']
#         widgets = {
#             'videos_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter video name'}),
#             'videos_image': forms.FileInput(attrs={'class': 'form-control'}),
#             'song_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter song URL'}),

#         }
class AssignArtist(forms.Form):
    artists = forms.ModelMultipleChoiceField(
        queryset=Artist.objects.all(), 
        required=False, # Fetch all artists from the database
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',  # Add CSS class for Bootstrap styling
            'size': 5  # Display 5 rows; adjust as needed
        }),
        label="Select Artists",  # Label for the dropdown
    )

    songs = forms.ModelMultipleChoiceField(
        queryset=Song.objects.all(), 
        required=False, # Fetch all artists from the database
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',  # Add CSS class for Bootstrap styling
            'size': 5  # Display 5 rows; adjust as needed
        }),
        label="Select Artists",  # Label for the dropdown
    )

    albums = forms.ModelMultipleChoiceField(
        queryset=Album.objects.all(),
        required=False,  # Fetch all artists from the database
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',  # Add CSS class for Bootstrap styling
            'size': 5  # Display 5 rows; adjust as needed
        }),
        label="Select albums",  # Label for the dropdown
    )

    genres= forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        required=False,  # Fetch all artists from the database
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',  # Add CSS class for Bootstrap styling
            'size': 5  # Display 5 rows; adjust as needed
        }),
        label="Select genres",  # Label for the dropdown
    )
    mixes= forms.ModelMultipleChoiceField(
        queryset=Mixes.objects.all(),
        required=False,  # Fetch all artists from the database
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',  # Add CSS class for Bootstrap styling
            'size': 5  # Display 5 rows; adjust as needed
        }),
        label="Select Mixes",  # Label for the dropdown
    )
    assign_trending = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-control'}),
        label='Assign song to trending'
    )
    recommended_tracks=forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-control'}),
        label="assign song to receommended tracks"
    )

class AssignVideos(forms.Form):
    videos_category = forms.ModelMultipleChoiceField(
        queryset=video_category.objects.all(), 
        required=False, # Fetch all artists from the database
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',  # Add CSS class for Bootstrap styling
            'size': 5  # Display 5 rows; adjust as needed
        }),
        label="Select video category",  # Label for the dropdown
    )

    video = forms.ModelMultipleChoiceField(
        queryset=Videos.objects.all(), 
        required=False, # Fetch all artists from the database
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',  # Add CSS class for Bootstrap styling
            'size': 5  # Display 5 rows; adjust as needed
        }),
        label="Select video",  # Label for the dropdown
    )


class SocialMediaForm(forms.ModelForm):
    class Meta:
        model = SocialMedia
        fields =[ "social_media_name","social_media_link"]
        widgets = {
            'social_media_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter social media name'}),
            'social_media_link': forms.URLInput(attrs={'class': 'form-control','placeholder':'enter social media link'})
        }

class ShareMyAppForm(forms.ModelForm):
    class Meta:
        model = ShareMyApp
        fields = ["shareapp_name","shareapp_andriod_link","shareapp_ios_link"]
        widgets = {
            'shareapp_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter app name'}),
            'shareapp_andriod_link': forms.URLInput(attrs={'class': 'form-control','placeholder':'enter andriod link'}),
            'shareapp_ios_link': forms.URLInput(attrs={'class':'form-control','placeholder':'enter ios link'})
        }

class MixesForm(forms.ModelForm):
    
    class Meta:
        model= Mixes
        fields=["name",'image']
        widgets={
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class TermsOfServiceForm(forms.ModelForm):
    class Meta:
        model = TermsOfService
        fields = ['title', 'description']
        widgets={
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }

class PrivacyPolicyForm(forms.ModelForm):
    class Meta:
        model = PrivacyPolicy
        fields = ['title', 'description']
        widgets={
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }



class LiveRadioForm(forms.ModelForm):
    class Meta:
        model = LiveRadio
        fields = ["liveradio_name","liveradio_image","liveradio_link"]
        widgets = {
            'liveradio_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter live radio name'}),
            'liveradio_link': forms.URLInput(attrs={'class': 'form-control','placeholder':'enter live radio link'}),
            'liveradio_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

# class VideosForm(forms.ModelForm):
#     class Meta:
#         model = Videos
#         fields = ["videos_name","videos_image","videos_link","videos_artist_name","videos_description"]
#         widgets = {
#             'videos_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter videos name'}),
#             'videos_image': forms.URLInput(attrs={'class': 'form-control','placeholder':'enter videos link'}),
#             'videos_link': forms.FileInput(attrs={'class': 'form-control'}),
#             'videos_artist_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter artist name'}),
#             'videos_description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter videos description'}),
            # 'created_at': forms.DateTimeInput(attrs={'class': 'form-control', 'placeholder': 'Enter created at'}),

# class TrendingArtistsForm(forms.ModelForm):
#     class Meta:
#         model = TrendingArtists
#         fields = ["trending_artists_name","trending_artists_image"]
#         widgets = {
#             'trending_artists_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter trending artist name'}),
#             'trending_artists_image': forms.FileInput(attrs={'class': 'form-control'}),
#         }