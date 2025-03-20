import io
import mimetypes
import uuid
import shortuuid
from wsgiref.util import FileWrapper
import zipfile
from celery import *
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view,authentication_classes,permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Max,Q
from my_app.models import *
import random
import string
import secrets
import jwt
import os
from django.conf import settings
from datetime import datetime, timedelta, timezone
from django.core.validators import EmailValidator, ValidationError  
#from ..decorators import authenticate_with_token
import re
from django.template.loader import render_to_string
from my_app import default_variables
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q, Case, When, Value, IntegerField
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.core.paginator import Paginator, EmptyPage
import requests
from zipfile import ZipFile
from io import BytesIO
import urllib.parse
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers import serialize
import json
from my_app.utils import *
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from urllib.parse import urljoin
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView

secret_key_token = 'rHx3e8uaNklG(Zoe.f])b,$V2>{o/{N8_{-LRG94zEw%/e-Iu>'

refresh_key_token = 'vQCpGLyt1aZTbuV5Rzysvt35oXXfPWwim9nkKR3-oQo'




#common function for success responses
def success_response_200(code, message, data):
    return JsonResponse({
        'code': code,
        'message': message,
        'data': data},
    status=status.HTTP_200_OK)

def paginated_success_response_200(code,message,data,per_page,current_page,last_page):
    return JsonResponse({
        'code':code,
        'message':message,
        'data':data,
        'per_page':per_page,
        "current_page":current_page,
        "last_page":last_page
    },status=status.HTTP_200_OK)

#common function to build url
def get_absolute_url(request,url):
    base_url = request.build_absolute_uri('/')[:-1]
    return urljoin(base_url,url)

#common function to generate token by passing user object
def generate_token(user):
    secret_key = secret_key_token
    refresh_key = refresh_key_token
    access_payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(hours=24)  # Set expiration time to 24 hours from now
    }
    refreash_payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(days=10)  # Set expiration time to 24 hours from now
    }

    access_token = jwt.encode(access_payload, secret_key, algorithm='HS256')
    refreash_token = jwt.encode(refreash_payload, refresh_key, algorithm='HS256')
    user.remember_token = access_token
    user.refresh_token = refreash_token
    user.save()
    return access_token,refreash_token



#common function to check password strength
def check_password_strength(password):
    special_char = '!@#$%^&*()_+-=[]{}|;:,.<>?~'
    numbers = '0123456789'
    if not any(char in special_char for char in password) or not any(char in numbers for char in password):
        raise Exception('Password must contain at least one special character and one number')
    return None



def validation(first_name,user_name,phone_number,email):
    
    # Check if username, email, or phone number already exists
    user_exists = CustomUser.objects.filter(
        Q(username=user_name) | Q(email=email) | Q(phone_number=phone_number)
    ).exists()
    if user_exists:
        raise Exception('User with this username, email, or phone number already exists.')

    # Validate name lengths
    if not (3 <= len(first_name) <= 20):
        raise Exception('First name must be between 3 and 20 characters.')
    if not (3 <= len(user_name) <= 20):
        raise Exception('Username must be between 3 and 20 characters.')
    
    # Validate phone number length
    if len(phone_number) != 10:
        raise Exception('Phone number must be 10 digits.')

    # Validate email pattern
    email_validator=EmailValidator()
    try:
        email_validator(email)
    except ValidationError:
        raise Exception('Invalid email address.')

    return None


def extract_token(request_obj):
    auth_header = request_obj.headers.get('Authorization')
    auth_type, token = auth_header.split()
    return token



#user login api
@swagger_auto_schema(method='post', operation_description="User for login", tags=['app-user'],
                     request_body=openapi.Schema(
                         type=openapi.TYPE_OBJECT,
                         properties={
                            'username': openapi.Schema(type=openapi.TYPE_STRING, description='User Name'),
                            'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                         }
                     ))
@api_view(['POST'])
@authentication_classes([])  # Disable authentication for this specific view
@permission_classes([])  # Disable permission checks for this specific view
def user_login(request):
    required_fields = ['username', 'password','fcm_id','device_type']
    missing_fields = [field for field in required_fields if not request.data.get(field)]
    if missing_fields:
        return success_response_200(400,f'Missing fields: {", ".join(missing_fields)}','null')
    
    username = request.data['username']
    entered_password = request.data['password']
    fcm_id = request.data['fcm_id']
    device_type = request.data['device_type']

    # Check if the username and password match in CustomUser
    try:
        user = CustomUser.objects.get(Q(username=username) | Q(email=username))
        
        if user.device_type != device_type:
            user.device_type = device_type
        if user.fcm_id != fcm_id:
            user.fcm_id = fcm_id
        user.save()


        if not check_password(entered_password, user.password):
            return success_response_200(401,'Invalid credentials.','null')
        
        access_token,refreash_token = generate_token(user)
        
        return success_response_200(200,'Login successful', {
            'user_id':user.id,
            'username':user.username,
            'email':user.email,
            'fcm_id':user.fcm_id,
            'token':access_token,
            })
    except CustomUser.DoesNotExist:
        return success_response_200(401,'Invalid credentials','null')



#user register api
@swagger_auto_schema(method='post', operation_description="User for create new user", tags=['app-user'],
                     request_body=openapi.Schema(
                         type=openapi.TYPE_OBJECT,
                         properties={
                            'type': openapi.Schema(type=openapi.TYPE_STRING, description='Type of user'),
                            'username': openapi.Schema(type=openapi.TYPE_STRING, description='User Name'),
                            'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First Name'),
                            'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
                            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number'),
                            'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                            'birth_date': openapi.Schema(type=openapi.TYPE_STRING, description='Birth date'),
                            'country_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Country id'),
                            'timezone': openapi.Schema(type=openapi.TYPE_STRING, description='Timezone'),
                            'device_type': openapi.Schema(type=openapi.TYPE_STRING, description='Device type'),
                            'fcm_id': openapi.Schema(type=openapi.TYPE_STRING, description='Fcm id'),
                         }
                     ))
@api_view(['POST'])
@authentication_classes([])  # Disable authentication for this specific view
@permission_classes([])  # Disable permission checks for this specific view
def user_register(request):
    type = request.data.get('type')
    match type:
        case 0:
            required_fields = ['fcm_id', 'device_type']
            missing_fields = [field for field in required_fields if not request.data.get(field)]
            if missing_fields:
                return success_response_200(400,f'Missing fields: {", ".join(missing_fields)}','null')
            fcm_id=request.data.get('fcm_id')
            device_type=request.data.get('device_type')
            short_uuid = shortuuid.ShortUUID().random(length=8)
            username = 'guest_user_' + short_uuid  # Using UUID to ensure uniqueness
            email = f'guest_{short_uuid}@gmail.com'
            
            user = CustomUser(
                type=type,
                fcm_id=fcm_id,
                device_type=device_type,
                username=username,
                email=email,
            )
            user.save()
            #generating token using common function
            access_token,refreash_token = generate_token(user)
            
            guest_user_data={
                'user_id':user.id,
                'username':user.username,
                'email':user.email,
                'fcm_id':user.fcm_id,
                'token':access_token,
            }
            
            return success_response_200(200,'Sucess! welcome to musica',guest_user_data)
        case 1:
            #validtion to check if all fields are present
            required_fields = ['fcm_id', 'name', 'contact', 'user_name', 'password', 'birth_date', 'email', 'country_id', 'timezone', 'device_type']
            missing_fields = [field for field in required_fields if not request.data.get(field)]
            if missing_fields:
                return success_response_200(400,f'Missing fields: {", ".join(missing_fields)}','null')

            #get data from request  
            fcm_id = request.data['fcm_id']
            first_name = request.data['name']
            phone_number = request.data['contact']
            user_name = request.data['user_name']
            password = request.data['password']
            birth_date = request.data['birth_date']
            email = request.data['email']
            country_id = request.data['country_id']
            timezone = request.data['timezone']
            # genres = request.data.get('genres', [])  # Use .get() to fetch genres safely
            device_type = request.data['device_type']

            # Validate the data
            try:
                validation(first_name, user_name, phone_number, email)
                check_password_strength(password)
            except Exception as e:
                return success_response_200(400, str(e), 'null')

            # Encrypting the password
            encrypted_password = make_password(password)

            # Fetch the country based on country_id
            try:
                country = Country.objects.get(id=country_id)
            except Country.DoesNotExist:
                return success_response_200(400, 'Invalid country ID', 'null')

            # Create the user
            user = CustomUser(
                fcm_id=fcm_id,
                first_name=first_name,
                phone_number=phone_number,
                username=user_name,
                email=email,
                password=encrypted_password,
                birth_date=birth_date,
                country_id=country,
                timezone=timezone,
                device_type=device_type,
            )

            # Save the user
            user.save()

            # Save genres if provided
            # if genres:
            #     genre_objects = Genre.objects.filter(id__in=genres)  # Assuming 'genres' is a list of genre IDs
            #     user.genres.set(genre_objects)  # This assigns the genres to the user
            # print(genre_objects)
            default_image_path = default_variables.THUMBNAIL_ICON_REACT()
            default_title_path = default_variables.GMAIL_WEBSITE_TITLE
            to_email = email
            subject = f'Account Created Successfully! {default_title_path}'
            context = {
                "username":user_name,
                "first_name":first_name,
                "email":email,
                "password":password,
                "country":country.name,
                "timezone":timezone,
                "app_name":default_title_path,
                "current_year":2024,
                "logo_url": default_image_path,
                "create_or_reset":"account registeration"
            }
            html_content = render_to_string('main_app/gmail_send.html', context)

            send_html_email(to_email, subject, html_content)


            response_data={
                'code':status.HTTP_200_OK,
                'message':'Sucess! welcome to musica',
                'user_id':user.id,
                'username':user.username,
                'email':user.email,
                'fcm_id':user.fcm_id,
            }
            return  success_response_200(200,'Sucess! welcome to musica',response_data)




#API to get country list and timezone 
@swagger_auto_schema(method='GET', operation_description="getting country and timezones", tags=['country-and-timezones'],
                     request_body=openapi.Schema(
                         type=openapi.TYPE_OBJECT,
                         properties={
                            'type': openapi.Schema(type=openapi.TYPE_STRING, description='Type of user'),
                         }
                     ))
@api_view(['GET'])
@authentication_classes([]) 
@permission_classes([])  
def countryandtimezone(request):
    #extracting type from query parameter
    type=request.GET.get('type')
    
    #handling request based on type 
    match type:
        case 'country':
            countries  = Country.objects.all()
            country_data = [
                {
                    'country_id': country.id,
                    'country_name': country.name,
                    'country_phone_code': country.phone_code,
                    'country_code': country.code,
                }
                for country in countries
            ]
            return success_response_200(200,'Country list', country_data)
        case 'timezone':
            country_code = request.GET.get('countrycode')
            timezones = Timezone.objects.get(country_code=country_code)
            if not timezones:
                return success_response_200(400,'timezone doesnot exists','null')
            timezone_data ={
                    'timezone_id': timezones.zone_id,
                    'country_code': timezones.country_code,
                    'timezone_name': timezones.zone_name, 
            }
            return success_response_200(200,'Timezone list', timezone_data)


#Api for user logout
@swagger_auto_schema(method='GET',operation_description="logout" ,tags=['logout'],
                     request_body=openapi.Schema(
                         type=openapi.TYPE_OBJECT,
                         properties={
                             'user_id':openapi.Schema(type=openapi.TYPE_OBJECT,description="user id"),
                         }
                     ))
@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def logout(request):
    user_id = request.GET.get('user_id')
    if not user_id:
        return success_response_200(404,"user id not found","null")
    user_obj = CustomUser.objects.get(id=user_id)
    user_obj.remember_token = ""
    user_obj.save()
    return success_response_200(200,"user logged out successfully","null")


#common api for trending section
@swagger_auto_schema(method='GET',operation_description="Trending Artists", 
                            # tags=['app-user']
                            request_body=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                            'artist_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='artist id'),
                            'artist_name': openapi.Schema(type=openapi.TYPE_STRING, description='artist name'),
                            'artist_image': openapi.Schema(type=openapi.TYPE_STRING, description='artist image'),
                         }
                     ))
@api_view(['GET'])
@authentication_classes([])  
@permission_classes([]) 
def Trending(request):
    token=extract_token(request)
    if not token:
        return success_response_200(401,'Unauthorized','null')
    user=CustomUser.objects.get(remember_token=token)
    page=request.GET.get("page",1)
    limit=request.GET.get("limit",10)
    type=request.GET.get("type")
    if not type:
        return success_response_200(404,'please mention type','null')
    match type:
        case 'Artists':
            artists = TrendingArtists.objects.order_by('position')
            if not artists:
                return success_response_200(200,'no trending artists found','null')
            data = [
                {
                    'trending_artist_id': artist.id,
                    'artist_id': artist.fk_artist.id,
                    'artist_name': artist.fk_artist.name,
                    'artist_image': get_absolute_url(request,artist.fk_artist.image.url),
                }
                for artist in artists
            ]
            type = 'artists'
        case 'Genres':
            genres = TrendingGenres.objects.order_by('position')
            if not genres:
                return success_response_200(200,'no trending genres found','null')
            data = [
                {
                    'trending_genre_id': genre.id,
                    'genre_id': genre.fk_genre.id,
                    'genre_name': genre.fk_genre.name,
                    'genre_image': get_absolute_url(request,genre.fk_genre.image.url),
                }
                for genre in genres
            ]
            type = 'genres'
        case 'Albums':
            albums = TrendingAlbums.objects.order_by('position')
            if not albums:
                return success_response_200(200,'no trending albums found','null')
            data = [
                {
                    'trending_album_id': album.id,
                    'album_id': album.fk_album.id,
                    'album_name': album.fk_album.name,
                    'album_image': get_absolute_url(request,album.fk_album.image.url),
                }
                for album in albums
            ]
            type = 'albums'
        case 'Tracks':
            Tracks = TrendingTracks.objects.order_by('position')
            if not Tracks:
                return success_response_200(200,'no trending songs found','null')
            data=[]
            for song in Tracks:
                favourite_status=FavouriteSong.objects.filter(fk_user=user.id,fk_song=song.fk_tracks.id).exists()
                artists=[]
                ArtistsObj = (
                    SongCategory.objects.filter(songs=song.fk_tracks.id,artists__isnull=False)
                    .select_related('artists')
                    .distinct()
                    .values('artists__id','artists__name','artists__image')
                )
                for artist in ArtistsObj:
                    artists.append({
                        'artist_id':artist['artists__id'],
                        'artist_name':artist['artists__name'],
                        'artist_image':get_absolute_url(request,artist['artists__image'])
                    })
                data.append({
                    'trending_song_id':song.id,
                    'song_id':song.fk_tracks.id,
                    'song_name':song.fk_tracks.name,
                    'song_image':get_absolute_url(request,song.fk_tracks.image.url) if song.fk_tracks.image else None,
                    'song_url':get_absolute_url(request,song.fk_tracks.song_file.url) if song.fk_tracks.song_file else get_absolute_url(request,song.fk_tracks.song_url),
                    'song_duration':song.fk_tracks.duration,
                    'total_likes':song.fk_tracks.total_likes,
                    'total_downloads':song.fk_tracks.total_downloads,
                    'playlist_count':song.fk_tracks.playlist_count,
                    'favourite_count':song.fk_tracks.favourite_count,
                    'favourite_status':favourite_status,
                    'artists':artists,
                })
            type = 'songs'
        case 'Mixes':
            mixes = TrendingMixes.objects.order_by('position')
            if not mixes:
                return success_response_200(200,'no trending mixes found','null')
            data=[]
            for mix in mixes:
                data.append({
                    'trending_mix_id':mix.id,
                    'mixes_id':mix.fk_mixes.id,
                    'mixes_name':mix.fk_mixes.name,
                    'mixes_image':get_absolute_url(request,mix.fk_mixes.image.url) if mix.fk_mixes.image else None,
                })
            type = 'mixes'
        case _:
            return success_response_200(200,'invalid query type','null')

    paginator=Paginator(data,limit)
    try:
        paginated_data=paginator.page(page)
    except PageNotAnInteger:
        paginated_data=paginator.page(1)
    except EmptyPage:
        paginated_data= []
    return JsonResponse({
        'code':200,
        'message':f"trending {type}",
        type:list(paginated_data),
        'page':page,
        'limit':limit,
        'total_pages':paginator.num_pages,        
    },status=status.HTTP_200_OK)
    


