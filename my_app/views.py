from datetime import datetime
import os
from django.db.models import Q
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate,login as auth_login,logout
from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from my_app.default_variables import *
from mutagen.mp3 import MP3
from .utils import *
from .models import *
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.core.files.storage import FileSystemStorage
# from .forms import LiveRadioForm
from django.core.paginator import Paginator
from moviepy.editor import VideoFileClip
import requests
from io import BytesIO


# Create your views here.
def register(request):
    if request.method == "POST":
        form = CustomHtmlUserCreationForm(request.POST)
        
        # Check if form is valid
        if form.is_valid():
            username = form.cleaned_data['username']
            if CustomUser.objects.filter(username=username).exists():
                form.add_error('username', 'This username is already taken.')
            else:
            # Get the user instance without saving it to the database yet
                user = form.save(commit=False)
            
            # Manually hash the password before saving it
            hashed_password = make_password(form.cleaned_data['password'])  # Hash the password
            user.password = hashed_password  # Set the hashed password to the user instance
            
            # Save the user instance to the database
            user.save()
            
            # Show success message
            messages.success(request, "Registration successful. You can now log in.")
            return redirect('login')  # Redirect to login page
        else:
            # If form is invalid, show error messages
            messages.error(request, "There was an error with your registration.")
    
    else:
        form = CustomHtmlUserCreationForm()  # Empty form on GET request
    
    return render(request, 'main_app/auth-register-basic.html', {'form': form})

def login(request):
    if request.method == "POST":
        username = request.POST.get('username') 
        password = request.POST.get('password')
        
        # Authenticate the user (Django's authenticate function automatically checks the password securely)
        user = authenticate(request, username=username, password=password)

        if user is not None:  # If user is authenticated successfully
            auth_login(request, user)  # Log the user in
            return redirect('dashboard')  # Redirect to the dashboard
        else:
            messages.error(request, 'Invalid username or password.')  # Show error message if authentication fails
    
    return render(request, 'main_app/auth-login-basic.html')   

def logout_view(request):
    logout(request)
    return redirect('login')


def index(request):
    context = {'segment': 'index'}
    return render(request, 'main_app/index.html', context)

from django.db.models import Q

