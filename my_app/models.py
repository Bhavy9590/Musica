from django.db import models
from django.contrib.auth.models import AbstractUser
from mutagen.mp3 import MP3
import os

class Genre(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='genres/')
    created_at = models.DateTimeField(auto_now_add=True, editable=True)  # Warning: Uncommon practice
    updated_at = models.DateTimeField(auto_now=True, editable=True)

    def __str__(self):
        return self.name
class Country(models.Model):
    name = models.CharField(max_length=100,unique=True)
    phone_code = models.CharField(max_length=100,unique=False)
    code = models.CharField(max_length=100,unique=True)

    def __str__(self):
        
        return self.name

class CustomUser(AbstractUser):
    type = models.IntegerField(default=0)
    birth_date = models.DateField(null=True, blank=True)
    country_id = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(unique=False)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    remember_token = models.CharField(max_length=200, blank=True, null=True,unique=True)
    refresh_token = models.CharField(max_length=200,null=True, blank=True,unique=True)
    otp_number = models.IntegerField(blank=True, null=True)
    fcm_id = models.TextField(null=True, blank=True)
    timezone = models.CharField(max_length=100, null=True, blank=True)  # Timezone of the user
    device_type = models.CharField(max_length=50, null=True, blank=True)
    image = models.ImageField(upload_to='users/profile/',default=None)
    genres= models.ManyToManyField(Genre ,related_name='users')
    # login_status = models.BooleanField(default=False)

    # Ensure related_name is set to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customer',  # Set a unique reverse name
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='permission',  # Set a unique reverse name
        blank=True
    )

    def __str__(self):
        return self.username


class Timezone(models.Model):
    zone_id = models.AutoField(primary_key=True)  # Unique ID for the timezone
    country_code = models.CharField(max_length=2)  # ISO 3166-1 alpha-2 code
    zone_name = models.CharField(max_length=100)  # Timezone name (e.g., Asia/Kolkata)

    def __str__(self):
        return self.zone_name

class Artist(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='artists/')
    created_at = models.DateTimeField(auto_now_add=True, editable=True)  # Warning: Uncommon practice
    updated_at = models.DateTimeField(auto_now=True, editable=True)

    # def __str__(self):
    #     return self.name

    def save(self, *args, **kwargs):
        # Check if the object already exists
        if self.pk:
            old_image = Artist.objects.get(pk=self.pk).image
            if old_image and old_image != self.image:  # If a new image is uploaded
                if os.path.isfile(old_image.path):  # Check if the file exists
                    os.remove(old_image.path)  # Delete the old file
        super().save(*args, **kwargs)

class Album(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='albums/')
    created_at = models.DateTimeField(auto_now_add=True, editable=True)  # Warning: Uncommon practice
    updated_at = models.DateTimeField(auto_now=True, editable=True)

    def __str__(self):
        return self.name

class Mixes(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='mixes/')
    created_at = models.DateTimeField(auto_now_add=True, editable=True)  # Warning: Uncommon practice
    updated_at = models.DateTimeField(auto_now=True, editable=True)


class Song(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='songs/images/')
    song_file = models.FileField(upload_to='songs/files/',blank=True,null=True)
    song_url = models.URLField(null=True, blank=True)  # Allow null and blank
    total_likes = models.IntegerField(default=0,blank=True, null=True)
    total_downloads=models.IntegerField(default=0,blank=True)
    total_played=models.IntegerField(default=0,blank=True)
    favourite_count=models.IntegerField(default=0,blank=True)
    playlist_count=models.IntegerField(default=0,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=True)  # Warning: Uncommon practice
    updated_at = models.DateTimeField(auto_now=True, editable=True)
    duration = models.CharField(max_length=255, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Calculate and save duration if song_file is provided
        if self.song_url and not self.duration:
            try:
                audio = MP3(self.song_url.path)
                self.duration = audio.info.length  # Duration in seconds
            except Exception as e:
                print(f"Error calculating duration: {e}")
        super().save(*args, **kwargs)

class video_category(models.Model):
    category_name=models.CharField(max_length=255,null=False,blank=False)
    category_image=models.ImageField(upload_to='videos/category/images',null=False,blank=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)


class Videos(models.Model):
    videos_name = models.CharField(max_length=255, null=False, blank=False)
    videos_image = models.ImageField(upload_to='videos/images', null=False, blank=False)
    videos_url = models.URLField(max_length=255, null=True, blank=True)  # Optional for local uploads
    videos_file = models.FileField(upload_to='videos/file', null=True, blank=True)
    duration = models.CharField(max_length=250,blank=True, null=True)  # Store duration as seconds
    videos_artist_name = models.CharField(max_length=255)
    videos_description = models.TextField()  # Use TextField for longer descriptions
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Fix: Updates on modification

    def __str__(self):
        return self.videos_name

class Live_Videos(models.Model):
    videos_name=models.CharField(max_length=255,null=False,blank=False)
    videos_image=models.ImageField(upload_to='videos/images',null=False,blank=False)
    videos_link=models.URLField(max_length=255,null=False,blank=False)
    videos_artist_name=models.CharField(max_length=255)
    videos_description=models.CharField(max_length=255)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)