#API FOR SOCIAL MEDIA LINKS
@swagger_auto_schema(method='GET', operation_description="Social Media", tags=['app-user'],
                     request_body=openapi.Schema(
                         type=openapi.TYPE_OBJECT,
                         properties={
                            'social_media_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='social media id'),
                            'social_media_name': openapi.Schema(type=openapi.TYPE_STRING, description='social media name'),
                            'social_media_link': openapi.Schema(type=openapi.TYPE_STRING, description='social media link'),
                         }
                     ))
@api_view(['GET'])
@authentication_classes([])  # Disable authentication for this specific view
@permission_classes([])  # Disable permission checks for this specific view
def Socialmedia(request):
    socialmedias=SocialMedia.objects.all()
    data=[{
        "social_media_id":socialmedia.id,
        "social_media_name":socialmedia.social_media_name,
        "social_media_link":socialmedia.social_media_link,
    } for socialmedia in socialmedias]
    return success_response_200(200,"social media links",data)

#API FOR SHARING THE APP
@swagger_auto_schema(method='GET', operation_description="Social Media", tags=['app-user'],
                     request_body=openapi.Schema(
                         type=openapi.TYPE_OBJECT,
                         properties={
                            'shareapp_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='share app id'),
                            'shareapp_name': openapi.Schema(type=openapi.TYPE_STRING, description='share app name'),
                            'shareapp_andriod_link': openapi.Schema(type=openapi.TYPE_STRING, description='share app andriod link'),
                            'shareapp_ios_link':openapi.Schema(type=openapi.TYPE_STRING,description='share app ios link')
                         }
                     ))
@api_view(['GET'])
@authentication_classes([])  # Disable authentication for this specific view
@permission_classes([])  # Disable permission checks for this specific view
def sharemyapp(request):
    Shareapps= ShareMyApp.objects.all()
    data=[{
        "shareapp_id":Shareapp.id,
        "shareapp_name":Shareapp.shareapp_name,
        "shareapp_andriod_link":Shareapp.shareapp_andriod_link,
        "shareapp_ios_link":Shareapp.shareapp_ios_link,
    } for Shareapp in Shareapps]
    return success_response_200(200,"Share My App",data)



#FORGOT PASSWORD API
@swagger_auto_schema(method='GET', operation_description="email for forgot password", tags=['app-user'],
                     request_body=openapi.Schema(
                         type=openapi.TYPE_OBJECT,
                         properties={
                            'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
                         }
                     ))
@api_view(['GET'])
@authentication_classes([]) 
@permission_classes([])     
def forgot_password(request):
    email = request.data.get('email')
    if not email:
        return success_response_200(400,'Email not found','null')
    user = CustomUser.objects.filter(email=email).first()
    if not user:
        return success_response_200(400,'User not found','null')
    
    chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?~"
    temp_password = "MU" + "".join(secrets.choice(chars) for _ in range(6))
    user.password = make_password(temp_password)
    user.save()

    default_image_path = default_variables.THUMBNAIL_ICON_REACT()
    default_title_path = default_variables.GMAIL_WEBSITE_TITLE
            
    to_email = email
    subject = f'Password Reset Successfully! {default_title_path}'
    context = {
        "username":user.username,
        "password":temp_password,
        "app_name":default_title_path,
        "current_year":2025,
        "logo_url": default_image_path,
    }
    html_content = render_to_string('main_app/gmail_send_password.html', context)
    send_html_email(to_email, subject, html_content)

    return success_response_200(200,'Temporary password has been sent to your email',{'password':temp_password})



@swagger_auto_schema(method='GET', operation_description="User for create new user", tags=['app-user'],
                     request_body=openapi.Schema(
                         type=openapi.TYPE_OBJECT,
                         properties={
                            'album_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Album id'),
                            'album_name': openapi.Schema(type=openapi.TYPE_STRING, description='Album name'),
                            'album_image': openapi.Schema(type=openapi.TYPE_STRING, description='Album image'),
                            'album_created_at': openapi.Schema(type=openapi.TYPE_STRING, description='Album created at'),
                            'album_updated_at':openapi.Schema(type=openapi.TYPE_STRING, description='Album updated at'),
                         }
                     ))
@api_view(['GET'])
@authentication_classes([])  # Disable authentication for this specific view
@permission_classes([])  # Disable permission checks for this specific view
def albums_list(request):
    # albums = Album.objects.all()
    albums_objs=(
        SongCategory.objects.filter(
            albums__isnull=False,
            songs__isnull=False
        )
        .select_related('albums')
        .values_list('albums',flat=True)
        .distinct()
    )
    albums=Album.objects.filter(id__in=albums_objs).distinct()
    albums_data = [
        {
            'album_id': album.id,
            'album_name': album.name,
            'album_image': request.build_absolute_uri(album.image.url) if album.image else None,
            'album_created_at': album.created_at,
            'album_updated_at': album.updated_at,
        }
        for album in albums
    ]
    return success_response_200(200,'Album list', albums_data)



#API FOR LiveRadio
@swagger_auto_schema(
    method='GET',
    operation_description="Retrieve Live Radio List",
    tags=['app-user']
)
@api_view(['GET'])
@authentication_classes([])  
@permission_classes([])  
def live_radio(request):
    live_radios = LiveRadio.objects.all()
    data = []
    
    for liveradio in live_radios:
        try:
            data.append({
                "liveradio_id":liveradio.id,
                "liveradio_name": str(liveradio.liveradio_name),
                "liveradio_link": liveradio.liveradio_link,
                "liveradio_image": request.build_absolute_uri(liveradio.liveradio_image.url) if liveradio.liveradio_image else None,
            })
        except Exception as e:
            print(f"Error processing record {liveradio.id}: {e}")

    return Response({"status": 200, "message": "Live Radio", "radios": data}, status=200)


#API FOR LiveVideo
@swagger_auto_schema(
    method='GET',
    operation_description="Retrieve Live Video List",
    tags=['app-user']
)
@api_view(['GET'])
@authentication_classes([])  
@permission_classes([])  
def videos(request):
    limit=request.GET.get("limit",10)
    page=request.GET.get("page",1)
    type=request.GET.get("type")
    if not type:
        return success_response_200(400,'type is required','null')
    data=[]
    match type:
        case 'videocategories':
            video_categories=(
                SongCategory.objects.filter(
                    fk_video_category__isnull=False
                )
                .values_list('fk_video_category',flat=True)
            )
            Video_Category_objs=video_category.objects.filter(id__in=video_categories).distinct()
            for Video_Category_obj in Video_Category_objs:
                data.append({
                    'video_category_id':Video_Category_obj.id,
                    'video_category_name':Video_Category_obj.category_name,
                    'video_category_image':get_absolute_url(request,Video_Category_obj.category_image.url) if Video_Category_obj.category_image else None,
                    'created_at':Video_Category_obj.created_at,
                    'updated_at':Video_Category_obj.updated_at,
                })
        case 'categoryvideos':
            category_id=request.GET.get("category_id")
            if not category_id:
                return success_response_200(400,'video category id is required in order to get the video list of video category','null')
            VideoCatObjs = (
                SongCategory.objects.filter(
                    fk_video_category=category_id
                )
                .select_related('fk_video_category')
                .distinct()
            )
            if not VideoCatObjs.exists():
                return success_response_200(400, 'Category does not exist or it has no video assigend', 'null')

            category_id=set()
            for videoCatObj in VideoCatObjs:
                videos_data=[]
                video_ids=set()
                videos_objs=(
                    SongCategory.objects.filter(
                        fk_video_category=videoCatObj.fk_video_category.id,
                        fk_video__isnull=False
                    )    
                )
                for video_obj in videos_objs:
                    if video_obj.fk_video.id not in video_ids:
                        videos_data.append({
                            'video_id':video_obj.fk_video.id,
                            'video_name':video_obj.fk_video.videos_name,
                            'video_image':get_absolute_url(request,video_obj.fk_video.videos_image.url) if video_obj.fk_video.videos_image else None,
                            # 'video_url':get_absolute_url(request,video_obj.fk_video.videos_file.url) if video_obj.fk_video.videos_file else get_absolute_url(request,video_obj.fk_video.videos_url),
                            # 'video_artist_name':video_obj.fk_video.videos_artist_name,
                            # 'videos_description':video_obj.fk_video.videos_description,
                            'videos_duration':video_obj.fk_video.duration,
                        })
                    video_ids.add(video_obj.fk_video.id)
                if videoCatObj.fk_video_category.id not in category_id:
                    data.append({
                        'video_category_id':videoCatObj.fk_video_category.id,
                        'video_category_name':videoCatObj.fk_video_category.category_name,
                        'video_category_image':get_absolute_url(request,videoCatObj.fk_video_category.category_image.url) if videoCatObj.fk_video_category.category_image else None,
                        'created_at':videoCatObj.fk_video_category.created_at,
                        'updated_at':videoCatObj.fk_video_category.updated_at,
                        'videos':videos_data,
                    })
                    category_id.add(videoCatObj.fk_video_category.id)

        case 'videodetails':
            video_id=request.GET.get("video_id")
            if not video_id:
                return success_response_200(400,'video id is required','null')
            video_details=Videos.objects.filter(id=video_id)
            if not  video_details.exists():
                return success_response_200(400,'video does not exists','null')
            
            for video_data in video_details:
                data.append({
                    'video_id':video_data.id,
                    'video_name':video_data.videos_name,
                    'video_image':get_absolute_url(request,video_data.videos_image.url),
                    'video_url':get_absolute_url(request,video_data.videos_file.url) if video_data.videos_file else video_data.videos_url,
                    'video_description':video_data.videos_description,
                    'video_artists_name':video_data.videos_artist_name,
                })

    paginator = Paginator(data,limit)

    try:
        paginated_data=paginator.page(page)
    except PageNotAnInteger:
        paginated_data=paginator.page(1)
    except EmptyPage:
        paginated_data=[]
    
    return JsonResponse({
        'code':200,
        'message':'aviable videos',
        'videos_data':list(paginated_data),
        'page':page,
        'limit':limit,
        'last_page':paginator.num_pages ,
    },status=status.HTTP_200_OK)

        



#     #         "song_id": song_category.songs.id,
#     #         "song_name": song_category.songs.name,
#     #         "song_image": get_absolute_url(request,song_category.songs.image.url) if song_category.songs.image else 'null',
#     #         "song_artist": song_category.artists.name,
#     #         "song_image": get_absolute_url(request,song_category.songs.image.url) if song_category.songs.image else 'null',
#     #         "song_url": get_absolute_url(request, song_category.songs.song_file.url if song_category.songs.song_file else song_category.songs.song_url),
#     #         "song_duration": song_category.songs.duration,
#     #     }
#     #     for song_category in SongsCategory
#     # ]

#     # # Fetch all songs without the category relationship to ensure every song is included
#     # all_songs = Song.objects.all()

#     # # Ensure all songs are included in the response even if they are not related to any SongCategory
#     # for song in all_songs:
#     #     if not any(sc.songs == song for sc in SongsCategory):
#     #         data.append({
#     #             "song_id": song.id,
#     #             "song_name": song.name,
#     #             "song_image": get_absolute_url(request, song.image.url) if song.image else 'null',
#     #             "song_artist": 'null',  # No artist if there's no relation
#     #             "song_url": get_absolute_url(request, song.song_file.url) if song.song_file else get_absolute_url(request,song.song_url),
#     #             "song_duration": song.duration,
#     #         })

#     return success_response_200(200, 'All Songs List', data)





# @swagger_auto_schema(method='GET', operation_description="User for create new user", tags=['app-user'],
#                      request_body=openapi.Schema(
#                          type=openapi.TYPE_OBJECT,
#                          properties={
#                             'song_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Song id'),
#                             'song_name': openapi.Schema(type=openapi.TYPE_STRING, description='Song name'),
#                             'song_image': openapi.Schema(type=openapi.TYPE_STRING, description='Song image'),
#                             'song_created_at': openapi.Schema(type=openapi.TYPE_STRING, description='Song created at'),
#                             'song_updated_at':openapi.Schema(type=openapi.TYPE_STRING, description='Song updated at'),
#                          }
#                      ))
# @api_view(['GET'])
# @authentication_classes([]) 
# @permission_classes([])              
# def songs_list(request):
#     # songs = Song.objects.filter(id=84)
#     base_url = request.build_absolute_uri('/')[:-1]
#     SongsCategory = SongCategory.objects.select_related('songs','artists').all()
#     data=[]
#     data = [
#         {
#             "song_id": song_category.songs.id,
#             "song_name": song_category.songs.name,
#             "song_image": urljoin(base_url, song_category.songs.image.url) if song_category.songs.image else None,
#             "song_url": song_category.songs.song_url,
#             "song_file": urljoin(base_url, song_category.songs.song_file.url) if song_category.songs.song_file else None,
#             "duration": song_category.songs.duration,
#             "artists_name": song_category.artists.name if song_category.artists else None,
#         }
#         for song_category in SongsCategory
#     ]

#     return success_response_200(200,'positive',data)
    
    # songs_data = [
    #     {
    #         'song_id': song.id,
    #         'song_name': song.name,
    #         'song_image': request.build_absolute_uri(song.image.url) if song.image else None,
    #         'song_duration': song.duration,
    #         'song_file': request.build_absolute_uri(song.song_file.url) if song.song_file else None,
    #         'song_url': song.song_url,
    #     }
    #     for song in songs
    # ]
    #return success_response_200(200,'Song list', songs_data)


@swagger_auto_schema(method='GET', operation_description="User for create new user", tags=['app-user'],
                     request_body=openapi.Schema(
                         type=openapi.TYPE_OBJECT,
                         properties={
                            'artist_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Artist id'),
                            'artist_name': openapi.Schema(type=openapi.TYPE_STRING, description='Artist name'),
                            'artist_image': openapi.Schema(type=openapi.TYPE_STRING, description='Artist image'),
                            'artist_created_at': openapi.Schema(type=openapi.TYPE_STRING, description='Artist created at'),
                            'artist_updated_at':openapi.Schema(type=openapi.TYPE_STRING, description='Artist updated at'),
                         }
                     ))
@api_view(['GET'])
@authentication_classes([]) 
@permission_classes([])     
def artists_list(request):
    data=[]
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 15))  # Default limit is 10
    # artists_obj = Artist.objects.all()
    # artists_list = Artist.objects.all().values_list('id',flat=True)
    # all_artists = SongCategory.objects.select_related('artists','songs').all()
    # print(all_artists)
    # for i in all_artists:
    #     data.append({
    #         'artist_id':i.artists.id,
    #        'artist_name':i.artists.name,
    #        'artist_image':urljoin(base_url,i.artists.image.url) if i.artists.image else "null",
    #     })
    # response=[]
    # for artist in artists_obj:
    #     if any(item['artist_id'] == artist.id for item in data):
    #         response.append({
    #             'artist_id':artist.id,
    #             'artist_name':artist.name,
    #             "artist_image" : urljoin(base_url,artist.image.url) if artist.image else "null"
    #         })
    # SongsCategory = SongCategory.objects.values_list('artists_id',flat=True)
    
    # artists = Artist.objects.filter(id__in=SongsCategory).values('id','name','image')
    # data=[{
    #     'artist_id':artist['id'],
    #     'artist_name':artist['name'],
    #     "artist_image" : urljoin(base_url,artist['image']) if artist['image'] else "null",
    # }for artist in artists]

    SongsCategory=SongCategory.objects.distinct().values_list('artists_id',flat=True)
    artists = Artist.objects.filter(id__in=SongsCategory)
    
    
    paginator = Paginator(SongsCategory,limit)

    try:
        # Get the objects for the requested page
        paginated_data = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, default to the first page
        paginated_data = paginator.page(1)
    except EmptyPage:
        # If page is out of range, return an empty list
        paginated_data = []

    for artist in artists:
        if artist.id in paginated_data:
            data.append({
                'artist_id':artist.id,
                'artist_name':artist.name,
                "artist_image" : get_absolute_url(request,artist.image.url) if artist.image else "null",
            })

    return JsonResponse({
        'code': 200,
        'message': 'artists list',
        'data': data,
        'current_page': page,
        'limit': limit, 
        'last_page': paginator.num_pages,
        'first_page':1,
    })

# @api_view(['GET'])
# def songsandalbums(request):
#     artist_id = request.GET.get("artist_id")
#     page = int(request.GET.get("page", 1))
#     per_page = int(request.GET.get("limit", 30))

#     # Fetch all distinct songs where the artist is associated
#     song_records = (
#         SongCategory.objects.filter(artists=artist_id, songs__isnull=False)
#         .select_related("songs")
#         .distinct()
#     )