def dashboard(request):
    if request.method == 'POST':
        form = AssignArtist(request.POST)
        if form.is_valid():
            selected_artists = form.cleaned_data['artists']
            selected_songs = form.cleaned_data['songs']
            selected_albums = form.cleaned_data['albums']
            selected_genres = form.cleaned_data['genres']
            selected_mixes = form.cleaned_data['mixes']
            is_treinding=form.cleaned_data['assign_trending']
            is_recommended = form.cleaned_data['recommended_tracks']
            # Extract IDs
            artists_id = [artist.id for artist in selected_artists]
            songs_id = [song.id for song in selected_songs]
            albums_id = [album.id for album in selected_albums]
            genres_id = [genre.id for genre in selected_genres]
            mixes_id=   [mix.id for mix in selected_mixes]
            
            if is_treinding and songs_id:
                for song_id in songs_id:
                    if not TrendingTracks.objects.filter(fk_track=song_id).exists():
                        TrendingTracks.objects.create(fk_track_id=song_id)
            if  is_recommended and songs_id:
                for song_id in songs_id:
                    if not RecommendedTracks.objects.filter(fk_song=song_id).exists():
                        RecommendedTracks.objects.create(fk_song_id=song_id)

            if artists_id and songs_id and not albums_id and not genres_id:
                for artist_id in artists_id:
                    for song_id in songs_id:
                        conditions = Q()
                        if artist_id:
                            conditions &= Q(artists_id=artist_id)
                        if song_id:
                            conditions &= Q(songs_id=song_id)
                        if not SongCategory.objects.filter(conditions).exists():
                            SongCategory.objects.create(
                                songs_id=song_id,
                                artists_id=artist_id
                            )
                return redirect('dashboard')
            
            if artists_id and songs_id and albums_id and not genres_id:
                for artist_id in artists_id:
                    for song_id in songs_id:
                        for album_id in albums_id:
                            conditions = Q()
                            if artist_id:
                                conditions &= Q(artists_id=artist_id)
                            if song_id:
                                conditions &= Q(songs_id=song_id)
                            if album_id:
                                conditions &= Q(albums_id=album_id)
                            if not SongCategory.objects.filter(conditions).exists():
                                SongCategory.objects.create(
                                    songs_id=song_id,
                                    artists_id=artist_id,
                                    albums_id=album_id,
                                )
                return redirect('dashboard')

            if songs_id and albums_id and not artists_id and not genres_id:
                for song_id in songs_id:
                    for album_id in albums_id:
                        conditions = Q()
                        if song_id:
                            conditions &= Q(songs_id=song_id)
                        if album_id:
                            conditions &= Q(albums_id=album_id)
                        if not SongCategory.objects.filter(conditions).exists():
                            SongCategory.objects.create(
                                songs_id=song_id,
                                albums_id=album_id
                            )
                return redirect('dashboard')

            if songs_id and genres_id and not artists_id and not albums_id:
                for song_id in songs_id:
                    for genre_id in genres_id:
                        conditions = Q()
                        if song_id:
                            conditions &= Q(songs_id=song_id)
                        if genre_id:
                            conditions &= Q(fk_genre=genre_id)
                        if not SongCategory.objects.filter(conditions).exists():
                            SongCategory.objects.create(
                                songs_id=song_id,
                                fk_genre_id=genre_id,
                            )
                return redirect('dashboard')

            if artists_id and albums_id and genres_id and not songs_id:
                for artist_id in artists_id:
                    for album_id in albums_id:
                        for genre_id in genres_id:
                            conditions = Q()
                            if artist_id:
                                conditions &= Q(artists_id=artist_id)
                            if album_id:
                                conditions &= Q(albums_id=album_id)
                            if genre_id:
                                conditions &= Q(fk_genre=genre_id)
                            if not SongCategory.objects.filter(conditions).exists():
                                SongCategory.objects.create(
                                    artists_id=artist_id,
                                    albums_id=album_id,
                                    fk_genre_id=genre_id,
                                )
                return redirect('dashboard')

            if artists_id and genres_id and not songs_id and not albums_id:
                for artist_id in artists_id:
                    for genre_id in genres_id:
                        conditions = Q()
                        if artist_id:
                            conditions &= Q(artists_id=artist_id)
                        if genre_id:
                            conditions &= Q(fk_genre=genre_id)
                        if not SongCategory.objects.filter(conditions).exists():
                            SongCategory.objects.create(
                                artists_id=artist_id,
                                fk_genre_id=genre_id,
                            )
                return redirect('dashboard')

            if songs_id and genres_id and not artists_id and not albums_id:
                for song_id in songs_id:
                    for genre_id in genres_id:
                        conditions = Q()
                        if song_id:
                            conditions &= Q(songs_id=song_id)
                        if genre_id:
                            conditions &= Q(fk_genre=genre_id)
                        if not SongCategory.objects.filter(conditions).exists():
                            SongCategory.objects.create(
                                songs_id=song_id,
                                fk_genre_id=genre_id,
                            )
                return redirect('dashboard')
            
            if artists_id and songs_id and albums_id and genres_id:
                for artist_id in artists_id:
                    for song_id in songs_id:
                        for album_id in albums_id:
                            for genre_id in genres_id:
                                conditions = Q()
                                if artist_id:
                                    conditions &= Q(artists_id=artist_id)
                                if song_id:
                                    conditions &= Q(songs_id=song_id)
                                if album_id:
                                    conditions &= Q(albums_id=album_id)
                                if genre_id:
                                    conditions &= Q(fk_genre=genre_id)
                                if not SongCategory.objects.filter(conditions).exists():
                                    SongCategory.objects.create(
                                        songs_id=song_id,
                                        artists_id=artist_id,
                                        albums_id=album_id,
                                        fk_genre_id=genre_id,
                                    )
                return redirect('dashboard')
            
            if albums_id and genres_id and not songs_id and not artists_id and not mixes_id:
                for genre_id in genres_id:
                    for album_id in albums_id:
                        conditions = Q()
                        if albums_id:
                            conditions &= Q(albums_id=album_id)
                        if genre_id:
                            conditions &= Q(fk_genre_id=genre_id)
                        if not SongCategory.objects.filter(conditions).exists():
                            SongCategory.objects.create(
                                fk_genre_id=genre_id,
                                albums_id=album_id
                            )

            #scnario for mixes and tracks
            if mixes_id and songs_id and not albums_id and not genres_id:
                for mix_id in mixes_id:
                    for song_id in songs_id:
                        conditions = Q()
                        if mix_id:
                            conditions &= Q(fk_mixes=mix_id)
                        if song_id:
                            conditions &= Q(songs_id=song_id)
                        if not SongCategory.objects.filter(conditions).exists():
                            SongCategory.objects.create(
                                songs_id=song_id,
                                fk_mixes_id=mix_id
                            )
                return redirect('dashboard')


            # Scenario 1: Only artists and songs
            # if artists_id and songs_id and not albums_id:
            #     for artist_id in artists_id:
            #         for song_id in songs_id:
            #             conditions = Q()
            #             if artist_id:
            #                 conditions &= Q(artists_id=artist_id)
            #             if song_id:
            #                 conditions &= Q(songs_id=song_id)
            #             if not SongCategory.objects.filter(conditions).exists():
            #                 SongCategory.objects.create(
            #                     songs_id=song_id,
            #                     artists_id=artist_id
            #                 )
            #     return redirect('dashboard')

            # # Scenario 2: Artists, songs, and albums
            # if artists_id and songs_id and albums_id:
            #     for artist_id in artists_id:
            #         for song_id in songs_id:
            #             for album_id in albums_id:
            #                 conditions = Q()
            #                 if artist_id:
            #                     conditions &= Q(artists_id=artist_id)
            #                 if song_id:
            #                     conditions &= Q(songs_id=song_id)
            #                 if album_id:
            #                     conditions &= Q(albums_id=album_id)
            #                 if not SongCategory.objects.filter(conditions).exists():
            #                         SongCategory.objects.create(
            #                             songs_id=song_id,
            #                             artists_id=artist_id,
            #                             albums_id=album_id,
            #                         )
            #     return redirect('dashboard')

            # #scenario 3: Only Songs and albums
            # if albums_id and songs_id and not artists_id:
            #     for song_id in songs_id:
            #         for album_id in albums_id:
            #             conditions = Q()
            #             if song_id:
            #                 conditions &= Q(songs_id=song_id)
            #             if album_id:
            #                 conditions &= Q(albums_id=album_id)
            #             if not SongCategory.objects.filter(conditions).exists():
            #                 SongCategory.objects.create(
            #                     songs_id=song_id,
            #                     albums_id=album_id
            #                 )
            #     return redirect('dashboard')
            
            # if songs_id and genres_id and not artists_id and not albums_id:
            #     for song_id in songs_id:
            #         for genre_id in genres_id:
            #             conditions = Q()
            #             if song_id:
            #                 conditions &= Q(songs_id=song_id)
            #             if genre_id:
            #                 conditions &= Q(fk_genre=genre_id)
            #             if not SongCategory.objects.filter(conditions).exists():
            #                 SongCategory.objects.create(
            #                     songs_id=song_id,
            #                     fk_genre_id=genre_id,
            #                 )
            #     return redirect('dashboard')

            # #scenario 4: Only Albums
            # if not artists_id and not songs_id and albums_id:
            #     for album_id in albums_id:
            #         if not SongCategory.objects.filter(albums_id=album_id).exists():
            #             SongCategory.objects.create(albums_id=album_id)
            #     return redirect('dashboard')
            
            # Add more scenarios as needed

    else:
        form = AssignArtist()

    song_list=Song.objects.all()
    paginator = Paginator(song_list, 10)  
    page_number = request.GET.get('page')
    songs = paginator.get_page(page_number)
    song_count = Song.objects.count()
    song_category = SongCategory.objects.all()

    context = {
        'segment': 'dashboard',
        'form': form,
        'songs': songs ,
        'artists': Artist.objects.all(),
        'albums': Album.objects.all(),
        'genres':Genre.objects.all(),
        'mixes':Mixes.objects.all(),
        'song_count': song_count,
        'song_category': song_category,
    }


    return render(request, 'main_app/dashboard.html', context)

def users(request):
    users=CustomUser.objects.all()
    context={
        'segment':'users',
        'allusers':users,
    }
    return render(request,'main_app/users_list.html',context)