class SongLike(models.Model):
    fk_user=models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    fk_song=models.ForeignKey(Song,on_delete=models.CASCADE)
    is_liked=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)

class SongCategory(models.Model):
    songs = models.ForeignKey(Song,on_delete=models.CASCADE, null=True, blank=True,unique=False)
    artists = models.ForeignKey(Artist,on_delete=models.CASCADE,null=True,blank=True,unique=False)
    albums = models.ForeignKey(Album,on_delete=models.CASCADE,null=True,blank=True,unique=False)
    fk_genre = models.ForeignKey(Genre, on_delete=models.CASCADE,null=True,blank=True,unique=False)
    fk_mixes = models.ForeignKey(Mixes, on_delete=models.CASCADE,null=True,blank=True,unique=False)
    fk_video=models.ForeignKey(Videos,on_delete=models.CASCADE,null=True,blank=True,unique=False)
    fk_video_category=models.ForeignKey(video_category,on_delete=models.CASCADE,null=True,blank=True,unique=False)


class SocialMedia(models.Model):
    social_media_name=models.CharField(max_length=150,unique=True,blank=True)
    social_media_link = models.URLField(max_length=250,unique=True)

class ShareMyApp(models.Model):
    shareapp_name = models.CharField(max_length=255,blank=True,unique=True)
    shareapp_andriod_link = models.URLField(max_length=255)
    shareapp_ios_link = models.URLField(max_length=255)

class LiveRadio(models.Model):
    liveradio_name = models.CharField(max_length=255, blank=True)
    liveradio_image = models.ImageField(upload_to='live_radio/', max_length=255)
    liveradio_link = models.URLField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class RecentPlayed(models.Model):
    fk_user= models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=False)
    fk_song=models.ForeignKey(Song,on_delete=models.CASCADE,null=False)
    #fk_artist=models.ForeignKey(Artist,on_delete=models.CASCADE,null=True)

class Playlist(models.Model):
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=150,default='', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Playlist_Songs(models.Model):
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    playlist_id = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    song_id = models.ForeignKey(Song, on_delete=models.CASCADE)
    fk_album = models.ForeignKey(Album,on_delete=models.CASCADE,blank=True,null=True,default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



class FavouriteSong(models.Model):
    fk_user= models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    fk_song=models.ForeignKey(Song,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Downloaded_Songs(models.Model):
    fk_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null = True)
    fk_song = models.ForeignKey(Song, on_delete=models.CASCADE, null = True)
    is_downloaded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class TermsOfService(models.Model):
    title = models.CharField(max_length=255,blank=False,null=False)
    description = models.CharField(max_length=255,blank=False,null=False)

class PrivacyPolicy(models.Model):
    title = models.CharField(max_length=255,blank=False,null=False)
    description = models.CharField(max_length=255,blank=False,null=False)

class Introduction_Slider(models.Model):
    image = models.ImageField(upload_to='introduction_slider/images/',verbose_name="Image")
    text = models.TextField(null=True,blank=True)
    position = models.IntegerField(default=None, blank=True, null=True)
    status = models.IntegerField(default=0, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Set the default value for position to the id if it's not already set
        if self.position is None:
            self.position = self.id
        super().save(*args, **kwargs)

class RecommendedTracks(models.Model):
    fk_song=models.ForeignKey(Song,on_delete=models.CASCADE)
    # fk_artist=models.ForeignKey(Artist,on_delete=models.CASCADE)

class TrendingArtists(models.Model):
    fk_artist=models.ForeignKey(Artist,on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=1)  # Position field

    class Meta:
        ordering = ['position'] 
   
class TrendingAlbums(models.Model):
    fk_album=models.ForeignKey(Album,on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=1)  # Position field

    class Meta:
        ordering = ['position']
class TrendingGenres(models.Model):
    fk_genre=models.ForeignKey(Genre,on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=1)  # Position field

class TrendingMixes(models.Model):  
    fk_mixes=models.ForeignKey(Mixes,on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=1)  # Position field
    class Meta:
        ordering = ['position']

class TrendingTracks(models.Model):
    fk_tracks=models.ForeignKey(Song,on_delete=models.CASCADE)
    position = models.PositiveIntegerField(blank=True,null=True)  # Position field
    
class DefaultPlaylist(models.Model):
    name=models.CharField(max_length=255,blank=False,null=False)
    image=models.ImageField(upload_to='playlists',null=False,blank=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)

    