#     data = []
#     unique_song_ids = set()

#     for record in song_records:
#         song = record.songs

#         if song.id in unique_song_ids:
#             continue
#         unique_song_ids.add(song.id)

#         # Fetch all artists for the current song
#         artist_objs = (
#             SongCategory.objects.filter(songs=song.id, artists__isnull=False)
#             .select_related("artists")
#             .exclude(artists=artist_id)
#             .distinct()
#         )

#         artists = []
#         artist_ids = set()
#         for artist_obj in artist_objs:
#             if artist_obj.artists and artist_obj.artists.id not in artist_ids:
#                 artists.append({
#                     "artist_id": artist_obj.artists.id,
#                     "artist_name": artist_obj.artists.name,
#                     "artist_image": get_absolute_url(request, artist_obj.artists.image.url)
#                     if artist_obj.artists.image else None
#                 })
#                 artist_ids.add(artist_obj.artists.id)

#         # Fetch all albums associated with the artist
#         album_objs = (
#             SongCategory.objects.filter(artists=artist_id, albums__isnull=False)
#             .select_related("albums")
#             .distinct()
#         )

#         albums = []
#         album_ids = set()
#         for album_obj in album_objs:
#             if album_obj.albums and album_obj.albums.id not in album_ids:
#                 albums.append({
#                     "album_id": album_obj.albums.id,
#                     "album_name": album_obj.albums.name,
#                     "album_image": get_absolute_url(request, album_obj.albums.image.url)
#                     if album_obj.albums.image else None
#                 })
#                 album_ids.add(album_obj.albums.id)

#         # Append song details
#         data.append({
#             "song_id": song.id,
#             "song_name": song.name,
#             "song_image": get_absolute_url(request, song.image.url) if song.image else None,
#             "song_duration": song.duration if hasattr(song, "duration") else "00:00:00",
#             "song_url": song.url if hasattr(song, "url") else None,
#             "total_likes": song.total_likes if hasattr(song, "total_likes") else 0,
#             "total_downloads": song.total_downloads if hasattr(song, "total_downloads") else 0,
#             "favourite_count": song.favourite_count if hasattr(song, "favourite_count") else 0,
#             "playlist_count": song.playlist_count if hasattr(song, "playlist_count") else 0,
#             "favourite_status": str(song.favourite_status) if hasattr(song, "favourite_status") else "False",
#             "artists": artists,
#         })

#     # Paginate results
#     data.append({
#         'albums':albums,
#     })
#     paginator = Paginator(data, per_page)
#     paginated_data = paginator.get_page(page)

#     response_data = list(paginated_data)  # Ensure it's a proper list
    
#     # return JsonResponse(
#     #     'code':200,
#     #     'message':"sucess",
#     #     'data':list(paginated_data),
#     # )
#     return paginated_success_response_200(
#         200, "Success", response_data, per_page, paginated_data.number, paginator.num_pages
#     )

# @api_view(['GET'])
# def songsandalbums(request):
#     artist_id = request.GET.get('artist_id')  # Get artist_id from the request
#     page = int(request.GET.get('page', 1))
#     limit = int(request.GET.get('limit',6))

#     if not artist_id:
#         return JsonResponse({'code': 400, 'message': 'Artist ID is required'}, status=400)

    
#     # Get artist details
#     artist = Artist.objects.filter(id=artist_id).first()
#     if not artist:
#         return JsonResponse({'code': 404, 'message': 'Artist not found'}, status=404)

#     # Fetch SongCategory entries with distinct combinations of artist_id, song_id, and album_id
#     song_categories = SongCategory.objects.filter(artists_id=artist_id).select_related('songs', 'albums').values('songs_id', 'albums_id').distinct()

#     # Prepare songs and albums lists
#     songs = []
#     albums = []
#     paginator = Paginator(song_categories,limit)

#     try:
#         # Get the objects for the requested page
#         paginated_data = paginator.page(page)
#     except PageNotAnInteger:
#         # If page is not an integer, default to the first page
#         paginated_data = paginator.page(1)
#     except EmptyPage:
#         # If page is out of range, return an empty list
#         paginated_data = []

#     for song_category in paginated_data:
#         song = song_category['songs_id']
#         album = song_category['albums_id']

#         # Add song details
#         song_obj = Song.objects.filter(id=song).first()
#         if song_obj:
#             songs.append({
#                 'song_id': song_obj.id,
#                 'song_name': song_obj.name,
#                 'song_image': get_absolute_url(request, song_obj.image.url) if song_obj.image else 'null',
#                 'song_url': get_absolute_url(request, song_obj.song_url) if song_obj.song_url else 'null',
#                 'artists':artist.name,
#             })

       
#         # Add album details (only if it hasn't been added yet)
#         album_obj = Album.objects.filter(id=album).first()
#         if album_obj and not any(a['album_id'] == album_obj.id for a in albums):
#             albums.append({
#                 'album_id': album_obj.id,
#                 'album_name': album_obj.name,
#                 'album_image': get_absolute_url(request, album_obj.image.url) if album_obj.image else 'null',
#             })

#     # Return the response
#     return JsonResponse({
#         'code': 200,
#         'message': 'success',
#         'artist_id': artist.id,
#         'artist_name': artist.name,
#         'artist_image': get_absolute_url(request, artist.image.url) if artist.image else 'null',
#         'songs': songs,
#         'albums': albums,
#         'current_page': page,
#         'limit': limit, 
#         'last_page': paginator.num_pages,
#         'first_page':1,
#     })

@api_view(['GET'])
def songsandalbums(request):
    artist_id = request.GET.get('artist_id')  # Get artist_id from the request
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 6))

    if not artist_id:
        return JsonResponse({'code': 400, 'message': 'Artist ID is required'}, status=400)

    # Get artist details
    artist = Artist.objects.filter(id=artist_id).first()
    if not artist:
        return JsonResponse({'code': 404, 'message': 'Artist not found'}, status=404)

    # Fetch distinct SongCategory entries
    song_categories = (
        SongCategory.objects.filter(artists_id=artist_id)
        .select_related('songs', 'albums')
        .values('songs_id', 'albums_id')
        .distinct()
    )

    # Prepare songs and albums lists
    songs = []
    albums = []
    paginator = Paginator(song_categories, limit)

    try:
        paginated_data = paginator.page(page)
    except PageNotAnInteger:
        paginated_data = paginator.page(1)
    except EmptyPage:
        paginated_data = []

    albums_ids=set()
    for song_category in paginated_data:
        song_id = song_category['songs_id']
        album_id = song_category['albums_id']

        # Fetch song details
        song_obj = Song.objects.filter(id=song_id).first()
        if song_obj:
            # Fetch all artists for this song excluding the requested artist_id
            artist_objs = (
                SongCategory.objects.filter(songs=song_id)
                .select_related('artists')
                .distinct()
            )

            artist_list = []
            for artist_obj in artist_objs:
                if artist_obj.artists:
                    artist_list.append({
                        "artist_id": artist_obj.artists.id,
                        "artist_name": artist_obj.artists.name,
                        "artist_image": get_absolute_url(request, artist_obj.artists.image.url)
                        if artist_obj.artists.image else None
                    })

            songs.append({
                'song_id': song_obj.id,
                'song_name': song_obj.name,
                'song_image': get_absolute_url(request, song_obj.image.url) if song_obj.image else None,
                'song_url': get_absolute_url(request, song_obj.song_file.url) if song_obj.song_file else get_absolute_url(request,song_obj.song_url),
                'artists': artist_list,  # ✅ Updated to include list of artists (excluding main artist_id)
            })

        # Fetch album details (only if not already added)
        album_obj = SongCategory.objects.filter(songs__isnull=False,artists=artist.id,albums__isnull=False).distinct()
        for album in album_obj:
            if album.albums.id not in albums_ids:
                albums.append({
                    'album_id':album.albums.id,
                    'album_name':album.albums.name,
                    'album_image':get_absolute_url(request,album.albums.image.url) if album.albums.image else None,
                })
                albums_ids.add(album.albums.id)
        

    # Return the response
    return JsonResponse({
        'code': 200,
        'message': 'success',
        'artist_id': artist.id,
        'artist_name': artist.name,
        'artist_image': get_absolute_url(request, artist.image.url) if artist.image else None,
        'songs': songs,
        'albums': albums,
        'current_page': page,
        'limit': limit,
        'last_page': paginator.num_pages,
        'first_page': 1,
    })


@api_view(['GET'])
def common_albums(request):
    artist_id = request.GET.get('artist_id')
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 10))  # Default limit is 10

    # Fetch data and filter by artist
    SongsCategory = SongCategory.objects.select_related('songs', 'artists', 'albums').filter(artists=artist_id)

    # Create a Paginator object
    paginator = Paginator(SongsCategory, limit)

    try:
        # Get the objects for the requested page
        paginated_data = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, default to the first page
        paginated_data = paginator.page(1)
    except EmptyPage:
        # If page is out of range, return an empty list
        paginated_data = []

    # Prepare response data
    data = [
        {
            "artist_id": song_category.artists.id,
            "artist_name": song_category.artists.name,
            "artist_image": get_absolute_url(request, song_category.artists.image.url) if song_category.artists.image else None,
            "songs": {
                "song_id": song_category.songs.id,
                "song_name": song_category.songs.name,
                "song_artist": song_category.artists.name,
                "song_image": get_absolute_url(request, song_category.songs.image.url) if song_category.songs.image else None,
                "song_url": get_absolute_url(request, song_category.songs.song_url),
                "song_duration": song_category.songs.duration,
            },
            "albums": {
                "album_id": song_category.albums.id,
                "album_name": song_category.albums.name,
                "album_image": get_absolute_url(request, song_category.albums.image.url) if song_category.albums.image else None,
            },
        }
        for song_category in paginated_data
    ]

    # Include pagination metadata
    response = {
        "data": data,
        "pagination": {
            "current_page": page,
            "limit": limit,
            "last_page": paginator.num_pages,
            "total_items": paginator.count,

        },
    }

    return success_response_200(200, "Data fetched successfully", response)
@swagger_auto_schema(method='GET', operation_description="User for create new user", tags=['app-user'],
                     request_body=openapi.Schema(
                         type=openapi.TYPE_OBJECT,
                         properties={
                            'artist_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Artist id'),
                            'artist_name': openapi.Schema(type=openapi.TYPE_STRING, description='Artist name'),
                            'artist_image': openapi.Schema(type=openapi.TYPE_STRING, description='Artist image'),
                            'artist_created_at': openapi.Schema(type=openapi.TYPE_STRING, description='Artist created at'),
                            'artist_updated_at':openapi.Schema(type=openapi.TYPE_STRING, description='Artist updated at'),
                         }
                     ))
@api_view(['GET'])
@authentication_classes([]) 
@permission_classes([])     
def artists_song(request):
    artist_id = request.GET.get('artist_id')
    SongsCategory = SongCategory.objects.select_related('songs', 'artists').filter(artists=artist_id,songs__isnull=False)
    
    data = [
        {
            "artist_id": song_category.artists.id,
            "artist_name": song_category.artists.name,
            "artist_image": get_absolute_url(request, song_category.artists.image.url) if song_category.artists.image else 'null',
            "song_id": song_category.songs.id,
            "song_name":song_category.songs.name,
            "song_artist":song_category.artists.name,
            "song_image": get_absolute_url(request, song_category.songs.image.url) if song_category.songs.image else 'null',
            "song_url": get_absolute_url(request,song_category.songs.song_url),
            "song_duration": song_category.songs.duration,
        }
        for song_category in SongsCategory
    ]

    # all_artists = Artist.objects.all()
    # for artist in all_artists:
    #     if not any(art.artists == artist for art in SongsCategory):
    #         data.append({
    #             'artist_id':artist.id,
    #             "artist_name":artist.name,
    #             "artist_image":urljoin(base_url,artist.image.url) if artist.image else "null",
    #             "song_id": "null",
    #             "song_name":"null",
    #             "song_image": "null",
    #             "song_url": "null",
    #             "song_duration": "null", 
    #         })
    
    # artists = Artist.objects.all()
    # artists_data = [
    #     {
    #         'artist_id': artist.id,
    #         'artist_name': artist.name,
    #         'artist_image': request.build_absolute_uri(artist.image.url) if artist.image else 'null',
    #     }
    #     for artist in artists
    # ]
    # artists_songs = SongCategory.objects.filter()
    
    return success_response_200(200,'Artist list',data )

@api_view(['GET'])
@authentication_classes([]) 
@permission_classes([])     
def recent(request):
    response=[]
    token = extract_token(request)
    if not token:
        return success_response_200(200,'token not found','null')
    LoggedInUserOBJ = CustomUser.objects.filter(remember_token=token).first()
    user_id=LoggedInUserOBJ.id
    recentplayed = RecentPlayed.objects.filter(fk_user=user_id)
    for data in recentplayed:
        favourite_status=FavouriteSong.objects.filter(fk_user=user_id,fk_song=data.fk_song.id).exists()
        Artists=[]
        Artists_obj = (
            SongCategory.objects.filter(songs=data.fk_song.id,artists__isnull=False)
            .select_related('artists')
            .distinct()
        )
        for Artist_obj in Artists_obj:
            Artists.append({
                'artist_id':Artist_obj.artists.id,
                'artist_name':Artist_obj.artists.name,
                'artist_image':get_absolute_url(request,Artist_obj.artists.image.url) if Artist_obj.artists.image else None
            })
        
        response.append({
            'recent_id':data.id,
            'song_id': data.fk_song.id,
            'song_name':data.fk_song.name,
            'song_image':get_absolute_url(request,data.fk_song.image.url),
            'total_likes':data.fk_song.total_likes,
            'total_downloads':data.fk_song.total_downloads,
            'playlist_count':data.fk_song.playlist_count,
            'song_duration':data.fk_song.duration,
            'favourite_count':data.fk_song.favourite_count,
            'favourite_status':favourite_status,
            'total_played':data.fk_song.total_played,
            'song_url':get_absolute_url(request,data.fk_song.song_file.url) if data.fk_song.song_file else get_absolute_url(request,data.fk_song.song_url),
            'artists':Artists,
        })
    return JsonResponse({
        'code':200,
        'message':'Recently Played Songs',
        'songs':response,
    })

@api_view(['GET'])
@authentication_classes([]) 
@permission_classes([])     
def addrecent(request):
    response=[]
    song_id=request.GET.get('song_id')
    token = extract_token(request)
    if not token:
        return success_response_200(200,'token not found','null')
    LoggedInUserObj = CustomUser.objects.filter(remember_token=token).first()
    if not LoggedInUserObj:
        return success_response_200(200,'user not found','null')
    user_id=LoggedInUserObj.id
    
    if not song_id:
        return success_response_200(400,'song id not found','null')
    
    song_obj=Song.objects.get(id=song_id)
    if not song_obj:
        return success_response_200(400,'song not found or it is not assigned to an artist',"null")
    
    user_obj = CustomUser.objects.get(id=user_id)
    if not user_obj:
        return success_response_200(400,'user not found',"null")
    RecentPlayedObj = RecentPlayed.objects.filter(fk_user=user_id,fk_song=song_id).exists()
    RelatedSongs=RecentPlayed.objects.filter(fk_user=user_id).exists()
    if RelatedSongs:#check if the user details is in the table or not
        if RecentPlayedObj:#exists in the table
            Obj = RecentPlayed.objects.filter(fk_user=user_id,fk_song=song_id).first()
            Obj.delete()
            recent = RecentPlayed(
                fk_user = user_obj,
                fk_song = song_obj,
                )
            recent.save()
            SongObj = Song.objects.get(id=song_obj.id)
            SongObj.total_played +=1
            SongObj.save()
            return success_response_200(200,'song added into recent played','null')
        else: #does not exist in the table
            if RecentPlayed.objects.filter(fk_user=user_id).count() < 10:
                recent = RecentPlayed(
                    fk_user = user_obj,
                    fk_song = song_obj,
                    )
                recent.save()
                SongObj = Song.objects.get(id=song_obj.id)
                SongObj.total_played +=1
                SongObj.save()
                return success_response_200(200,'song added into recent played','null')
            else:
                FirstObj = RecentPlayed.objects.filter(fk_user=user_id).first()
                FirstObj.delete()
                recent = RecentPlayed(
                    fk_user = user_obj,
                    fk_song = song_obj,
                    )
                recent.save()
                SongObj = Song.objects.get(id=song_obj.id)
                SongObj.total_played +=1
                SongObj.save()
                return success_response_200(200,'song added into recent played','null')
    else:
        recent = RecentPlayed(
            fk_user = user_obj,
            fk_song = song_obj,
            )
        recent.save()
        SongObj = Song.objects.get(id=song_obj.id)
        SongObj.total_played +=1
        SongObj.save()
        return success_response_200(200,'song added into recent played','null')
        