def delete_user(request,id):
    user=get_object_or_404(CustomUser,id=id)
    user.delete()
    return redirect('users')
def music(request):
    context = {
        'segment': 'music',
    }
    return render(request, 'main_app/music.html', context)

# Artists Views
def artists(request):
    artists = Artist.objects.all()
    context = {
        'segment': 'artists',
        'artists': artists
    }
    return render(request, 'main_app/artists.html', context)

def add_artist(request):
    error = ""
    form = ArtistForm()
    if request.method == "POST":
        form = ArtistForm(request.POST, request.FILES)
        name = request.POST.get('name')
        image = request.FILES.get('image')

        if image:
            original_image_name = image.name
            new_image_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{original_image_name}"
            image.name = new_image_name

        if Artist.objects.filter(name=name).exists():
            error = "Artist already exists"
        else:
            if form.is_valid():
                form.save()
                messages.success(request, "Artist added successfully.")
                return redirect('artists')

    context = {'form': form, 'errors': error}
    return render(request, 'main_app/add-artist.html', context)

def edit_artist(request, id):
    error = ""
    artist = get_object_or_404(Artist, id=id)
    form = ArtistForm(instance=artist)

    if request.method == "POST":
        form = ArtistForm(request.POST, request.FILES, instance=artist)
        name = request.POST.get('name')
        image = request.FILES.get('image')

        if Artist.objects.filter(name=name).exclude(id=id).exists():
            error = "Artist with this name already exists"
        else:
            if form.is_valid():
                if image:
                    original_image_name = image.name
                    new_image_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{original_image_name}"
                    image.name = new_image_name
                form.save()
                messages.success(request, "Artist updated successfully.")
                return redirect('artists')

    context = {'form': form, 'artist': artist, 'errors': error}
    return render(request, 'main_app/edit-artist.html', context)

def delete_artist(request, id):
    artist = get_object_or_404(Artist, id=id)
    artist.delete()
    messages.success(request, "Artist deleted successfully.")
    return redirect('artists')

# Albums Views
def albums(request):
    albums = Album.objects.all()
    context = {
        'segment': 'albums',
        'albums': albums
    }
    return render(request, 'main_app/album.html', context)

def album_details(request,id=id):
    context={
        'album_id':id,
    }
    return render(request,'main_app/album_details.html',context)

def album_details_lazy_scroll(request,id=id):
    skip = int(request.GET.get('skip', 0))
    limit = int(request.GET.get('limit', 10))
    album_id= get_object_or_404(Album,id=id)
    TrackIDS=(
        SongCategory.objects.filter(albums=album_id,songs__isnull=False)
        .values_list('songs',flat=True)
        .distinct()
    )
    data = Song.objects.filter(id__in=TrackIDS)[skip:skip + limit]
    
    song_list = []  

    for item in data:
        song_data = {
            "id": item.id,
            "name": item.name,
            "image": item.image.url if item.image else None,
            "duration":item.duration,  
            "song_url": item.song_file.url if item.song_file else item.song_url 
        }
        song_list.append(song_data)

    return JsonResponse({'data': song_list})

def album_add_song(request,id=id):
    error=""
    if request.method == "POST":
        album_id= request.POST.get('album_id')
        name = request.POST.get('name')
        image = request.FILES.get('image')  # Optional image upload
        song_url = request.POST.get('song_url')  # Song URL (if provided)
        song_file = request.FILES.get('song_file')  # Uploaded song file
        album_obj= get_object_or_404(Album,id=album_id)
        # Initialize the song object
        song = Song(
            name=name,
            image=image,
        )

        # Handle the song file upload
        if song_file:
            try:
                # Assign the song file to the model field
                song.song_file = song_file
                song.save()

                # Calculate and set the song duration
                file_path = song.song_file.path  # Get the file path
                audio = MP3(file_path)  # Use mutagen to read the MP3 file
                duration = audio.info.length  # Get the song duration

                song.duration = format_duration(duration)  # Format the duration
                song.save()  # Save the updated duration

            except Exception as e:
                print(f"Error calculating duration for uploaded file: {e}")
                song.duration = None
                messages.error(request, "Error calculating duration for uploaded file.")
                song.save()
        # Handle external song URL
        elif song_url:
            song.song_url = song_url
            try:
                if song_url.endswith('.mp3'):
                    # For MP3 URLs, fetch the content and calculate the duration
                    response = requests.get(song_url, timeout=60)
                    response.raise_for_status()  # Check if request is successful
                    audio = MP3(BytesIO(response.content))
                    duration = audio.info.length
                    song.duration = format_duration(duration)
                else:
                    # Handle non-MP3 song URLs (e.g., streaming or other formats)
                    duration = get_song_duration_from_url(song_url)
                    if duration:
                        song.duration = duration
            except Exception as e:
                print(f"Error calculating duration for song URL {song_url}: {e}")
                song.duration = None

        else:
            print("No song source provided.")

        # Save the song object with the final data (only once)
        song.save()
        LastSongObj=Song.objects.last()
    
        SongCategory.objects.create(
                albums=album_obj,
                songs=LastSongObj,
            )
        
        return redirect('album_details',id=id)

    
    context={
        'album_id':id,
        'errors': error,
    }
    return render(request,'main_app/album_song_add.html',context)

def add_album(request):
    error = ""
    form = AlbumForm()
    if request.method == "POST":
        form = AlbumForm(request.POST, request.FILES)
        name = request.POST.get('name')
        image = request.FILES.get('image')

        if image:
            original_image_name = image.name
            new_image_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{original_image_name}"
            image.name = new_image_name

        if Album.objects.filter(name=name).exists():
            error = "Album already exists"
        else:
            if form.is_valid():
                form.save()
                messages.success(request, "Album added successfully.")
                return redirect('albums')

    context = {'form': form, 'errors': error}
    return render(request, 'main_app/add-album.html', context)

def edit_album(request, id):
    error = ""
    album = get_object_or_404(Album, id=id)
    form = AlbumForm(instance=album)

    if request.method == "POST":
        form = AlbumForm(request.POST, request.FILES, instance=album)
        name = request.POST.get('name')
        image = request.FILES.get('image')

        if Album.objects.filter(name=name).exclude(id=id).exists():
            error = "Album with this name already exists"
        else:
            if form.is_valid():
                if image:
                    original_image_name = image.name
                    new_image_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{original_image_name}"
                    image.name = new_image_name
                form.save()
                messages.success(request, "Album updated successfully.")
                return redirect('albums')

    context = {'form': form, 'album': album, 'errors': error}
    return render(request, 'main_app/edit-album.html', context)