#API for uploading user image
@swagger_auto_schema(method='POST', operation_description="user image upload", tags=['image-upload'],
                     request_body=openapi.Schema(
                         type=openapi.TYPE_OBJECT,
                         properties={
                            'image': openapi.Schema(type=openapi.TYPE_STRING, description='user image'),
                         }
                     ))
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def uploads(request):
    token = extract_token(request)
    if not token:
        return success_response_200(400,'authentication missing','null')
    image = request.FILES.get("image",None)
    if not image:
        return success_response_200(400,'image missing','null')
    user = CustomUser.objects.get(remember_token=token)
    if not user:
        return success_response_200(400,'user not found','null')
    
    user.image = image
    user.save()
    return JsonResponse({
        'code':200,
        'message':'image uploaded successfully',
        'image': get_absolute_url(request,user.image.url) if user.image else None
    })

@swagger_auto_schema(method='GET', operation_description="Get profile details", tags=['image-upload'],
                     request_body=openapi.Schema(
                         type=openapi.TYPE_OBJECT,
                         properties={
                            'user_id': openapi.Schema(type=openapi.TYPE_STRING, description='if to extract user profile details'),
                         }
                     ))
@api_view(['GET'])
@permission_classes([])
@authentication_classes([])
def profile(request):
    user_id = request.GET.get('user_id',None)
    token = extract_token(request)
    if not token:
        return success_response_200(400,'authentication token not found','null')
    #taking user id or using token for extracting user's details
    if user_id:
        user_obj = CustomUser.objects.filter(id=int(user_id)).first()  
    else:
        user_obj = CustomUser.objects.filter(remember_token=token).first()

    if not user_obj:
        return success_response_200(400,'user not found','null')

    return JsonResponse({
        'code': 200,
        'message': 'user details',
        'fcm_id': user_obj.fcm_id if user_obj.fcm_id else None,
        'image': get_absolute_url(request, user_obj.image.url) if user_obj.image else None,
        'username': user_obj.username if user_obj.username else None,
        'name': user_obj.first_name if user_obj.first_name else None,
        'email': user_obj.email if user_obj.email else None,
        'contact': user_obj.phone_number if user_obj.phone_number else None,
        'birthdate': user_obj.birth_date if user_obj.birth_date else None,
        'country': user_obj.country_id.name if user_obj.country_id else None,
        'timezone': user_obj.timezone if user_obj.timezone else None,
    }, status=200)


@api_view(['POST'])
def update_profile(request):
    token = extract_token(request)
    if not token:
        return success_response_200(400,'authentication token missing','null')
    required_fields=["first_name","last_name","username","phone_number","email","country","timezone","birth_date","image"]
    missing_fields=[field for field in required_fields if not request.data.get(field)]
    if missing_fields:
        return success_response_200(400,f'field missing {','.join(missing_fields)}','null')

    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    username = request.data.get('username')
    phone_number = request.data.get('phone_number')
    email = request.data.get('email')
    country = request.data.get('country')
    timezone = request.data.get('timezone')
    birth_date = request.data.get('birth_date')
    image= request.FILES.get('image')

    try:
        country_obj = Country.objects.get(id=int(country))
    except ObjectDoesNotExist:
        return success_response_200(400, 'Country not found', 'null')       

    phone_number=str(phone_number)
    if not len(phone_number) == 10:
        return success_response_200(400,'length of phone number must be exactly 10')
    
    if CustomUser.objects.filter(username=username).exclude(remember_token=token).exists():
        return success_response_200(400,'user with this username already exisrs',"null")
    
    user=CustomUser.objects.get(remember_token=token)
    if not user:
        return success_response_200(400,'user not found','null')
    
    user.username=username
    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.phone_number = int(phone_number)
    user.country_id = country_obj
    user.timezone = timezone
    user.birth_date = birth_date
    user.image = image
    user.save()
    return JsonResponse({
        'code':200,
        'message':'profile updated successfully',
        'username':user.username,
        'first_name':user.first_name,
        'last_name':user.last_name,
        'email':user.email,
        'phone_number':user.phone_number,
        'user_country':user.country_id.name,
        'user_timezone':user.timezone,
        'image':get_absolute_url(request,user.image.url) if user.image else None,
    })

@api_view(['POST'])
def changepassword(request):
    token = extract_token(request)
    if not token:
        return success_response_200(400,'authentication token missing')
    required_fields = ["new_password","confirm_password"]
    missing_fields = [field for field in required_fields if not request.data.get(field)]
    if missing_fields:
        return success_response_200(400,f'missing fields {','.join(missing_fields)}','null')
    user_obj = CustomUser.objects.get(remember_token = token)
    if user_obj.type != 1:
        return success_response_200(400,'only registered users can access this page')
    old_password = user_obj.password
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")

    if new_password != confirm_password:
        return success_response_200(400,'confirm password does not match new password','null')
    
    encrypted_password = make_password(new_password)
    user_obj.password = encrypted_password
    user_obj.save()
    default_image_path = default_variables.THUMBNAIL_ICON_REACT()
    default_title_path = default_variables.GMAIL_WEBSITE_TITLE
    to_email = user_obj.email
    subject = f'Account Created Successfully! {default_title_path}'
    context = {
        "username":user_obj.username,
        "password":new_password,
        "app_name":default_title_path,
        "current_year":2024,
        "logo_url": default_image_path,
        "create_or_reset":"password has been changed"
    }
    html_content = render_to_string('main_app/password_change_email.html', context)

    send_html_email(to_email, subject, html_content)


    return JsonResponse({
        'code':200,
        'message':'password changed successfully',
        'old_password': old_password,
        'new_password':new_password,
        'confirm_password':confirm_password
    })





    
  
# @api_view(['GET'])
# def videos(request):
#     videos = Videos.objects.all()
#     if not videos:
#         return success_response_200(400,'no videos avaiable currently','null')
#     data=[]
#     for video in videos:
#         data.append({
#             'videos_id':video.id,
#             'videos_name':videos.videos_name,
#             'videos_image':get_absolute_url(request,video.videos_image.url) if video.image else None,
#             'videos_link':video.videos_link,
#             'videos_artist_name':video.videos_artist_name,
#             'videos_description':video.videos_description,
#             'created_at':video.created_at,
#         })
#     return success_response_200(200,'available videos',data)

@api_view(['GET'])
def playlist(request):
    user_id=request.GET.get('user_id')
    if not user_id:
        return success_response_200(400,'user id not found','null')
    playlists = Playlist.objects.filter(user_id=int(user_id))
    if not playlists:
        return success_response_200(400,'no playlist found','null')
    data=[]
    for playlist in playlists:
        data.append({
            'playlist_id':playlist.id,
            'user_id':playlist.user_id.id,
            'playlist_name':playlist.name,
            'created_at':playlist.created_at,
        })
    return success_response_200(200,'avaiable playlists',data)

@api_view(['POST'])
def add_playlist(request):
    data=[]
    user_id=request.GET.get('user_id')
    playlist_name=request.data['playlist_name']
    
    if not playlist_name:
        return success_response_200(400,'playlist name not found','null')
    
    if not user_id:
        return success_response_200(400,'user id not found','null')
    
    user_obj = CustomUser.objects.filter(id=user_id).first()
    if not user_obj:
        return success_response_200(400,'user doesnt exists','null')
    
    playlist,created = Playlist.objects.get_or_create(
        user_id=user_obj,
        name=playlist_name
    )   
    data.append({
        'user_id':user_id,
        'playlist_id':playlist.id,
        'playlist_name':playlist.name,
        'created_at':playlist.created_at,
    })
    if created:
        return success_response_200(200,'playlist added successfully',data)
    else:
        return success_response_200(400,'playlist already exists','null')

@api_view(['POST'])
def remove_playlist(request):
    user_id=request.GET.get('user_id')
    playlist_id=request.GET.get('playlist_id')
    if not user_id:
        return success_response_200(400,'user id not found','null')
    if not playlist_id:
        return success_response_200(400,'playlist id not found','null')
    
    playlist=Playlist.objects.filter(user_id=user_id,id=playlist_id)
    if not playlist:
        return success_response_200(400,'playlist doesnt exists','null')
    playlist.delete()
    
    return success_response_200(200,'playlist removed successfully','null')

@api_view(['GET'])
def playlistsongs(request):
    data=[]
    user_id=request.GET.get('user_id')
    playlist_id = request.GET.get('playlist_id')
    if not user_id:
        return success_response_200(400,'didnt get user id','null')
    if not playlist_id:
        return success_response_200(400,'didnt get playlist id','null')
    
    playlist_songs=Playlist_Songs.objects.filter(user_id=user_id,playlist_id=playlist_id)
    if not playlist_songs:
        return success_response_200(400,'no songs avaialable in the playlist','null')
    
    for playlist_song in playlist_songs:
    # Fetch distinct songs and artists
        song_category_obj = (
            SongCategory.objects.filter(songs=playlist_song.song_id.id)
            .select_related('artists','songs').distinct()  # Optimize query to include artist details
            
        )
        artists=[]
        artist_ids=set()
        for song_category in song_category_obj:
            if song_category.artists:
                if song_category.artists.id not in artist_ids:
                    artists.append({
                        'artist_id': song_category.artists.id,
                        'artist_name': song_category.artists.name,
                        'artist_image': get_absolute_url(request, song_category.artists.image.url) if song_category.artists.image else None
                    })
                    artist_ids.add(song_category.artists.id)
        
        # Append song data along with artist details
        data.append({
            'playlist_song_id': playlist_song.id,
            'playlist_id': playlist_song.playlist_id.id,
            'song_id': playlist_song.song_id.id,
            'song_name': playlist_song.song_id.name,
            'song_image': get_absolute_url(request, playlist_song.song_id.image.url) if playlist_song.song_id.image else None,
            'song_duration': playlist_song.song_id.duration,
            'song_url': get_absolute_url(request, playlist_song.song_id.song_file.url) if playlist_song.song_id.song_file else get_absolute_url(request, playlist_song.song_id.song_url),
            'artists': artists if artists else None,  # Add artist details here
        })
    
    return success_response_200(200,'playlist songs',data)

@api_view(['POST'])
def playlistsongadd(request):
    #data=[]
    user_id=request.GET.get('user_id')
    playlist_id=request.GET.get('playlist_id')
    song_id=request.GET.get('song_id')

    if not user_id:
        return success_response_200(400,'user id not found','null')
    if not playlist_id:
        return success_response_200(400,'playlist id not found','null')
    if not song_id:
        return success_response_200(400,'song id not found','null')
    
    user_obj=CustomUser.objects.filter(id=user_id).first()
    playlist_obj = Playlist.objects.filter(id=playlist_id).first()
    song_obj=Song.objects.filter(id=song_id).first()

    if not user_obj:
        return success_response_200(400,'user doesnt exist','null')
    elif not playlist_obj:
        return success_response_200(400,'playlist doesnt exist','null')
    elif not song_obj:
        return success_response_200(400,'song doesnt exist','null')
    
    if Playlist.objects.filter(user_id=user_id,id=playlist_id).exists():
        if not Playlist_Songs.objects.filter(user_id=user_id,playlist_id=playlist_id,song_id=song_id).exists():
            playlist_song_obj = Playlist_Songs(
                user_id=user_obj,
                playlist_id=playlist_obj,
                song_id=song_obj,
            )
            playlist_song_obj.save()
            song_obj.playlist_count = Playlist_Songs.objects.filter(song_id=song_id).count()
            song_obj.save()
            return success_response_200(200,'song added into the playlist','null')
        else:
            song_obj.playlist_count = Playlist_Songs.objects.filter(song_id=song_id).count()
            song_obj.save()
            return success_response_200(400,'song already present in the playlist','null')
    else:
        return success_response_200(400,'playlist with this user id doesnot exist','null')

    
@api_view(['DELETE'])
def playlistsongremove(request):
    user_id=request.GET.get('user_id')
    playlist_id=request.GET.get('playlist_id')
    song_id=request.GET.get('song_id')

    if not user_id:
        return success_response_200(400,'user id not found','null')
    if not playlist_id:
        return success_response_200(400,'playlist id not found','null')
    if not song_id:
        return success_response_200(400,'song id not found','null')
    song_obj = get_object_or_404(Song,id=song_id)
    try:
        playlist_song=Playlist_Songs.objects.get(user_id=user_id,playlist_id=playlist_id,song_id=song_id)
    except ObjectDoesNotExist:
        return success_response_200(400,'song doesnt exist in the playlist','null')
    playlist_song.delete()
    song_obj.playlist_count = Playlist_Songs.objects.filter(fk_song=song_id).count()
    song_obj.save()
    return success_response_200(200,'song removed from the playlist successfully','null')

@api_view(['GET'])
def playlistsongremoveall(request):
    user_id=request.GET.get("user_id")
    playlist_id=request.GET.get("playlist_id")

    playlist_songs = Playlist_Songs.objects.filter(user_id=user_id,playlist_id=playlist_id)
    if not playlist_songs:
        return success_response_200(400,'playlist does not have any songs','null')
    
    for playlist_song in playlist_songs:
        song_obj = Song.objects.filter(id=playlist_song.song_id.id)
        for song in song_obj:
            playlist_song.delete()
            song.playlist_count=Playlist_Songs.objects.filter(playlist_id=playlist_id,song_id=song.id)
    
    return success_response_200(200,'songs removed from the playlist successfully','null')
    
@api_view(['GET'])
def playlistalbums_add(request):
    playlist_id=request.GET.get("playlist_id")
    album_id=request.GET.get("album_id")
    if not playlist_id:
        return success_response_200(400,'playlist not found','null')
    if not album_id:
        return success_response_200(400,'album not found','null')
    token = extract_token(request)
    if not token:
        return success_response_200(404,'authentication token missing',"null")
    UserOBJ = CustomUser.objects.filter(remember_token=token).first()
    if not UserOBJ:
        return success_response_200(400,'user not found','null')
    if  Playlist_Songs.objects.filter(user_id=UserOBJ.id,playlist_id=playlist_id,fk_album=album_id).exists():
        return success_response_200(400,'album has already been added into the playlist','null')
    AlbumSongs = (
        SongCategory.objects.filter(albums=album_id,songs__isnull=False)
        .distinct()
    )
    for AlbumSong in AlbumSongs:
        if not Playlist_Songs.objects.filter(song_id=AlbumSong.songs.id,playlist_id=playlist_id,user_id=UserOBJ.id).exists():
            object = Playlist_Songs(
                song_id_id=AlbumSong.songs.id,
                playlist_id_id=playlist_id,
                fk_album_id=album_id,
                user_id=UserOBJ,
            )
            object.save()
    return success_response_200(200,"album added into the playlist",'null')

@api_view(['GET'])
def playlistalbums(request):
    token=extract_token(request)
    if not token:
        return success_response_200(400,'invalid authentication','null')
    page=request.GET.get("page",1)
    limit=request.GET.get("limit",10)
    playlist_id=request.GET.get("playlist_id")
    if not playlist_id:
        return success_response_200(400,'playlist id is required')
    UserObj = CustomUser.objects.filter(remember_token=token).first()
    if not UserObj:
        return success_response_200(400,'user not found','null')
    if not Playlist.objects.filter(id=playlist_id,user_id=UserObj.id).exists():
        return success_response_200(400,'playlist does not exists','null')
    PlaylistAlbums=(
        Playlist_Songs.objects.filter(playlist_id=playlist_id,user_id=UserObj.id)
        .values_list('fk_album',flat=True)
        .distinct()
    )
    AlbumsObj=Album.objects.filter(id__in=PlaylistAlbums)
    data=[]
    for AlbumObj in AlbumsObj:
        data.append({
            'album_id':AlbumObj.id,
            'album_name':AlbumObj.name,
            'album_image':get_absolute_url(request,AlbumObj.image.url) if AlbumObj.image else None,
        })
    paginator =Paginator(data,limit)

    try:
        paginated_data = paginator.page(page)
    except PageNotAnInteger:
        paginated_data = paginator.page(1)
    except EmptyPage:
        paginated_data= []

    return JsonResponse({
        'code':200,
        'message':'list of albums added into playlist',
        'playlist_albums':list(paginated_data),
        'page':page,
        'limit':limit,
        'last_page':paginator.num_pages,
    },status=status.HTTP_200_OK)
    
@api_view(['GET'])
def playlistalbums_remove(request):
    token=extract_token(request)
    if not token:
        return success_response_200(400,'invalid authentication','null')
    UserObj=CustomUser.objects.filter(remember_token=token).first()
    if not UserObj:
        return success_response_200(400,'user not found','null')
    playlist_id=request.GET.get("playlist_id")
    album_id=request.GET.get("album_id")
    AlbumObj = Playlist_Songs.objects.filter(fk_album=album_id,playlist_id=playlist_id,user_id=UserObj.id)
    AlbumObj.delete()
    return success_response_200(200,'album removed successfully','null')

@api_view(['POST'])
def playlistalbums_removeall(request):
    token = extract_token(request)
    if not token:
        return success_response_200(400,'invalid authentication','null')
    UserObj=CustomUser.objects.filter(remember_token=token).first()
    if not UserObj:
        return success_response_200(400,'user not found','null')
    playlist_id = request.GET.get("playlist_id")
    PlaylistObj= Playlist_Songs.objects.filter(user_id=UserObj.id,playlist_id=playlist_id,fk_album__isnull=False)
    if not PlaylistObj.exists():
        return success_response_200(400,'playlist does not have any albums added in it','null')
    PlaylistObj.delete()
    return success_response_200(200,'all albums removed from the playlist','null')
    

@api_view(['GET'])
def favourite(request):
    required_fields = ["user_id", "limit", "page"]
    missing_fields = [field for field in required_fields if not request.GET.get(field)]
    if missing_fields:
        return success_response_200(
            400, f"{', '.join(missing_fields)} fields are missing", "null"
        )

    # Get query parameters
    user_id = request.GET.get("user_id")
    limit = int(request.GET.get("limit"))
    page = int(request.GET.get("page"))

    # Validate user and song existence
    user_obj = CustomUser.objects.filter(id=user_id).first()
    if not user_obj:
        return success_response_200(400, "User does not exist", "null")

    # Fetch favourite songs
    favourite_songs = FavouriteSong.objects.filter(fk_user=user_obj)

    if not favourite_songs.exists():
        return success_response_200(400, "No favourite songs found", "null")

    # Paginate the results
    paginator = Paginator(favourite_songs, limit)
    try:
        paginated_data = paginator.page(page)
    except PageNotAnInteger:
        paginated_data = paginator.page(1)
    except EmptyPage:
        paginated_data = []

    data=[]
    artists = []
    artists_id = set()
    for favourite_song in paginated_data:
        artist_obj = (
            SongCategory.objects.filter(songs=favourite_song.fk_song.id)
            .select_related('songs','artists')
            .distinct()
            )
        
        for artist in artist_obj:
            if artist.artists.id not in artists_id:
                artists.append({
                    'artist_id': artist.artists.id,
                    'artist_name': artist.artists.name,
                    'artist_image': get_absolute_url(request, artist.artists.image.url) if artist.artists.image else None,
                })
                artists_id.add(artist.artists.id)

        data.append({
            'favourite_id':favourite_song.id,
            'song_id':favourite_song.fk_song.id,
            'song_name':favourite_song.fk_song.name,
            'song_image':get_absolute_url(request,favourite_song.fk_song.image.url) if favourite_song.fk_song.image else None,
            'song_duration':favourite_song.fk_song.duration,
            'artists':artists
        })


    # Return paginated response
    return paginated_success_response_200(200,'favourite songs',data,limit,page,paginator.num_pages)

@api_view(['POST'])
def addfavourite(request):
    user_id=request.GET.get('user_id')
    song_id=request.GET.get('song_id')
    if not user_id:
        return success_response_200(400,'didnt get user id','null')
    if not song_id:
        return success_response_200(400,'didnt get song id','null')
    user_obj = CustomUser.objects.filter(id=user_id).first()
    song_obj = Song.objects.filter(id=song_id).first()
    if not user_obj:
        return success_response_200(400,'user doesnt exist','null')
    elif not song_obj:
        return success_response_200(400,'song doesnt exist','null')
    present,created = FavouriteSong.objects.get_or_create(
        fk_user=user_obj,
        fk_song=song_obj
    )
    if created:
        song_obj.favourite_count = FavouriteSong.objects.filter(fk_song=song_id).count()
        song_obj.save()
        return success_response_200(200,'song added into favourites','null')
    else:
        song_obj.favourite_count = FavouriteSong.objects.filter(fk_song=song_id).count()
        song_obj.save()
        return success_response_200(400,'song already present in the playlist','null')
    
@api_view(['GET'])
def removefavourite(request):
    user_id=request.GET.get('user_id')
    song_id=request.GET.get('song_id')
    if not user_id:
        return success_response_200(400,'didnt get user id','null')
    if not song_id:
        return success_response_200(400,'didnt get song id','null')
    user_obj = CustomUser.objects.filter(id=user_id).first()
    song_obj = Song.objects.filter(id=song_id).first()
    if not user_obj:
        return success_response_200(400,'user doesnt exist','null')
    elif not song_obj:
        return success_response_200(400,'song doesnt exist','null')
    
    favourtie_obj = FavouriteSong.objects.filter(fk_user=user_id,fk_song=song_id).first()
    if not favourtie_obj:
        return success_response_200(400,'invalid song id','null')
    favourtie_obj.delete()
    song_obj.favourite_count = FavouriteSong.objects.filter(fk_song=song_id).count()
    song_obj.save()
    return success_response_200(200,'song removed from the favourites successfully','null')

@api_view(['GET'])
def like_unlike(request):
    required_fields=['user_id','song_id']
    missing_fields = [field for field in required_fields if not request.GET.get(field)]
    if missing_fields:
        return success_response_200(400,f'{', '.join(missing_fields)} field(s) is missing','null')
    
    user_id=request.GET.get('user_id')  
    song_id=request.GET.get('song_id')
    
    user_obj=get_object_or_404(CustomUser,id=user_id)
    song_obj = get_object_or_404(Song,id=song_id)

    songlike,created = SongLike.objects.get_or_create(fk_user=user_obj,fk_song=song_obj)

    if not created:
        songlike.is_liked= not songlike.is_liked
        songlike.save()
        action='liked' if songlike.is_liked else 'disliked'
    else:
        songlike.is_liked=True
        songlike.save()
        action='liked'

    song_obj.total_likes = SongLike.objects.filter(fk_song=song_id,is_liked=True).count()
    song_obj.save()
    return success_response_200(200,f'song {action}','null')

    
@api_view(['GET'])
def songdownload(request):
    required_fields=['user_id','song_id']
    missing_fields = [field for field in required_fields if not request.GET.get(field)]
    if missing_fields:
        return success_response_200(400,f'{', '.join(missing_fields)} field(s) is missing','null')
    
    user_id=request.GET.get('user_id')  
    song_id=request.GET.get('song_id')
    
    user_obj=get_object_or_404(CustomUser,id=user_id)
    song_obj = get_object_or_404(Song,id=song_id)

    if not Downloaded_Songs.objects.filter(fk_user=user_id,fk_song=song_id,is_downloaded=True):
        songdownload = Downloaded_Songs(
            fk_user=user_obj,
            fk_song=song_obj,
            is_downloaded=True
        )
        songdownload.save()
        song_obj.total_downloads = Downloaded_Songs.objects.filter(is_downloaded=True,fk_song=song_id).count()
        song_obj.save()
        return success_response_200(200,'song downloaded successfully','null')
    else:
        song_obj.total_downloads = Downloaded_Songs.objects.filter(is_downloaded=True,fk_song=song_id).count()
        song_obj.save()
        return success_response_200(400,'song has already been downloaded','null')

@api_view(['GET'])
def removefromdownloads(request):
    required_fields=["type","user_id"]
    missing_fields=[field for field in required_fields if not request.GET.get(field)]
    if missing_fields:
        return success_response_200(400,f'{', '.jon(missing_fields)} field(s) is missing','null')
    type=request.GET.get('type')
    user_id = request.GET.get('user_id')
    match type:
        case 'song':
            song_id = request.GET.get("song_id")
            if not song_id:
                return success_response_200(400,'song id not found','null')
            Downloaded_obj = get_object_or_404(Downloaded_Songs,fk_user=user_id,fk_song=song_id)
            Downloaded_obj.delete()
            song_obj = get_object_or_404(Song,id=song_id)
            song_obj.total_downloads=Downloaded_Songs.objects.filter(is_downloaded=True,fk_song=song_id).count()
            song_obj.save()
            return success_response_200(200,'song removed from the downloads successfully','null')
        case 'album':
            return success_response_200(200,'temporary','null')
        

@api_view(['GET'])
def songdetail(request):
    required_fields=["song_id","user_id"]
    missing_fields=[field for field in required_fields if not request.GET.get(field)]
    if missing_fields:
        return success_response_200(400,f'{', '.jon(missing_fields)} field(s) is missing','null')
    user_id=request.GET.get("user_id")
    song_id=request.GET.get("song_id")

    song_obj=get_object_or_404(Song,id=song_id)
    favourite=FavouriteSong.objects.filter(fk_song=song_id,fk_user=user_id).first()
    artists=[]
    data=[]
    artists_id=set()
    if song_obj:
        #this query will take all of the song artists assigned to the song
        artists_obj = (
            SongCategory.objects.filter(songs=song_obj.id)
            .select_related('songs','artists')
            .distinct()
        )
        #this query will extract all of the song artists only assigned to the songs
        # artists_obj = (SongCategory.objects.filter(songs=song_obj.id) \
        #     .filter(albums__isnull=True) \
        #     .select_related('songs','artists')\
        #     .distinct()
        # )
        
        for artist in artists_obj:
            if artist.artists:
                if artist.artists.id not in artists_id:
                    artists.append({
                        'artist_id':artist.artists.id if artist.artists.id else None,
                        'artist_name':artist.artists.name if artist.artists.name else None,
                        'artist_image':get_absolute_url(request,artist.artists.image.url) if artist.artists.image.url else None,
                    })
                artists_id.add(artist.artists.id)
        
        data.append({
            'song_id':song_obj.id,
            'song_name':song_obj.name,
            'song_image':get_absolute_url(request,song_obj.image.url) if song_obj.image else None,
            'song_duration':song_obj.duration,
            'totlal_likes':song_obj.total_likes,
            'total_downloads':song_obj.total_downloads,
            'song_url':get_absolute_url(request,song_obj.song_file.url) if song_obj.song_file else get_absolute_url(request,song_obj.song_url),
            'favourite_count':song_obj.favourite_count,
            'playlist_count':song_obj.playlist_count,
            'favourite_status':"True" if favourite else "False",
            'artists':artists,
        })


    return success_response_200(200,'song details',data)
        
@api_view(['GET'])
def termsandpolicies(request):
    type=request.GET.get('type')
    data=[]
    if not type:
        return success_response_200(400,'type not found')
    match type:
        case 'terms':
            terms = TermsOfService.objects.first()
            data.append({
                'title':terms.title,
                'description':terms.description,
            })
            return success_response_200(400,'Terms of Service',data)
        case 'privacy':
            privacy = PrivacyPolicy.objects.first()
            data.append({
                'title':privacy.title,
                'description':privacy.description,
            })
            return success_response_200(400,'Privacy Policy',data)
        
@api_view(['GET'])
def introslider(request):
    sliders=Introduction_Slider.objects.all()
    if not sliders:
        return success_response_200(400,'no introduction slider found','null')
    data=[]
    for slider in sliders:
        data.append({
            'slider_id':slider.id,
            'slider_image':get_absolute_url(request,slider.image.url) if slider.image else None,
            'slider_text':slider.text,
            'created_at':slider.created_at,
        })
    return success_response_200(200,'available introduction sliders',data)

@api_view(['POST'])
def introslideradd(request):
    slider_image=request.FILES.get('slider_image')
    slider_text=request.GET.get('slider_text')

    slider_obj = Introduction_Slider(
        image=slider_image,
        text=slider_text,
    )
    slider_obj.save()
    return success_response_200(200,'introslider added','null')

# @api_view(['GET'])
# def recommended(request):
#     required_fields = ["user_id","limit","page"]
#     missing_fields = [field for field in required_fields if not request.GET.get(field)]
#     if missing_fields:
#         return success_response_200(400,f'{', '.join(missing_fields)} are missing','null')
#     user_id=request.GET.get("user_id")
#     limit=request.GET.get("limit")
#     page=request.GET.get("page")

#     Recommended_Tracks = RecommendedTracks.objects.all().select_related('fk_song')[:20]
#     if not Recommended_Tracks:
#         return success_response_200(400,'no data available','null')
#     paginator = Paginator(Recommended_Tracks, limit)
#     try:
#         paginated_data = paginator.page(page)
#     except PageNotAnInteger:
#         paginated_data = paginator.page(1)
#     except EmptyPage:
#         paginated_data = []
#     data=[]
#     artists=[]
#     artists_id=set()
#     for Recommended_Track in paginated_data:
#         Artist_and_songs=SongCategory.objects.filter(songs=Recommended_Track.fk_song.id,artists__isnull=False).select_related('artists').distinct()
#         favourite = FavouriteSong.objects.filter(fk_user=user_id,fk_song=Recommended_Track.fk_song.id)
#         for artist in Artist_and_songs:
#             if artist.artists.id not in artists_id:
#                 artists.append({
#                 'artist_id':artist.artists.id if artist.artists.id else None,
#                 'artist_name':artist.artists.name if artist.artists.name else None,
#                 'artist_image':get_absolute_url(request,artist.artists.image.url) if artist.artists.image else None,
#                 })
#             artists_id.add(artist.artists.id)
#         data.append({
#             'recommended_id':Recommended_Track.id,
#             'song_id':Recommended_Track.fk_song.id,
#             'song_name':Recommended_Track.fk_song.name,
#             'song_image':get_absolute_url(request,Recommended_Track.fk_song.image.url) if Recommended_Track.fk_song.image else None,
#             'song_duration':Recommended_Track.fk_song.duration,
#             'song_url':get_absolute_url(request,Recommended_Track.fk_song.song_file.url) if Recommended_Track.fk_song.song_file else get_absolute_url(request,Recommended_Track.fk_song.song_url),
#             'total_likes':Recommended_Track.fk_song.total_likes,
#             'total_downloads':Recommended_Track.fk_song.total_downloads,
#             'favourite_count':Recommended_Track.fk_song.favourite_count,
#             'playlist_count':Recommended_Track.fk_song.playlist_count,
#             'favourite_status': "True" if favourite else "False",
#             'artists':artists,
#         })





#         # Artists_and_Songs = SongCategory.objects.filter(songs=Recommended_Track.fk_song.id).select_related('artists','songs')
#         # favourite = FavouriteSong.objects.filter(fk_user=user_id,fk_song=Recommended_Track.fk_song.id).exists()
#         # for artist in Artists_and_Songs:
#         #     if artist.artists.id not in artists_id:
#         #         artists.append({
#         #         'artist_id':artist.artists.id if artist.artists.id else None,
#         #         'artist_name':artist.artists.name if artist.artists.name else None,
#         #         'artist_image':get_absolute_url(request,artist.artists.image.url) if artist.artists.image else None,
#         #         })
#         #     artists_id.add(artist.artists.id)
#         # data.append({
#         #     'recommended_id':Recommended_Track.id,
#         #     'song_id':Recommended_Track.fk_song.id,
#         #     'song_name':Recommended_Track.fk_song.name,
#         #     'song_image':get_absolute_url(request,Recommended_Track.fk_song.image.url) if Recommended_Track.fk_song.image else None,
#         #     'song_duration':Recommended_Track.fk_song.duration,
#         #     'song_url':get_absolute_url(request,Recommended_Track.fk_song.song_file.url) if Recommended_Track.fk_song.song_file else get_absolute_url(request,Recommended_Track.fk_song.song_url),
#         #     'total_likes':Recommended_Track.fk_song.total_likes,
#         #     'total_downloads':Recommended_Track.fk_song.total_downloads,
#         #     'favourite_count':Recommended_Track.fk_song.favourite_count,
#         #     'playlist_count':Recommended_Track.fk_song.playlist_count,
#         #     'favourite_status': "True" if favourite else "False",
#         #     'artists':artists,
#         # })
#     return paginated_success_response_200(200,'Recommended Tracks',data,limit,page,paginator.num_pages)