def delete_album(request, id):
    album = get_object_or_404(Album, id=id)
    album.delete()
    messages.success(request, "Album deleted successfully.")
    return redirect('albums')

# Genres Views
def genres(request):
    genres = Genre.objects.all()
    context = {
        'segment': 'genres',
        'genres': genres
    }
    return render(request, 'main_app/genres.html', context)

def add_genre(request):
    error = ""
    form = GenreForm()
    if request.method == "POST":
        form = GenreForm(request.POST, request.FILES)
        name = request.POST.get('name')

        if Genre.objects.filter(name=name).exists():
            error = "Genre already exists"
        else:
            if form.is_valid():
                form.save()
                messages.success(request, "Genre added successfully.")
                return redirect('genres')

    context = {'form': form, 'errors': error}
    return render(request, 'main_app/add-genre.html', context)

def edit_genre(request, id):
    error = ""
    genre = get_object_or_404(Genre, id=id)
    form = GenreForm(instance=genre)

    if request.method == "POST":
        form = GenreForm(request.POST, request.FILES, instance=genre)
        name = request.POST.get('name')

        if Genre.objects.filter(name=name).exclude(id=id).exists():
            error = "Genre with this name already exists"
        else:
            if form.is_valid():
                form.save()
                messages.success(request, "Genre updated successfully.")
                return redirect('genres')

    context = {'form': form, 'genre': genre, 'errors': error}
    return render(request, 'main_app/edit-genre.html', context)

def delete_genre(request, id):
    genre = get_object_or_404(Genre, id=id)
    genre.delete()
    messages.success(request, "Genre deleted successfully.")
    return redirect('genres')

# def songs(request):
#     songs = Song.objects.all() 
#     print(songs)
#     context = {
#         'segment': 'songs',
#         'songs': songs
#     }
#     return render(request, 'main_app/music.html', context)

def songs(request):
    context={
        'sgement':'songs'
    }
    return render(request,'main_app/music.html',context)


def lazy_scroll_songs(request):
    skip = int(request.GET.get('skip', 0))
    limit = int(request.GET.get('limit', 10))
    
    data = Song.objects.all()[skip:skip + limit]
    
    song_list = []  

    for item in data:
        song_data = {
            "id": item.id,
            "name": item.name,
            "image": item.image.url if item.image else None,
            "duration":item.duration,  
            "song_url": item.song_file.url if item.song_file else item.song_url 
        }
        song_list.append(song_data)

    return JsonResponse({'data': song_list})









# main_app/views.py

from mutagen.mp3 import MP3
from io import BytesIO
import requests
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

import requests
from mutagen.mp3 import MP3
from io import BytesIO

def add_song(request):
    if request.method == "POST":
        # Get data from the form
        name = request.POST.get('name')
        image = request.FILES.get('image')  # Optional image upload
        song_url = request.POST.get('song_url')  # Song URL (if provided)
        song_file = request.FILES.get('song_file')  # Uploaded song file

        # Initialize the song object
        song = Song(
            name=name,
            image=image,
        )

        # Handle the song file upload
        if song_file:
            try:
                # Assign the song file to the model field
                song.song_file = song_file
                song.save()
                messages.success(request, "Song added successfully.")

                # Calculate and set the song duration
                file_path = song.song_file.path  # Get the file path
                audio = MP3(file_path)  # Use mutagen to read the MP3 file
                duration = audio.info.length  # Get the song duration

                song.duration = format_duration(duration)  # Format the duration
                song.save()  # Save the updated duration
                messages.success(request, "Song duration calculated successfully.")

            except Exception as e:
                print(f"Error calculating duration for uploaded file: {e}")
                song.duration = None
                song.save()
                messages.error(request, "There was an error with your song upload.")
        # Handle external song URL
        elif song_url:
            song.song_url = song_url
            try:
                if song_url.endswith('.mp3'):
                    # For MP3 URLs, fetch the content and calculate the duration
                    response = requests.get(song_url, timeout=60)
                    response.raise_for_status()  # Check if request is successful
                    audio = MP3(BytesIO(response.content))
                    duration = audio.info.length
                    song.duration = format_duration(duration)
                else:
                    # Handle non-MP3 song URLs (e.g., streaming or other formats)
                    duration = get_song_duration_from_url(song_url)
                    if duration:
                        song.duration = duration
            except Exception as e:
                print(f"Error calculating duration for song URL {song_url}: {e}")
                song.duration = None

        else:
            print("No song source provided.")

        # Save the song object with the final data (only once)
        song.save()
        messages.success(request, "Song added successfully.")
        return redirect('songs')

    # Load related objects for the form (e.g., artists, albums, genres)
    artists = Artist.objects.all()
    albums = Album.objects.all()
    genres = Genre.objects.all()

    return render(request, 'main_app/add-music.html', {'artists': artists, 'albums': albums, 'genres': genres})

def view_song(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    return render(request, 'main_app/view-songs.html', {'song': song})

def delete_music(request, id):
    song = get_object_or_404(Song, id=id)
    song.delete()
    messages.success(request, "Song deleted successfully.")
    return redirect('songs')


def social_media(request):
    socialmedias=SocialMedia.objects.all()
    context={
        'segment':'social-media',
        'socialmedias':socialmedias,
    }
    return render(request,'main_app/social-media.html',context)

def add_social_media(request):
    if request.method == "POST":
        form = SocialMediaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Social media added successfully.")
            return redirect('social-media')
    else:
        form = SocialMediaForm()
    context={
        'form':form,
    }
    return render(request,'main_app/add-social-media.html',context)

def edit_social_media(request,id):
    socialmedia=get_object_or_404(SocialMedia,id=id)
    form=SocialMediaForm(instance=socialmedia)
    if request.method == "POST":
        form=SocialMediaForm(request.POST,instance=socialmedia)
        if form.is_valid():
            form.save()
            messages.success(request, "Social media updated successfully.")
            return redirect('social-media')
    context={
        'form':form,
        'socialmedia':socialmedia,
    }
    return render(request,'main_app/edit-social-media.html',context)

def delete_social_media(request,id):
    socialmedia=get_object_or_404(SocialMedia,id=id)
    socialmedia.delete()
    messages.success(request, "Social media deleted successfully.")
    return redirect('social-media')


def share_my_app(request):
    shareapp = ShareMyApp.objects.all()
    context={
        'segment':'share_my_app',
        'shareapp_data':shareapp
    }
    return render(request,'main_app/share-my-app.html',context)


def add_share_my_app(request):
    if request.method == "POST":
        form = ShareMyAppForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Share my app added successfully.")
            return redirect('share_my_app')
    else:
        form = ShareMyAppForm()
    context={
        'form':form,
    }
    return render(request,'main_app/add-shareapp.html',context)

def edit_share_my_app(request, id):
    share_app = get_object_or_404(ShareMyApp, id=id)

    if request.method == 'POST':
        form = ShareMyAppForm(request.POST, instance=share_app)
        if form.is_valid():
            form.save()
            messages.success(request, "Share my app updated successfully.")
            return redirect('share_my_app')
    else:
        form = ShareMyAppForm(instance=share_app)

    context = {
        'form': form,
        'data': share_app,  # Pass the object as 'data'
    }
    return render(request, 'main_app/edit-shareapp.html', context)


def delete_share_app(request, id):
    share_app = get_object_or_404(ShareMyApp, id=id) 
    share_app.delete()
    messages.success(request, "Share my app deleted successfully.") 
    return redirect('share_my_app')  


def mixes(request):
    mixes = Mixes.objects.all()
    context={
        'segment':'Mixes',
        'mixes':mixes,
    }
    return render(request,'main_app/mixes.html',context)

def add_mixes(request):
    error = ""
    form = MixesForm()
    if request.method == "POST":
        form = MixesForm(request.POST, request.FILES)
        name = request.POST.get('name')
        image = request.FILES.get('image')

        # if Album.objects.filter(name=name).exists():
        #     error = "Album already exists"
        # else:
        if form.is_valid():
            form.save()
            messages.success(request, "Mix added successfully.")
            return redirect('Mixes')

    context = {'form': form, 'errors': error}
    return render(request, 'main_app/add-mix.html', context)

def edit_mix(request,id):
    error = ""
    mix = get_object_or_404(Mixes, id=id)
    form = MixesForm(instance=mix)

    if request.method == "POST":
        form = MixesForm(request.POST, request.FILES, instance=mix)
        name = request.POST.get('name')
        image = request.FILES.get('image')

        if form.is_valid():
            form.save()
            messages.success(request, "Mix updated successfully.")
            return redirect('Mixes')

    context = {'form': form, 'mix': mix, 'errors': error}
    return render(request, 'main_app/edit-mix.html', context)

def delete_mix(request,id):
    mix = get_object_or_404(Mixes, id=id)
    mix.delete()
    messages.success(request, "Mix deleted successfully.")
    return redirect('Mixes')
 
def live_video(request): 
    """Handles displaying and adding live video records."""
    
    # Retrieve the latest live video record
    live_video = Live_Videos.objects.order_by('-id').first()  # Use .first() to avoid errors if no videos exist
    
    # Ensure live_video is not None before accessing attributes
    context = {
        'segment': 'live_video',
        'videos_name': live_video.name if live_video else '',
        'videos_image': live_video.image.url if live_video and live_video.image else '',
        'videos_link': live_video.video_link if live_video else '',
        'videos_artist_name': live_video.artist_name if live_video else '',
        'videos_description': live_video.description if live_video else '',
    }

    if request.method == "POST":
        # Retrieving form data
        videos_name = request.POST.get('livevideo_name')
        videos_image = request.FILES.get('livevideo_image')
        videos_link = request.POST.get('livevideo_link')
        videos_artist_name = request.POST.get('livevideo_artist_name')
        videos_description = request.POST.get('livevideo_description')

        # Ensure all fields are provided
        if videos_name and videos_link and videos_image and videos_artist_name and videos_description:
            # Check if the video name already exists (to prevent duplicates)
            if Videos.objects.filter(name=videos_name).exists():  # Use correct field name
                messages.warning(request, "⚠️ This video already exists!")
            else:
                # Create the new video object
                new_video = Videos.objects.create(
                    name=videos_name,  # Use correct field name
                    image=videos_image, 
                    video_link=videos_link,  # Use correct field name
                    artist_name=videos_artist_name,  # Use correct field name
                    description=videos_description,  # Use correct field name
                )
                new_video.save()
                messages.success(request, "✅ Live video added successfully!")
                print("✅ New Live Video Added:", new_video)
        else:
            messages.error(request, "❌ Error: Name, Link, Image, Artist, and Description are required fields!")

        print("📩 Received POST request")
        print("📝 POST Data:", request.POST)
        print("📂 FILES Data:", request.FILES)

        return redirect('live-video')  # Redirect to clear the form after submission

    return render(request, 'main_app/live-video.html', context)



from django.shortcuts import render, redirect
from .forms import LiveRadioForm  # Assuming you have a form called LiveRadioForm
from .models import LiveRadio
from django.contrib import messages

def live_radio(request):
    """Handles displaying and adding/updating live radio records."""
    
    # Get the first live radio record (if it exists)
    live_radio = LiveRadio.objects.first()  # Retrieve the first live radio record
    
    if request.method == "POST":
        form = LiveRadioForm(request.POST, request.FILES, instance=live_radio)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Live radio updated successfully!")
            return redirect('live-radio')  # Redirect to refresh page after submission
    else:
        form = LiveRadioForm(instance=live_radio)  # Prepopulate the form with the existing data

    # Handle the case when live_radio is None
    created_at = live_radio.created_at.strftime("%d-%m-%Y") if live_radio and live_radio.created_at else ''
    updated_at = live_radio.updated_at.strftime("%H:%M:%S %p") if live_radio and live_radio.updated_at else ''

    # Pass the live_radio object fields to the template
    context = {
        'form': form,
        'live_radio_name': live_radio.liveradio_name if live_radio else '',
        'live_radio_link': live_radio.liveradio_link if live_radio else '',
        'live_radio_image': live_radio.liveradio_image if live_radio else None,
        'created_at': created_at,
        'updated_at': updated_at,
    }

    return render(request, 'main_app/live-radio.html', context)



def trending_artists(request):
    context = {}  
    if request.method == 'POST':
        selected_artists_ids = request.POST.getlist('artists')  
        selected_artists = Artist.objects.filter(id__in=selected_artists_ids)  
        trending_artists_ids = TrendingArtists.objects.values_list('fk_artist', flat=True)

        # Get the last position and handle empty queryset scenario
        last_element = TrendingArtists.objects.order_by('position').last()
        last_position = last_element.position if last_element else 0  # Default to 0 if empty

        for artist in selected_artists:
            if artist.id not in trending_artists_ids:
                last_position += 1  # Increment position
                TrendingArtists.objects.create(fk_artist=artist, position=last_position)

        return redirect("trending_artists")
    
    assigned_artists = (
        SongCategory.objects.filter(songs__isnull=False)
        .values_list('artists', flat=True)
        .distinct()
    )
    all_artists = Artist.objects.filter(id__in=assigned_artists)

    context = {
        'segment': 'Trending_Artist',  
        'artists': all_artists,  
        'trending_artists': TrendingArtists.objects.all(),  
    }    

    return render(request, 'main_app/trending_artist.html', context)

def update_positions_artists(request):
    if request.method == 'POST':
        # try:
            data = json.loads(request.body)  # Parse incoming JSON data
            positions = data.get('positions', [])  # Extract the 'positions' array

            # Loop through the positions and update each artist's position
            for index, artist_id in enumerate(positions, start=1):
                artist = TrendingArtists.objects.get(id=artist_id)  # Get the artist by ID
                artist.position = index  # Update position field (you may need to adjust this field if it's different)
                artist.save()  # Save the updated artist

            # return JsonResponse({'message': 'Positions updated successfully'})

        # except Exception as e:
        #     return JsonResponse({'message': str(e)}, status=400)

    return JsonResponse({'message': 'Invalid request method'}, status=400)


def trending_albums(request):
    context = {}

    if request.method == 'POST':
        selected_albums_ids = request.POST.getlist('albums')
        selected_albums = SongCategory.objects.filter(id__in=selected_albums_ids)
        trending_albums_ids = TrendingAlbums.objects.values_list('fk_album', flat=True)

        for album in selected_albums:
            if album.id not in trending_albums_ids:
                TrendingAlbums.objects.create(fk_album_id=album.id)
                print(f"Album {album.id} added to trending albums.")  # Debugging line

        return redirect("trending_albums")

    assinged_albums=(
            SongCategory.objects.filter(songs__isnull=False, albums__isnull=False)
            .values_list('albums')
            .distinct()
        )
    all_albums=Album.objects.filter(id__in=assinged_albums)
    

    context = {
        'albums': all_albums,
        'segment': 'trending_album',
        'trending_albums': TrendingAlbums.objects.all(),
    }

    # Debugging output
    print(f"Trending albums: {context['trending_albums']}")
    return render(request, 'main_app/trending_album.html', context)   

def recommended(request):
    context={}
    RecommendedSongs = RecommendedTracks.objects.all().values_list('fk_song', flat=True).distinct()
    Songs = Song.objects.filter(id__in=RecommendedSongs)

    song_data = []  # This will be passed to the frontend

    for song in Songs:
        artists = (SongCategory.objects.filter(songs=song.id, artists__isnull=False)
                .select_related('songs', 'artists')
                .values_list('artists__name', flat=True)  # Get only artist names
                .distinct()
                )

        song_data.append({
            "id": song.id,
            "name": song.name,
            "duration": song.duration,
            "image": song.image.url if song.image else None,
            "song_url":song.song_file.url if song.song_file else song.song_url,
            "artists": list(artists)  # Convert QuerySet to a list
        })

    context = {
        "song_data": song_data
    }

    return render(request, "main_app/recommended_songs.html", context)
    
    # context={
    #     'songs':Songs,
    # }
    # return render(request,'main_app/recommended_songs.html',context)
def update_positions_albums(request):
    if request.method == 'POST':
        # try:
            data = json.loads(request.body)  # Parse incoming JSON data
            positions = data.get('positions', [])  # Extract the 'positions' array

            # Loop through the positions and update each album's position
            for index, album_id in enumerate(positions, start=1):
                album = TrendingAlbums.objects.get(id=album_id)  # Get the album by ID
                album.position = index  # Update position field (you may need to adjust this field if it's different)
                album.save()  # Save the updated album

            return JsonResponse({'message': 'Positions updated successfully'})

        # except Exception as e:
        #     return JsonResponse({'message': str(e)}, status=400)

    return JsonResponse({'message': 'Invalid request method'}, status=400)

def trending_geners(request):
    context = {}

    if request.method == 'POST':
        selected_genres_ids = request.POST.getlist('genres')
        selected_genres = Genre.objects.filter(id__in=selected_genres_ids)
        trending_genres_ids = TrendingGenres.objects.values_list('fk_genre', flat=True)

        for genre in selected_genres:
            if genre.id not in trending_genres_ids:
                TrendingGenres.objects.create(fk_genre_id=genre.id)
                print(f"Genre {genre.id} added to trending genres.")  # Debugging line

        return redirect("trending_geners")

    assinged_genres=(
            SongCategory.objects.filter(songs__isnull=False, fk_genre__isnull=False)
            .values_list('fk_genre')
            .distinct()
        )
    all_genres=Genre.objects.filter(id__in=assinged_genres)
    

    context = {
        'genres': all_genres,
        'segment': 'Trending_genres',
        'trending_genres': TrendingGenres.objects.all(),
    }

    # Debugging output
    print(f"Trending genres: {context['trending_genres']}")
    return render(request, 'main_app/trending_geners.html', context)   

def update_positions_geners(request):
    if request.method == 'POST':
        # try:
            data = json.loads(request.body)  # Parse incoming JSON data
            positions = data.get('positions', [])  # Extract the 'positions' array

            # Loop through the positions and update each genre's position
            for index, genre_id in enumerate(positions, start=1):
                genre = TrendingGenres.objects.get(id=genre_id)  # Get the genre by ID
                genre.position = index  # Update position field (you may need to adjust this field if it's different)
                genre.save()  # Save the updated genre

            return JsonResponse({'message': 'Positions updated successfully'})

        # except Exception as e:
        #     return JsonResponse({'message': str(e)}, status=400)

    return JsonResponse({'message': 'Invalid request method'}, status=400)    

def trending_mixes(request):
    context = {}

    if request.method == 'POST':
        selected_mixes_ids = request.POST.getlist('mixes')
        selected_mixes = Mixes.objects.filter(id__in=selected_mixes_ids)
        trending_mixes_ids = TrendingMixes.objects.values_list('fk_mixes', flat=True)  # Corrected field name

        for mix in selected_mixes:
            if mix.id not in trending_mixes_ids:
                TrendingMixes.objects.create(fk_mixes_id=mix.id)  # Corrected field name
                print(f"Mix {mix.id} added to trending mixes.")  # Use `mix.id` instead of `Mixes.id`
        return redirect("trending_mixes")

    assigned_mixes = (
        SongCategory.objects.filter(songs__isnull=False, fk_mixes__isnull=False)
        .values_list('fk_mixes', flat=True)  # Ensure correct field name
        .distinct()
    )
    all_mixes = Mixes.objects.filter(id__in=assigned_mixes)
    context = {
        'mixes': all_mixes,
        'segment': 'Trending_mixes',
        'trending_mixes': TrendingMixes.objects.all(),
    }

    # Debugging output
    print(f"Trending mixes: {context['trending_mixes']}")
    return render(request, 'main_app/trending_mixes.html', context)


def update_positions_mixes(request):
    if request.method == 'POST':
        # try:
            data = json.loads(request.body)  # Parse incoming JSON data
            positions = data.get('positions', [])  # Extract the 'positions' array

            # Loop through the positions and update each mix's position
            for index, mix_id in enumerate(positions, start=1):
                mix = TrendingMixes.objects.get(id=mix_id)  # Get the mix by ID
                mix.position = index  # Update position field (you may need to adjust this field if it's different)
                mix.save()  # Save the updated mix
                messages.success(request, "Positions updated successfully.")

            return JsonResponse({'message': 'Positions updated successfully'})

        # except Exception as e:
        #     return JsonResponse({'message': str(e)}, status=400)

    return JsonResponse({'message': 'Invalid request method'}, status=400)

def trending_tracks(request):
    context = {}

    if request.method == 'POST':
        selected_tracks_ids = request.POST.getlist('tracks')
        selected_tracks = Song.objects.filter(id__in=selected_tracks_ids)
        trending_tracks_ids = TrendingTracks.objects.values_list('fk_tracks_id', flat=True)

        for track in selected_tracks:
            if track.id not in trending_tracks_ids:
                TrendingTracks.objects.create(fk_tracks_id=track.id)
                print(f"Track {track.id} added to trending tracks.")

        return redirect("trending_tracks")

    assigned_tracks = (
        SongCategory.objects.filter(songs__isnull=False)
        .values_list('songs', flat=True)
        .distinct()
    )
    all_tracks = Song.objects.filter(id__in=assigned_tracks)

    context = {
        'tracks': all_tracks,
        'segment': 'Trending_tracks',
        'trending_tracks': TrendingTracks.objects.select_related('fk_tracks').all(),
    }

    print(f"Trending tracks: {context['trending_tracks']}")
    return render(request, 'main_app/trending_tracks.html', context)



def update_positions_tracks(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Parse incoming JSON data
            positions = data.get('positions', [])  # Extract the 'positions' array

            # Loop through the positions and update each track's position
            for index, track_id in enumerate(positions, start=1):
                track = TrendingTracks.objects.get(id=track_id)  # Get the track by ID
                track.position = index  # Update position field (Ensure you have a 'position' field in the model)
                track.save()  # Save the updated track
                messages.success(request, "Positions updated successfully.")

            return JsonResponse({'message': 'Positions updated successfully'})

        except Exception as e:
            return JsonResponse({'message': str(e)}, status=400)

    return JsonResponse({'message': 'Invalid request method'}, status=400)

def playlists(request):
    context={
        
    }
    return render(request,'main_app/playlists.html',context)


def terms_of_service(request):
    # Handle POST request (form submission)
    if request.method == "POST":
        form = TermsOfServiceForm(request.POST)
        if form.is_valid():
            # Access cleaned data from the form
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            
            # Check if the object already exists (to edit it) or create a new one
            first_obj = TermsOfService.objects.first()
            if first_obj:
                # Update the existing object
                first_obj.title = title
                first_obj.description = description
                first_obj.save()
            else:
                # If no object exists, create a new one
                TermsOfService.objects.create(title=title, description=description)
            
            # Redirect to the terms_of_service page after saving
            return redirect('terms_of_service')  # Redirect to the same page or success page
    else:
        # Handle GET request (form load)
        first_obj = TermsOfService.objects.first()

        # If there's an existing object, prepopulate the form
        if first_obj:
            form = TermsOfServiceForm(instance=first_obj)
        else:
            # If no object exists, initialize an empty form
            form = TermsOfServiceForm()

    # Context for rendering the page
    context = {
        'form': form,
        'title': getattr(first_obj, 'title', ''),
        'description': getattr(first_obj, 'description', ''),   
        'segment':'terms_of_service',
    }
    return render(request, 'main_app/Terms_Of_Services.html', context)


def privacy_policy(request):
    # Handle POST request (form submission)
    if request.method == "POST":
        form = PrivacyPolicyForm(request.POST)
        if form.is_valid():
            # Access cleaned data from the form
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            
            # Check if the object already exists (to edit it) or create a new one
            first_obj = PrivacyPolicy.objects.first()
            if first_obj:
                # Update the existing object
                first_obj.title = title
                first_obj.description = description
                first_obj.save()
                messages.success(request, "Privacy policy updated successfully.")
            else:
                # If no object exists, create a new one
                PrivacyPolicy.objects.create(title=title, description=description)
            
            # Redirect to the terms_of_service page after saving
            return redirect('privacy_policy')  # Redirect to the same page or success page
    else:
        # Handle GET request (form load)
        first_obj = PrivacyPolicy.objects.first()

        # If there's an existing object, prepopulate the form
        if first_obj:
            form = PrivacyPolicyForm(instance=first_obj)
        else:
            # If no object exists, initialize an empty form
            form = PrivacyPolicyForm()

    # Context for rendering the page
    context = {
        'form': form,
        'title': getattr(first_obj, 'title', ''),
        'description': getattr(first_obj, 'description', ''),
        'segment':'privacy_policy',
    }
    return render(request, 'main_app/Privacy_Policy.html', context)


def videos(request):
    if request.method == "POST":
        form = AssignVideos(request.POST)
        if form.is_valid():
            selected_videos = form.cleaned_data['video']
            selected_videos_category = form.cleaned_data['videos_category']

            videos_id = [video.id for video in selected_videos]
            category_id = [video_category.id for video_category in selected_videos_category]

            if category_id and videos_id:
                for category in category_id:
                    for video in videos_id:
                        conditions = Q()
                        if category:
                            conditions &= Q(fk_video_category=category)
                        if video:
                            conditions &= Q(fk_video=video)
                        if not SongCategory.objects.filter(conditions).exists():
                            SongCategory.objects.create(
                                fk_video_category_id=category,
                                fk_video_id=video
                            )
                return redirect('videos_frontend')
            

            
    VideosOBJ = Videos.objects.all()
    videos_cat_objs=video_category.objects.all()
    context={
        'videos':VideosOBJ,
        'videos_cats_obj':videos_cat_objs,
    }
    return render(request,'main_app/Videos/Videos.html',context)


def videos_add(request):
    if request.method == "POST":
        # Get data from the form
        videos_name = request.POST.get('videos_name')
        videos_image = request.FILES.get('videos_image')  # Optional image upload
        videos_url = request.POST.get('videos_url')  # Song URL (if provided)
        videos_file = request.FILES.get('videos_file')
        videos_artist_name=request.POST.get("videos_artist_name")
        videos_description=request.POST.get("videos_description")
          # Uploaded song file

        # Initialize the song object
        video = Videos(
            videos_name=videos_name,
            videos_image=videos_image,
            videos_artist_name=videos_artist_name,
            videos_description=videos_description,
        )

        # Handle the song file upload
        if videos_file:
            try:
                video.videos_file = videos_file  # Assign file to model
                video.save()
                messages.success(request, "Video uploaded successfully.")

                # Calculate video duration
                file_path = video.videos_file.path  # Get the file path
                clip = VideoFileClip(file_path)
                duration = clip.duration  # Get duration in seconds
                clip.close()

                video.duration = format_duration(duration)  # Format duration if needed
                video.save()
                messages.success(request, "Video duration calculated successfully.")

            except Exception as e:
                print(f"Error calculating duration for uploaded video file: {e}")
                video.duration = None
                video.save()
                messages.error(request, "Error calculating duration for uploaded video file.")

        elif videos_url:
            video.videos_url = videos_url
            try:
                # Fetch video content and process it
                response = requests.get(videos_url, timeout=60, stream=True)
                response.raise_for_status()

                with BytesIO(response.content) as video_buffer:
                    with open("temp_video.mp4", "wb") as f:
                        f.write(video_buffer.read())  # Save to a temporary file

                    clip = VideoFileClip("temp_video.mp4")
                    duration = clip.duration
                    clip.close()

                video.duration = format_duration(duration)
                video.save()
                messages.success(request, "Video duration calculated successfully.")

            except Exception as e:
                print(f"Error calculating duration for video URL {videos_url}: {e}")
                video.duration = None

        else:
            print("No video source provided.")


        # Save the song object with the final data (only once)
        video.save()
        messages.success(request, "Video added successfully.")
        redirect('videos_frontend')

    return render(request,'main_app/Videos/Videos_Add.html')

def videos_delete(request,id):
    video_obj=get_object_or_404(Videos,id=id)
    video_obj.delete()
    messages.success(request, "Video deleted successfully.")
    redirect('videos_frontend')
    return render(request,'main_app/Videos/Videos.html')

def videos_cat(request):
    videos_cats=video_category.objects.all()
    context={
        'video_cats':videos_cats,
    }
    return render(request,'main_app/Videos/Videos_Cat.html',context)

def videos_cat_add(request):
    if request.method == "POST":
        category_name=request.POST.get("category_name")
        category_image=request.FILES.get("category_image")

        category=video_category(
            category_name=category_name,
            category_image=category_image
        )
        category.save()
        messages.success(request, "Video category added successfully.")
        return redirect('videos_cat')
    return render(request,'main_app/Videos/Videos_Cat_Add.html')

def videos_cat_delete(request,id):
    video_cat_obj=get_object_or_404(video_category,id=id)
    video_cat_obj.delete()
    redirect('videos_cat')
    return render(request,'main_app/Videos/Videos_Cat.html')
    return render(request, 'main_app\Videos\Videos_Add.html', {'artists': artists, 'albums': albums, 'genres': genres})



def edit_song(request, id):
    error = ""
    song = get_object_or_404(Song, id=id)
    form = SongForm(instance=song)

    if request.method == "POST":
        form = SongForm(request.POST, request.FILES, instance=song)
        name = request.POST.get("name")
        song_source = request.POST.get("song_source")  # Get selected source
        audio_file = request.FILES.get("song_file") if song_source == "file" else None
        song_url = request.POST.get("song_url") if song_source == "url" else song.song_url  # Keep old URL if not changed

        if Song.objects.filter(name=name).exclude(id=id).exists():
            error = "A song with this name already exists."
        else:
            if form.is_valid():
                if song_source == "file" and audio_file:
                    # Rename audio file before saving
                    original_audio_name = audio_file.name
                    new_audio_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{original_audio_name}"
                    audio_file.name = new_audio_name
                    song.song_file = audio_file  # Save the new file
                
                elif song_source == "url":
                    song.song_file = None  # 🔥 Remove file path when URL is selected
                    song.song_url = song_url  # Save only the URL
                
                form.save()
                messages.success(request, "Song updated successfully.")
                return redirect("songs")  # Ensure 'songs' is a valid URL name
            else:
                messages.error(request, "There was an error with your song update.")

    context = {
        "form": form,
        "song": song,
        "errors": error,
        "song_url": song.song_url,  # Pass the existing URL to the template
    }
    return render(request, "main_app/edit-song.html", context)


def delete_song(request, id):
    song = get_object_or_404(Song, id=id)
    song.delete()
    messages.success(request, "Song deleted successfully.")
    return redirect('songs')