@api_view(['GET'])
def recommended(request):
    required_fields = ["user_id", "limit", "page"]
    missing_fields = [field for field in required_fields if not request.GET.get(field)]
    if missing_fields:
        return success_response_200(400, f'{", ".join(missing_fields)} are missing', 'null')

    user_id = request.GET.get("user_id")
    limit = int(request.GET.get("limit"))
    page = int(request.GET.get("page"))

    # Fetch all recommended tracks with related song data
    recommended_tracks = (
        RecommendedTracks.objects.select_related('fk_song')
        .filter(fk_song__isnull=False)[:20]
    )

    if not recommended_tracks.exists():
        return success_response_200(400, 'No data available', 'null')

    # Paginate the results
    paginator = Paginator(recommended_tracks, limit)
    try:
        paginated_data = paginator.page(page)
    except PageNotAnInteger:
        paginated_data = paginator.page(1)
    except EmptyPage:
        paginated_data = []

    # Fetch artist data for all songs in the paginated results
    song_ids = [track.fk_song.id for track in paginated_data]
    artists_and_songs = SongCategory.objects.filter(
        songs__in=song_ids, artists__isnull=False
    ).select_related('artists').distinct()

    # Build a dictionary to group artists by song ID
    artists_by_song = {}
    for item in artists_and_songs:
        song_id = item.songs.id
        if song_id not in artists_by_song:
            artists_by_song[song_id] = []
        if item.artists:
            artists_by_song[song_id].append({
                'artist_id': item.artists.id,
                'artist_name': item.artists.name,
                'artist_image': get_absolute_url(request, item.artists.image.url) if item.artists.image else None,
            })

    # Prepare the response data
    data = []
    for track in paginated_data:
        song = track.fk_song
        favourite_status = FavouriteSong.objects.filter(fk_user=user_id, fk_song=song.id).exists()
        data.append({
            'recommended_id': track.id,
            'song_id': song.id,
            'song_name': song.name,
            'song_image': get_absolute_url(request, song.image.url) if song.image else None,
            'song_duration': song.duration,
            'song_url': get_absolute_url(request, song.song_file.url) if song.song_file else get_absolute_url(request, song.song_url),
            'total_likes': song.total_likes,
            'total_downloads': song.total_downloads,
            'favourite_count': song.favourite_count,
            'playlist_count': song.playlist_count,
            'favourite_status': "True" if favourite_status else "False",
            'artists': artists_by_song.get(song.id, []),  # Get artists for this song
        })

    return paginated_success_response_200(200, 'Recommended Tracks', data, limit, page, paginator.num_pages)




# @api_view(['POST'])
# def addrecommended(request):
#     song_id=request.GET.get("song_id")
#     song_obj = Song.objects.filter(id=song_id).first()
#     recommended = RecommendedTracks(fk_song = song_obj)
#     recommended.save()
#     return success_response_200(200,'mkc','null')

#my code 101ms
# @api_view(['GET'])
# def album_details(request):
#     required_fields=["user_id","album_id","artist_id","page","limit"]
#     missing_fields = [field for field in required_fields if not request.GET.get(field)]
#     if missing_fields:
#         return success_response_200(400,f'{' ,'.join(missing_fields)} missing fields','null')
#     user_id=request.GET.get("user_id")
#     album_id=request.GET.get("album_id")
#     artist_id=request.GET.get("artist_id")
#     limit=request.GET.get("limit")
#     page=request.GET.get("page")

#     albums_data = (SongCategory.objects.filter(albums=album_id)
#                     .distinct()
#                     )
#     paginator = Paginator(albums_data,limit)

#     try:
#         paginated_data = paginator.page(page)
#     except PageNotAnInteger:
#         paginated_data = paginator.page(1)
#     except EmptyPage:
#         paginated_data = []
    
#     data=[]
#     artists=[]
#     artists_id=[]
#     artist_id=set()
#     songs_id=set()
#     for album_data in paginated_data:
#     # Get all unique songs for the album
#         song_objects = (
#             SongCategory.objects.filter(albums=album_data.albums.id)
#             .select_related('songs', 'artists')
#             .distinct()
#         )

#         for song_obj in song_objects:
#             # Check if the song is already processed
#             if song_obj.songs.id not in songs_id:
#                 # Get all artists associated with the current song
#                 artist_objects = (
#                     SongCategory.objects.filter(songs=song_obj.songs.id, albums=album_data.albums.id)
#                     .exclude(artists__isnull=True)  # Exclude entries without associated artists
#                     .select_related('artists')
#                     .distinct()
#                 )

#                 # Prepare artist details (only if there are artists for the song)
#                 artists = []
#                 for artist_obj in artist_objects:
#                     if artist_obj.artists.id not in artist_id:
#                         artists.append({
#                             'artist_id': artist_obj.artists.id,
#                             'artist_name': artist_obj.artists.name,
#                             'artist_image': get_absolute_url(request, artist_obj.artists.image.url)
#                             if artist_obj.artists.image else None,
#                         })
#                         artist_id.add(artist_obj.artists.id)

#                 # Check if the song is marked as a favorite
#                 favourite = FavouriteSong.objects.filter(fk_user=user_id, fk_song=song_obj.songs.id).exists()

#                 # Add song details
#                 data.append({
#                     'album_id': album_data.albums.id,
#                     'song_id': song_obj.songs.id,
#                     'song_name': song_obj.songs.name,
#                     'song_image': get_absolute_url(request, song_obj.songs.image.url)
#                     if song_obj.songs.image else None,
#                     'song_duration': song_obj.songs.duration,
#                     'song_url': get_absolute_url(request, song_obj.songs.song_file.url)
#                     if song_obj.songs.song_file else get_absolute_url(request, song_obj.songs.song_url),
#                     'total_likes': song_obj.songs.total_likes,
#                     'total_downloads': song_obj.songs.total_downloads,
#                     'favourite_count': song_obj.songs.favourite_count,
#                     'playlist_count': song_obj.songs.playlist_count,
#                     'favourite_status': "True" if favourite else "False",
#                     'artists': artists,  # Only artists explicitly linked to this song
#                 })

#                 # Mark song as processed
#                 songs_id.add(song_obj.songs.id)


#     for album_data in paginated_data:
#         song_obj = (
#             SongCategory.objects.filter(id=album_data.id)
#             .select_related('songs','artists')
#             .distinct()
#         )
#         for song in song_obj:
#             favourite = FavouriteSong.objects.filter(fk_user=user_id,fk_song=song.id)
#             if not song.songs.id in songs_id:
#                 artists_obj = (
#                     SongCategory.objects.filter(albums=album_data.albums.id,songs=song.songs.id)
#                     .select_related('songs','artists')
#                     .distinct()
#                 )
#                 for artist in artists_obj:
#                     if not artist.artists.id in artist_id:
#                         artists.append({
#                             'artist_id':artist.artists.id if artist.artists.id else None,
#                             'artist_name':artist.artists.name if artist.artists.name else None,
#                             'artist_image':get_absolute_url(request,artist.artists.image.url) if artist.artists.image else None,
#                         })
#                     artist_id.add(artist.artists.id)
#                 # artists_obj = (
#                 #     SongCategory.objects.filter(songs=song.id)
#                 #     .select_related('songs','artists')
#                 #     .distinct()
#                 # )
#                 # for artist in artists_obj:
#                 #     if not artist.artists.id in artist_id:
#                 #         artists.append({
#                 #             'artist_id':artist.artists.id if artist.artists.id else None,
#                 #             'artist_name':artist.artists.name if artist.artists.name else None,
#                 #             'artist_image': get_absolute_url(request,artist.artists.image.url) if artist.artists.image else None,
#                 #         })
#                 #     artist_id.add(artist.artists.id)
#                     data.append({
#                         'album_id':album_data.albums.id,
#                         'song_id':song.songs.id,
#                         'song_name':song.songs.name,
#                         'song_image':get_absolute_url(request,song.songs.image.url) if song.songs.image else None,
#                         'song_duration':song.songs.duration,
#                         'song_url':get_absolute_url(request,song.songs.song_file.url) if song.songs.song_file else get_absolute_url(request,song.songs.song_url),
#                         'total_likes':song.songs.total_likes,
#                         'total_downloads':song.songs.total_downloads,
#                         'favourite_count':song.songs.favourite_count,
#                         'playlist_count':song.songs.playlist_count,
#                         'favourite_status': "True" if favourite else "False",
#                         'artists':artists,
#                     })
#                     songs_id.add(song.songs.id)
        
#     return paginated_success_response_200(200,'album data',data,limit,page,paginator.num_pages)

# @api_view(['GET'])
# def album_details(request):
#     required_fields = ["user_id", "album_id", "artist_id", "page", "limit"]
#     missing_fields = [field for field in required_fields if not request.GET.get(field)]
#     if missing_fields:
#         return success_response_200(400, f"{', '.join(missing_fields)} missing fields", 'null')
    
#     user_id = request.GET.get("user_id")
#     album_id = request.GET.get("album_id")
#     limit = int(request.GET.get("limit"))
#     page = int(request.GET.get("page"))

#     # Fetch all distinct songs for the given album
#     albums_data = (
#         SongCategory.objects.filter(albums=album_id)
#         .select_related('songs', 'artists')
#         .distinct()
#     )

#     # Paginate the data
#     paginator = Paginator(albums_data, limit)
#     try:
#         paginated_data = paginator.page(page)
#     except PageNotAnInteger:
#         paginated_data = paginator.page(1)
#     except EmptyPage:
#         paginated_data = []

#     # Prepare the response data
#     data = []
#     songs_id = set()  # To track processed songs

#     for album_data in paginated_data:
#         # Fetch unique songs for the album
#         song_objects = (
#             SongCategory.objects.filter(albums=album_id)
#             .select_related('songs', 'artists')
#             .distinct()
#         )

#         for song_obj in song_objects:
#             if song_obj.songs.id not in songs_id:
#                 # Fetch artists associated with the song
#                 artist_objects = (
#                     SongCategory.objects.filter(songs=song_obj.songs.id, albums=album_id)
#                     .exclude(artists__isnull=True)
#                     .select_related('artists')
#                     .distinct()
#                 )

#                 # Use a set to track artist IDs for this song
#                 song_artist_ids = set()
#                 artists = []

#                 for artist_obj in artist_objects:
#                     if artist_obj.artists.id not in song_artist_ids:
#                         artists.append({
#                             'artist_id': artist_obj.artists.id,
#                             'artist_name': artist_obj.artists.name,
#                             'artist_image': get_absolute_url(request, artist_obj.artists.image.url)
#                             if artist_obj.artists.image else None,
#                         })
#                         song_artist_ids.add(artist_obj.artists.id)

#                 # Check if the song is marked as a favorite
#                 favourite = FavouriteSong.objects.filter(fk_user=user_id, fk_song=song_obj.songs.id).exists()

#                 # Add song details to the response
#                 data.append({
#                     'album_id': album_id,
#                     'song_id': song_obj.songs.id,
#                     'song_name': song_obj.songs.name,
#                     'song_image': get_absolute_url(request, song_obj.songs.image.url)
#                     if song_obj.songs.image else None,
#                     'song_duration': song_obj.songs.duration,
#                     'song_url': get_absolute_url(request, song_obj.songs.song_file.url)
#                     if song_obj.songs.song_file else get_absolute_url(request, song_obj.songs.song_url),
#                     'total_likes': song_obj.songs.total_likes,
#                     'total_downloads': song_obj.songs.total_downloads,
#                     'favourite_count': song_obj.songs.favourite_count,
#                     'playlist_count': song_obj.songs.playlist_count,
#                     'favourite_status': "True" if favourite else "False",
#                     'artists': artists,  # Distinct artists
#                 })

#                 # Mark song as processed
#                 songs_id.add(song_obj.songs.id)

#     album_songs=(
#         SongCategory.objects.filter(id=album_id)
#         .filter(artists__isnull=True)
#         .select_related('songs','albums')
#         .distinct()
#     )
#     for song in album_songs:
#         if song.songs.id not in data['song_id']:
#             data.append({
#                 'album_id': album_id,
#                     'song_id': song_obj.songs.id,
#                     'song_name': song.songs.name,
#                     'song_image': get_absolute_url(request, song.songs.image.url) if song.songs.image else None,
#                     'song_duration': song.songs.duration,
#                     'song_url': get_absolute_url(request, song.songs.song_file.url) if song.songs.song_file else get_absolute_url(request, song.songs.song_url),
#                     'total_likes': song.songs.total_likes,
#                     'total_downloads': song.songs.total_downloads,
#                     'favourite_count': song.songs.favourite_count,
#                     'playlist_count': song.songs.playlist_count,
#                     'favourite_status': "True" if favourite else "False",
#                     'artists': [],
#             })

#     # Return the response
#     return success_response_200(200, 'Success', data)

# from django.db.models import Prefetch, Q
# from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# def album_details(request):
    required_fields = ["user_id", "album_id", "page", "limit"]
    missing_fields = [field for field in required_fields if not request.GET.get(field)]
    if missing_fields:
        return success_response_200(400, f"{', '.join(missing_fields)} missing fields", 'null')

    user_id = request.GET.get("user_id")
    album_id = request.GET.get("album_id")
    limit = int(request.GET.get("limit"))
    page = int(request.GET.get("page"))

    # Fetch songs and related artists in one query
    song_objects = (
        SongCategory.objects.filter(albums=album_id)
        .select_related('songs')
        .prefetch_related(
            Prefetch(
                'artists',
                queryset=Artist.objects.all().distinct(),
                to_attr='related_artists'
            )
        )
        .distinct()
    )

    # Paginate the data
    paginator = Paginator(song_objects, limit)
    try:
        paginated_data = paginator.page(page)
    except PageNotAnInteger:
        paginated_data = paginator.page(1)
    except EmptyPage:
        paginated_data = []

    # Prepare the response data
    data = []
    songs_id = set()

    for song_obj in paginated_data:
        if song_obj.songs.id not in songs_id:
            # Prepare artists data
            artist = getattr(song_obj, 'related_artists', None)
            artists = [
                {
                    'artist_id': artist.id if artist else None,
                    'artist_name': artist.name if artist else None,
                    'artist_image': get_absolute_url(request, artist.image.url) if artist and artist.image else None,
                }
            ]



            # Check if the song is marked as a favorite
            favourite = FavouriteSong.objects.filter(fk_user=user_id, fk_song=song_obj.songs.id).exists()

            # Add song details to the response
            data.append({
                'album_id': album_id,
                'song_id': song_obj.songs.id,
                'song_name': song_obj.songs.name,
                'song_image': get_absolute_url(request, song_obj.songs.image.url)
                if song_obj.songs.image else None,
                'song_duration': song_obj.songs.duration,
                'song_url': get_absolute_url(request, song_obj.songs.song_file.url)
                if song_obj.songs.song_file else get_absolute_url(request, song_obj.songs.song_url),
                'total_likes': song_obj.songs.total_likes,
                'total_downloads': song_obj.songs.total_downloads,
                'favourite_count': song_obj.songs.favourite_count,
                'playlist_count': song_obj.songs.playlist_count,
                'favourite_status': "True" if favourite else "False",
                'artists': artists,
            })

            # Mark song as processed
            songs_id.add(song_obj.songs.id)

    # Handle songs with no artists
    unassociated_songs = (
        SongCategory.objects.filter(albums=album_id, artists__isnull=True)
        .select_related('songs')
        .distinct()
    )
    for song_obj in unassociated_songs:
        if song_obj.songs.id not in songs_id:
            data.append({
                'album_id': album_id,
                'song_id': song_obj.songs.id,
                'song_name': song_obj.songs.name,
                'song_image': get_absolute_url(request, song_obj.songs.image.url)
                if song_obj.songs.image else None,
                'song_duration': song_obj.songs.duration,
                'song_url': get_absolute_url(request, song_obj.songs.song_file.url)
                if song_obj.songs.song_file else get_absolute_url(request, song_obj.songs.song_url),
                'total_likes': song_obj.songs.total_likes,
                'total_downloads': song_obj.songs.total_downloads,
                'favourite_count': song_obj.songs.favourite_count,
                'playlist_count': song_obj.songs.playlist_count,
                'favourite_status': "False",
                'artists': [],
            })

    # Return the response
    return success_response_200(200, 'Success', data)


# chatgpt
@api_view(['GET'])
def album_details(request):
    # Validate required fields
    required_fields = ["user_id", "album_id", "artist_id", "page", "limit"]
    missing_fields = [field for field in required_fields if not request.GET.get(field)]
    if missing_fields:
        return success_response_200(400, f"{', '.join(missing_fields)} missing fields", 'null')

    # Get parameters from the request
    user_id = request.GET.get("user_id")
    album_id = request.GET.get("album_id")
    limit = int(request.GET.get("limit"))
    page = int(request.GET.get("page"))

    # Fetch all songs for the given album
    songs_data = (
        SongCategory.objects.filter(albums=album_id)
        .select_related('songs', 'artists')
        .distinct()
    )

    # Paginate the data
    paginator = Paginator(songs_data, limit)
    try:
        paginated_songs = paginator.page(page)
    except PageNotAnInteger:
        paginated_songs = paginator.page(1)
    except EmptyPage:
        paginated_songs = []

    # Prepare the response data
    data = []
    processed_song_ids = set()  # To track processed song IDs

    for song_entry in paginated_songs:
        song = song_entry.songs
        if song.id not in processed_song_ids:
            # Fetch associated artists
            artists_data = (
                SongCategory.objects.filter(songs=song.id, albums=album_id)
                .exclude(artists__isnull=True)
                .select_related('artists')
            )
            artists = [
                {
                    'artist_id': artist_entry.artists.id,
                    'artist_name': artist_entry.artists.name,
                    'artist_image': get_absolute_url(request, artist_entry.artists.image.url)
                    if artist_entry.artists.image else None,
                }
                for artist_entry in artists_data
            ]

            # Check if the song is marked as a favorite
            is_favourite = FavouriteSong.objects.filter(fk_user=user_id, fk_song=song.id).exists()

            # Add song details to the response
            data.append({
                'album_id': album_id,
                'song_id': song.id,
                'song_name': song.name,
                'song_image': get_absolute_url(request, song.image.url) if song.image else None,
                'song_duration': song.duration,
                'song_url': get_absolute_url(request, song.song_file.url)
                if song.song_file else get_absolute_url(request, song.song_url),
                'total_likes': song.total_likes,
                'total_downloads': song.total_downloads,
                'favourite_count': song.favourite_count,
                'playlist_count': song.playlist_count,
                'favourite_status': "True" if is_favourite else "False",
                'artists': artists,
            })

            # Mark song as processed
            processed_song_ids.add(song.id)

    # Fetch and add songs without associated artists (if applicable)
    no_artist_songs = (
        SongCategory.objects.filter(albums=album_id, artists__isnull=True)
        .select_related('songs')
    )
    for song_entry in no_artist_songs:
        song = song_entry.songs
        if song.id not in processed_song_ids:
            data.append({
                'album_id': album_id,
                'song_id': song.id,
                'song_name': song.name,
                'song_image': get_absolute_url(request, song.image.url) if song.image else None,
                'song_duration': song.duration,
                'song_url': get_absolute_url(request, song.song_file.url)
                if song.song_file else get_absolute_url(request, song.song_url),
                'total_likes': song.total_likes,
                'total_downloads': song.total_downloads,
                'favourite_count': song.favourite_count,
                'playlist_count': song.playlist_count,
                'favourite_status': "False",
                'artists': [],
            })

    # Return the response
    return paginated_success_response_200(200, 'Success', data,limit,page,paginator.num_pages)


#optimised
# @api_view(['GET'])
# def album_details(request):
#     # Validate required fields
#     required_fields = ["user_id", "album_id", "artist_id", "page", "limit"]
#     missing_fields = [field for field in required_fields if not request.GET.get(field)]
#     if missing_fields:
#         return success_response_200(400, f"{', '.join(missing_fields)} missing fields", 'null')

#     # Get parameters from the request
#     user_id = request.GET.get("user_id")
#     album_id = request.GET.get("album_id")
#     limit = int(request.GET.get("limit"))
#     page = int(request.GET.get("page"))
#     artist_id=int(request.GET.get("artist_id"))

#     try:
#     # Fetch all songs for the given album
#         songs_data = (
#             SongCategory.objects.filter(albums=album_id,artists=artist_id)
#             .select_related('songs', 'artists')
#             .distinct()
#         )
#     except SongCategory.ObjectDoesNotExist:
#         return success_response_200(400,'album doesnot exist','null')

#     # Paginate the data
#     paginator = Paginator(songs_data, limit)
#     try:
#         paginated_songs = paginator.page(page)
#     except PageNotAnInteger:
#         paginated_songs = paginator.page(1)
#     except EmptyPage:
#         paginated_songs = []
    
#     data=[]
#     artists_id=set()
#     artists=[]
#     for Album_obj in paginated_songs:
#         Artist_obj = SongCategory.objects.filter(songs=Album_obj.songs.id).select_related('artists').first()
#         if Artist_obj.artists.id not in artists_id:
#             artists.append(
#                 {
#                     'artist_id':Album_obj.artists.id,
#                     'artists_name':Album_obj.artists.name,
#                     'artist_image':Album_obj.artists.image.url
#                 }
#             )
#         artists_id.add(Artist_obj.artists.id)

#         data.append({
#                 'album_id': Album_obj.albums.id,
#                 'song_id': Album_obj.songs.id,
#                 'song_name': Album_obj.songs.name,
#                 'song_image': get_absolute_url(request, Album_obj.songs.image.url) if Album_obj.songs.image else None,
#                 'song_duration': Album_obj.songs.duration,
#                 'song_url': get_absolute_url(request, Album_obj.songs.song_file.url)if Album_obj.songs.song_file else get_absolute_url(request, Album_obj.songs.song_url),
#                 'total_likes': Album_obj.songs.total_likes,
#                 'total_downloads': Album_obj.songs.total_downloads,
#                 'favourite_count': Album_obj.songs.favourite_count,
#                 'playlist_count': Album_obj.songs.playlist_count,
#                 #'favourite_status': "True" if is_favourite else "False",
#                 'artists': artists,
#             })
    
#     # SONGS_OBJ = SongCategory.objects.filter()
#     # for Songs in 

        
    
#     return success_response_200(200,'album details',data)

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@api_view(['GET'])
def songs_list(request):
    # Step 1: Fetch all unique song IDs with assigned artists in a single query
    assigned_songs = (SongCategory.objects.filter(artists__isnull=False,songs__isnull=False)
                      .select_related('songs', 'artists')
                      .distinct())
    print(assigned_songs)
    data = []
    processed_song_ids = set()  # To track added song IDs

    # Group SongCategory by song IDs and prefetch artists for efficiency
    grouped_song_categories = {}
    for category in assigned_songs:
        song_id = category.songs.id
        if song_id not in grouped_song_categories:
            grouped_song_categories[song_id] = []
        grouped_song_categories[song_id].append(category.artists)
    
    print(grouped_song_categories)

    # Build the response for songs with assigned artists
    for song_id, artists in grouped_song_categories.items():
        song = assigned_songs.filter(songs__id=song_id).first().songs
        processed_song_ids.add(song_id)

        # Generate artist details
        artists_list = [{
            'artist_id': artist.id,
            'artist_name': artist.name,
            'artist_image': get_absolute_url(request, artist.image.url) if artist.image else None,
        } for artist in artists if artist]

        data.append({
            'song_id': song.id,
            'song_name': song.name,
            'song_image': get_absolute_url(request, song.image.url) if song.image else None,
            'song_url': get_absolute_url(request, song.song_file.url) if song.song_file else get_absolute_url(request, song.song_url),
            'song_duration': song.duration,
            'total_likes': song.total_likes,
            'total_downloads': song.total_downloads,
            'favourite_count': song.favourite_count,
            'playlist_count': song.playlist_count,
            'artists': artists_list,
        })

    # Step 2: Fetch all remaining songs in one query
    remaining_songs = Song.objects.exclude(id__in=processed_song_ids)

    # Build the response for songs without assigned artists
    for song in remaining_songs:
        data.append({
            'song_id': song.id,
            'song_name': song.name,
            'song_image': get_absolute_url(request, song.image.url) if song.image else None,
            'song_url': get_absolute_url(request, song.song_file.url) if song.song_file else get_absolute_url(request, song.song_url),
            'song_duration': song.duration,
            'total_likes': song.total_likes,
            'total_downloads': song.total_downloads,
            'favourite_count': song.favourite_count,
            'playlist_count': song.playlist_count,
            'artists': [],  # No artists assigned
        })

    # Step 3: Implement Pagination
    page = int(request.GET.get('page', 1))  # Get the page number from query params
    limit = int(request.GET.get('limit', 10))  # Items per page (default 10)

    paginator = Paginator(data, limit)  # Paginate the `data` list

    try:
        paginated_data = paginator.page(page)  # Get the requested page
    except PageNotAnInteger:
        paginated_data = paginator.page(1)  # Return the first page if `page` is not an integer
    except EmptyPage:
        paginated_data = []  # Return an empty list if the page is out of range

    # Return the paginated response
    return paginated_success_response_200(200,'available songs',data,limit,page,paginator.num_pages)
 

@api_view(['GET'])
def album_songs(request):
    token = extract_token(request)
    if not token:
        return success_response_200(200, 'token not found', 'null')

    LoggedInUserObj = CustomUser.objects.filter(remember_token=token).first()
    if not LoggedInUserObj:
        return success_response_200(200, 'user not found', 'null')

    album_id = request.GET.get("album_id")
    artist_id = request.GET.get("artist_id")
    page = int(request.GET.get("page", 1))
    limit = int(request.GET.get("limit", 10))  # Default limit is 10

    if not album_id:
        return success_response_200(200, 'album id is required', 'null')

    album = Album.objects.filter(id=album_id).first()
    if not album:
        return success_response_200(200, 'album does not exist', 'null')

    # Fetch all songs in the album, filtering by artist if provided
    album_songs_query = SongCategory.objects.filter(albums=album_id, songs__isnull=False)

    if artist_id:
        album_songs_query = album_songs_query.filter(artists=artist_id)

    album_songs_query = album_songs_query.select_related('songs').distinct()

    # Apply pagination
    paginator = Paginator(album_songs_query, limit)

    try:
        paginated_songs = paginator.page(page)
    except PageNotAnInteger:
        paginated_songs = paginator.page(1)
    except EmptyPage:
        paginated_songs = []

    data = []

    # Fetch all favorite songs in one query
    fav_song_ids = set(
        FavouriteSong.objects.filter(fk_user=LoggedInUserObj.id, fk_song__in=[s.songs.id for s in paginated_songs])
        .values_list('fk_song', flat=True)
    )

    for album_song in paginated_songs:
        song = album_song.songs
        favourite_status = song.id in fav_song_ids

        # Fetch all artists for the song excluding the given artist_id
        artist_objs = (
            SongCategory.objects.filter(songs=song.id)
            .select_related('artists')
            .distinct()
        )

        artists = [{
            'artist_id': artist_obj.artists.id,
            'artist_name': artist_obj.artists.name,
            'artist_image': get_absolute_url(request, artist_obj.artists.image.url)
            if artist_obj.artists.image else None,
        } for artist_obj in artist_objs if artist_obj.artists]

        data.append({
            'song_id': song.id,
            'song_name': song.name,
            'song_image': get_absolute_url(request, song.image.url) if song.image else None,
            'song_url': get_absolute_url(request, song.song_file.url) if song.song_file else song.song_url,
            'song_duration': song.duration,
            'total_likes': song.total_likes,
            'total_downloads': song.total_downloads,
            'playlist_count': song.playlist_count,
            'favourite_count': song.favourite_count,
            'favourite_status': favourite_status,
            'artists': artists,
        })

    # Return paginated response
    return JsonResponse({
        'code': 200,
        'message': 'album songs',
        'album_id': album.id,
        'album_name': album.name,
        'album_image': get_absolute_url(request, album.image.url) if album.image else None,
        'songs': data,
        'current_page': page,
        'limit': limit,
        'last_page': paginator.num_pages,
        'first_page': 1,
    })

@api_view(['GET'])
def genres(request):
    page=request.GET.get("page",1)
    limit=request.GET.get("limit",10)
    data=[]
    token=extract_token(request)
    if not token:
        return success_response_200(200,'token not found','null')
    Genres=Genre.objects.all()
    if not Genres:
        return success_response_200(200,'genres not found','null')
    paginator = Paginator(Genres,limit)
    try:
        paginated_data=paginator.page(page)
    except PageNotAnInteger:
        paginated_data=paginator.page(1)
    except EmptyPage:
        paginated_data=[]
    for genre in paginated_data:
        data.append({
            'genre_id':genre.id,
            'genre_name':genre.name,
            'genre_image':get_absolute_url(request,genre.image.url) if genre.image else None,
            'created_at':genre.created_at,
        })
    return JsonResponse({
        'code':200,
        'message':'available genres',
        'genres':data,
        'current_page':page,
        'total_pages':paginator.num_pages,
        'limit':limit,
    })

@api_view(['GET'])
def genres_save(request):

    return success_response_200(200,'success','null')

@api_view(['GET'])
def subcategoryandtracks(request):
    page=int(request.GET.get("page",1))
    RecordType=request.GET.get("recordtype")
    limit=int(request.GET.get("limit",10))
    artist_id=request.GET.get("artist_id")
    genre_id = request.GET.get("genre_id")
    album_id=request.GET.get("album_id")
    mixes_id=request.GET.get("mixes_id")
    filter=request.GET.get("filter")
    token = extract_token(request)
    if not token:
        return success_response_200(200,'token missing','null')
    LoggedInUserObj = CustomUser.objects.filter(remember_token=token).first()
    if not LoggedInUserObj:
        return success_response_200(200,'user not found','null')
    data=[]
    match filter:
        case 'Mixes':
            match RecordType:
                case 'Tracks':
                    Mix = Mixes.objects.filter(id=mixes_id).first()
                    if not Mix:
                        return success_response_200(200,'mixes doesnt exists','null')
                    RelationObj = (
                        SongCategory.objects.filter(fk_mixes=mixes_id,songs__isnull=False)
                        .select_related('fk_mixes','songs')
                        .distinct()
                    )
                    for MixesObj in RelationObj:
                        favourite_satus = FavouriteSong.objects.filter(fk_user=LoggedInUserObj.id,fk_song=MixesObj.songs.id).exists()
                        artists=[]
                        ArtistsObj = (
                            SongCategory.objects.filter(songs=MixesObj.songs.id,artists__isnull=False)
                            .select_related('artists')
                            .distinct()
                        )
                        for artist in ArtistsObj:
                            artists.append({
                                'artist_id':artist.artists.id,
                                'artist_name':artist.artists.name,
                                'artist_image':get_absolute_url(request,artist.artists.image.url) if artist.artists.image else None,
                            })
                        data.append({
                            'song_id':MixesObj.songs.id,
                            'song_name':MixesObj.songs.name,
                            'song_image':get_absolute_url(request,MixesObj.songs.image.url) if MixesObj.songs.image else None,
                            'song_duration':MixesObj.songs.duration,
                            'total_likes':MixesObj.songs.total_likes,
                            'total_downloads':MixesObj.songs.total_downloads,
                            'playlist_count':MixesObj.songs.playlist_count,
                            'favourite_count':MixesObj.songs.favourite_count,
                            'favourite_status':favourite_satus,
                            'artists':artists,
                        })
                    paginator= Paginator(data,limit)
                    
                    try:
                        paginated_data=paginator.page(page)
                    except PageNotAnInteger:
                        paginated_data=paginator.page(1)
                    except EmptyPage:
                        paginated_data=[]

                    return JsonResponse({
                        'code':200,
                        'message':'available Songs',
                        'mixes_id': Mix.id,
                        'mixes_name':Mix.name,
                        'mixes_image':get_absolute_url(request,Mix.image.url) if Mix.image else None,
                        'songs':list(paginated_data),
                        'page':page,
                        'limit':limit,
                        'total_pages':paginator.num_pages,
                    },status=status.HTTP_200_OK)
                case _:
                    return success_response_200(200,'incorrect recordtype','null')
        case 'Artist':
            match RecordType:
                case 'Tracks':
                    RequestedArtistObj = Artist.objects.get(id=artist_id)
                    if not RequestedArtistObj:
                        return success_response_200(200,'artist does not exists','null')
                    RelationObj = (
                        SongCategory.objects.filter(artists=artist_id,songs__isnull=False)
                        .select_related('artists','songs')
                        .distinct()
                    )
                    for SongObj in RelationObj:
                        favourite_satus = FavouriteSong.objects.filter(fk_user=LoggedInUserObj.id,fk_song=SongObj.songs.id).exists()
                        artists=[]
                        ArtistsObj = (
                            SongCategory.objects.filter(songs=SongObj.songs.id,artists__isnull=False)
                            .select_related('artists')
                            .distinct()
                        )   
                        for artist in ArtistsObj:
                            artists.append({
                                'artist_id':artist.artists.id,
                                'artist_name':artist.artists.name,
                                'artist_image':get_absolute_url(request,artist.artists.image.url) if artist.artists.image else None,
                            })
                        data.append({
                            'song_id':SongObj.songs.id,
                            'song_name':SongObj.songs.name,
                            'song_image':get_absolute_url(request,SongObj.songs.image.url) if SongObj.songs.image else None,
                            'song_duration':SongObj.songs.duration,
                            'total_likes':SongObj.songs.total_likes,
                            'total_downloads':SongObj.songs.total_downloads,
                            'playlist_count':SongObj.songs.playlist_count,
                            'favourite_count':SongObj.songs.favourite_count,
                            'favourite_status':favourite_satus,
                            'artists':artists,
                        })
                    paginator= Paginator(data,limit)
                    
                    try:
                        paginated_data=paginator.page(page)
                    except PageNotAnInteger:
                        paginated_data=paginator.page(1)
                    except EmptyPage:
                        paginated_data=[]

                    return JsonResponse({
                        'code':200,
                        'message':'available Songs',
                        'artist_id': RequestedArtistObj.id,
                        'artist_name':RequestedArtistObj.name,
                        'artist_image':get_absolute_url(request,RequestedArtistObj.image.url) if RequestedArtistObj.image else None,
                        'songs':list(paginated_data),
                        'page':page,
                        'limit':limit,
                        'total_pages':paginator.num_pages,
                    },status=status.HTTP_200_OK)
                
                case 'Albums':
                    RequestedArtistObj = Artist.objects.filter(id=artist_id).first()
                    if not RequestedArtistObj:
                        return success_response_200(200,'artist does not exists','null')
                    ArtistAlbums=(
                        SongCategory.objects.filter(artists=artist_id,songs__isnull=False,albums__isnull=False)
                        .select_related('artists','albums')
                        .distinct()
                    )
                    album_ids=set()
                    for ArtistAlbum in ArtistAlbums:
                        if ArtistAlbum.albums.id not in album_ids:
                            data.append({
                                'album_id':ArtistAlbum.albums.id,
                                'album_name':ArtistAlbum.albums.name,
                                'album_image':get_absolute_url(request,ArtistAlbum.albums.image.url) if ArtistAlbum.albums.image else None,
                            })
                            album_ids.add(ArtistAlbum.albums.id)
                    paginator= Paginator(data,limit)
                    try:
                        paginated_data = paginator.page(page)
                    except PageNotAnInteger:
                        paginated_data = paginator.page(1)
                    except EmptyPage:
                        paginated_data = []
                    return JsonResponse({
                        'code':200,
                        'message':'Available Albums',
                        'artist_id':RequestedArtistObj.id,
                        'artist_name':RequestedArtistObj.name,
                        'artist_image':get_absolute_url(request,RequestedArtistObj.image.url) if RequestedArtistObj.image else None,
                        'albums':list(paginated_data),
                        'page':page,
                        'limit':limit,
                        'total_pages':paginator.num_pages,
                    })
                case 'AlbumsTracks':
                    RequestedArtistObj = Artist.objects.get(id=artist_id)
                    if not RequestedArtistObj:
                        return success_response_200(200,'artist does not exists','null')
                    RequestedAlbumObj = Album.objects.filter(id=album_id).first()
                    if not RequestedAlbumObj:
                        return success_response_200(200,'album not found','null')
                    AssignedSongs = (
                        SongCategory.objects.filter(albums=album_id,artists=RequestedArtistObj.id,songs__isnull=False)
                        .select_related('songs','albums')
                        .distinct()
                    )
                    for AssignedSong in AssignedSongs:
                        favourite_satus = FavouriteSong.objects.filter(fk_user=LoggedInUserObj.id,fk_song=AssignedSong.songs.id).exists()
                        SongArtists=(
                            SongCategory.objects.filter(songs=AssignedSong.songs.id,artists__isnull=False)
                            .select_related('artists')
                            .distinct()
                        )
                        artists=[]
                        for SongArtist in SongArtists:
                            artists.append({
                                'artist_id':SongArtist.artists.id,
                                'artist_name':SongArtist.artists.name,
                                'artist_image':get_absolute_url(request,SongArtist.artists.image.url) if SongArtist.artists.image else None,
                            })
                        data.append({
                            'song_id':AssignedSong.songs.id,
                            'song_name':AssignedSong.songs.name,
                            'song_image':get_absolute_url(request,AssignedSong.songs.image.url) if AssignedSong.songs.image else None,
                            'song_duration':AssignedSong.songs.duration,
                            'total_likes':AssignedSong.songs.total_likes,
                            'total_downloads':AssignedSong.songs.total_downloads,
                            'playlist_count':AssignedSong.songs.playlist_count,
                            'favourite_count':AssignedSong.songs.favourite_count,
                            'favourite_status':favourite_satus,
                            'artists':artists,
                        })
                    paginator = Paginator(data,limit)
                    try:
                        paginated_data = paginator.page(page)
                    except PageNotAnInteger:
                        paginated_data = paginator.page(1)
                    except EmptyPage:
                        paginated_data = []
                    
                    return JsonResponse({
                        'code':200,
                        'message':'available album songs',
                        'album_id': RequestedAlbumObj.id,
                        'album_name':RequestedAlbumObj.name,
                        'album_image':get_absolute_url(request,RequestedAlbumObj.image.url) if RequestedAlbumObj.image else None,
                        'songs':list(paginated_data),
                        'page':page,
                        'limit':limit,
                        'total_pages':paginator.num_pages,
                        },status=status.HTTP_200_OK)
                case _:
                    return success_response_200(200,'incorrect recordtype','null')

        case 'Genres':
            match RecordType:
                case 'Tracks':
                    RequestedGenreObj = Genre.objects.filter(id=genre_id).first()
                    if not RequestedGenreObj:
                        return success_response_200(200,'genre not found','null')
                    RelationObj = (
                        SongCategory.objects.filter(fk_genre=genre_id,songs__isnull=False)
                        .select_related('fk_genre','songs')
                        .distinct()
                    )        
                    for GenreSong in RelationObj:
                        favourite_satus = FavouriteSong.objects.filter(fk_user=LoggedInUserObj.id,fk_song=GenreSong.songs.id).exists()
                        artists=[]
                        ArtistsObj =(
                            SongCategory.objects.filter(songs=GenreSong.songs.id,artists__isnull=False)
                            .select_related('artists')
                            .distinct()
                        )
                        for ArtistObj in ArtistsObj:
                            artists.append({
                                'artist_id':ArtistObj.artists.id,
                                'artist_name':ArtistObj.artists.name,
                                'artist_image':get_absolute_url(request,ArtistObj.artists.image.url) if ArtistObj.artists.image else None,
                            })
                        data.append({
                            'song_id':GenreSong.songs.id,
                            'song_name':GenreSong.songs.name,
                            'song_image':get_absolute_url(request,GenreSong.songs.image.url) if GenreSong.songs.image else None,
                            'song_duration':GenreSong.songs.duration,
                            'total_likes':GenreSong.songs.total_likes,
                            'total_downloads':GenreSong.songs.total_downloads,
                            'playlist_count':GenreSong.songs.playlist_count,
                            'favourite_count':GenreSong.songs.favourite_count,
                            'favourite_status':favourite_satus,
                            'artists':artists,
                        })

                    paginator = Paginator(data,limit)
                    try:
                        paginated_data=paginator.page(page)
                    except PageNotAnInteger:
                        paginated_data = paginator.page(1)
                    except EmptyPage:
                        paginated_data = []

                    return JsonResponse({
                        'code':200,
                        'message':'avaiable Genre Songs',
                        'genre_id': RequestedGenreObj.id,
                        'genre_name':RequestedGenreObj.name,
                        'genre_image':get_absolute_url(request,RequestedGenreObj.image.url) if RequestedGenreObj.image else None,
                        'songs':list(paginated_data),
                        'page':page,
                        'limit':limit,
                        'total_pages':paginator.num_pages,
                    },status=status.HTTP_200_OK)
                
                case 'GenreAlbums':
                    RequestedGenreObj = SongCategory.objects.filter(fk_genre=genre_id).select_related('fk_genre').first()
                    if not RequestedGenreObj:
                        return success_response_200(200,'genre not found','null')
                    RelationObj = (
                        SongCategory.objects.filter(fk_genre=genre_id,albums__isnull=False)
                        .select_related('albums','fk_genre')
                        .distinct()
                    )
                    for Genrealbum in RelationObj:
                        AssignedSong = (
                            SongCategory.objects.filter(albums=Genrealbum.albums.id,songs__isnull=False).exists()
                        )
                        if AssignedSong:
                            albums_ids=set()
                            if Genrealbum.albums.id not in albums_ids: 
                                data.append({
                                    'album_id':Genrealbum.albums.id,
                                    'album_name':Genrealbum.albums.name,
                                    'album_image':get_absolute_url(request,Genrealbum.albums.image.url) if Genrealbum.albums.image else None,
                                })
                                albums_ids.add(Genrealbum.albums.id)

                    paginator=Paginator(data,limit)
                    try:
                        paginated_data=paginator.page(page)
                    except PageNotAnInteger:
                        paginated_data = paginator.page(1)
                    except EmptyPage:
                        paginated_data = []              

                    return JsonResponse({
                        'code':200,
                        'message':'genre albums',
                        'genre_id':RequestedGenreObj.fk_genre.id,
                        'genre_name':RequestedGenreObj.fk_genre.name,
                        'genre_image':get_absolute_url(request,RequestedGenreObj.fk_genre.image.url) if RequestedGenreObj.fk_genre.image else None,
                        'albums':list(paginated_data),
                        'page':page,
                        'limit':limit,
                        'total_pages':paginator.num_pages,
                    },status=status.HTTP_200_OK)    
                
                case 'AlbumsTracks':
                    RequestedArtistObj = Artist.objects.get(id=artist_id)
                    if not RequestedArtistObj:
                        return success_response_200(200,'artist does not exists','null')
                    RequestedAlbumObj = Album.objects.filter(id=album_id).first()
                    if not RequestedAlbumObj:
                        return success_response_200(200,'album not found','null')
                    AssignedSongs = (
                        SongCategory.objects.filter(albums=album_id,artists=RequestedArtistObj.id,songs__isnull=False)
                        .select_related('songs','albums')
                        .distinct()
                    )
                    for AssignedSong in AssignedSongs:
                        favourite_satus = FavouriteSong.objects.filter(fk_user=LoggedInUserObj.id,fk_song=AssignedSong.songs.id).exists()
                        SongArtists=(
                            SongCategory.objects.filter(songs=AssignedSong.songs.id,artists__isnull=False)
                            .select_related('artists')
                            .distinct()
                        )
                        artists=[]
                        for SongArtist in SongArtists:
                            artists.append({
                                'artist_id':SongArtist.artists.id,
                                'artist_name':SongArtist.artists.name,
                                'artist_image':get_absolute_url(request,SongArtist.artists.image.url) if SongArtist.artists.image else None,
                            })
                        data.append({
                            'song_id':AssignedSong.songs.id,
                            'song_name':AssignedSong.songs.name,
                            'song_image':get_absolute_url(request,AssignedSong.songs.image.url) if AssignedSong.songs.image else None,
                            'song_duration':AssignedSong.songs.duration,
                            'total_likes':AssignedSong.songs.total_likes,
                            'total_downloads':AssignedSong.songs.total_downloads,
                            'playlist_count':AssignedSong.songs.playlist_count,
                            'favourite_count':AssignedSong.songs.favourite_count,
                            'total_played':AssignedSong.songs.total_played,
                            'favourite_status':favourite_satus,
                            'artists':artists,
                        })
                    paginator = Paginator(data,limit)
                    try:
                        paginated_data = paginator.page(page)
                    except PageNotAnInteger:
                        paginated_data = paginator.page(1)
                    except EmptyPage:
                        paginated_data = []
                    
                    return JsonResponse({
                        'code':200,
                        'message':'available album songs',
                        'album_id': RequestedAlbumObj.id,
                        'album_name':RequestedAlbumObj.name,
                        'album_image':get_absolute_url(request,RequestedAlbumObj.image.url) if RequestedAlbumObj.image else None,
                        'songs':list(paginated_data),
                        'page':page,
                        'limit':limit,
                        'total_pages':paginator.num_pages,
                        },status=status.HTTP_200_OK)
                case _:
                    return success_response_200(200,'invalid record type','null')
        case _:
            return success_response_200(200,'invalid filter','null')
                
# @api_view(['GET'])
# def mostplayed(request):
#     page=request.GET.get("page",1)
#     limit=request.GET.get("limit",10)
#     token = extract_token(request)
#     if not token:
#         return success_response_200(200,'token is missing','null')  
#     user_obj = CustomUser.objects.filter(remember_token=token).first()
#     if not user_obj:
#         return success_response_200(200,'user not found','null')
#     mostplayed_obj = Song.objects.order_by('-total_played')[:20]
#     data=[]
#     for song in mostplayed_obj:
#         favourite_status=FavouriteSong.objects.filter(fk_user=user_obj.id,fk_song=song.id).exists()
#         artists=[]
#         ArtistsObj = (
#             SongCategory.objects.filter(songs=song.id,artists__isnull=False)
#             .select_related('artists')
#             .distinct()
#         )
#         for ArtistObj in ArtistsObj:
#             if ArtistObj:
#                 artists.append({
#                     'artist_id':ArtistObj.artists.id,
#                     'artist_name':ArtistObj.artists.name,
#                     'artist_image':get_absolute_url(request,ArtistObj.artists.image.url) if ArtistObj.artists.image else None,
#                 })
#         data.append({
#             'song_id':song.id,
#             'song_name':song.name,
#             'song_image':get_absolute_url(request,song.image.url) if song.image else None,
#             'duration': song.duration,
#             'song_url': get_absolute_url(request,song.song_file.url) if song.song_file else get_absolute_url(request,song.song_url),
#             'total_likes':song.total_likes,
#             'total_downloads':song.total_downloads,
#             'total_played':song.total_played,
#             'playlist_count':song.playlist_count,
#             'favourite_status':favourite_status,
#             'artists':artists,
#         })
#     paginator = Paginator(data,limit)
#     try:
#         paginated_data=paginator.page(page)
#     except PageNotAnInteger:
#         paginated_data=paginator.page(1)
#     except EmptyPage:
#         paginated_data=[]
    
#     return JsonResponse({
#         'code':200,
#         'message':'Most Played Songs',
#         'songs':list(paginated_data),
#         'page':int(page),
#         'limit':int(limit),
#         'total_pages':paginator.num_pages,
#     },status=status.HTTP_200_OK)
class MostPlayedSongsView(APIView):
    """Returns the most played songs with pagination and user validation."""

    def get(self, request):
        # Extract pagination parameters
        page = request.GET.get("page", 1)
        limit = request.GET.get("limit", 10)

        # Validate user token
        token = extract_token(request)
        if not token:
            return Response({'code': 200, 'message': 'Token is missing', 'songs': None}, status=status.HTTP_200_OK)

        user_obj = CustomUser.objects.filter(remember_token=token).first()
        if not user_obj:
            return Response({'code': 200, 'message': 'User not found', 'songs': None}, status=status.HTTP_200_OK)

        # Fetch most played songs
        mostplayed_obj = Song.objects.order_by('-total_played')[:20]

        # Prepare response data
        data = []
        for song in mostplayed_obj:
            favourite_status = FavouriteSong.objects.filter(fk_user=user_obj.id, fk_song=song.id).exists()
            artists = [
                {
                    'artist_id': artist.artists.id,
                    'artist_name': artist.artists.name,
                    'artist_image': get_absolute_url(request, artist.artists.image.url) if artist.artists.image else None,
                }
                for artist in SongCategory.objects.filter(songs=song.id, artists__isnull=False).select_related('artists').distinct()
            ]

            data.append({
                'song_id': song.id,
                'song_name': song.name,
                'song_image': get_absolute_url(request, song.image.url) if song.image else None,
                'duration': song.duration,
                'song_url': get_absolute_url(request, song.song_file.url) if song.song_file else get_absolute_url(request, song.song_url),
                'total_likes': song.total_likes,
                'total_downloads': song.total_downloads,
                'total_played': song.total_played,
                'playlist_count': song.playlist_count,
                'favourite_status': favourite_status,
                'artists': artists,
            })

        # Paginate results
        paginator = Paginator(data, limit)
        try:
            paginated_data = paginator.page(page)
        except PageNotAnInteger:
            paginated_data = paginator.page(1)
        except EmptyPage:
            paginated_data = []

        return JsonResponse({
            'code': 200,
            'message': 'Most Played Songs',
            'songs': list(paginated_data),
            'page': int(page),
            'limit': int(limit),
            'total_pages': paginator.num_pages,
        }, status=status.HTTP_200_OK)
