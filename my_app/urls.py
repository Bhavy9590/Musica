from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from my_app.apis.api_views import *
from .apis import api_views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    #path('register/', views.register, name='register'),
    path('index/', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # path('songs/',views.songs,name='songs'),
    path('song/',views.songs,name="songs"),
    path('song/lazy-scroll-songs/', views.lazy_scroll_songs, name='lazy_scroll_songs'),
    path('edit-song/<int:id>/', views.edit_song, name='edit_song'),
    path('delete-song/<int:id>/',views.delete_song,name='delete_song'),

    # path('live-radio/',views.live_radio,name='live_radio'),
    # path('live-video/',views.live_video,name='live_video'),
    path('artists/',views.artists,name='artists'),
    path('add-artist/',views.add_artist,name='add_artist'),
    path('edit-artist/<int:id>/',views.edit_artist,name='edit_artist'),
    path('delete-artist/<int:id>/',views.delete_artist,name='delete_artist'),


    path('albums/',views.albums,name='albums'),
    path('albums/<int:id>/details/',views.album_details,name="album_details"),
    path('albums/<int:id>/details/lazy-scroll-album-details/',views.album_details_lazy_scroll,name="lazy_scroll_album_details"),
    path("albums/<int:id>/tracks/add", views.album_add_song, name="album_song_add"),
    path('add-album/',views.add_album,name='add_album'),
    path('edit-album/<int:id>/',views.edit_album,name='edit_album'),
    path('delete-album/<int:id>/',views.delete_album,name='delete_album'),
    
    
    path('videos/',views.videos,name='videos_frontend'),
    path('videos/add/',views.videos_add,name='Videos_Add'),
    path('videos/delete/<int:id>/',views.videos_delete,name='Videos_delete'),

    path('video_cat/',views.videos_cat,name='videos_cat'),
    path('video_cat/add/',views.videos_cat_add,name='videos_cat_add'),
    path('video_cat/delete/<int:id>/',views.videos_cat_delete,name='videos_cat_delete'),

    path('genres/',views.genres,name='genres'),
    path('add-genre/',views.add_genre,name='add_genre'),
    path('edit-genre/<int:id>/',views.edit_genre,name='edit_genre'),
    path('delete-genre/<int:id>/',views.delete_genre,name='delete_genre'),
    path('add-song/',views.add_song,name='add_song'),   
    path('view-song/<int:song_id>/', views.view_song, name='view_song'),
    path('delete-music/<int:id>/',views.delete_music,name='delete_music'),
    path('users/',views.users,name='users'),
    path('delete_user/<int:id>',views.delete_user,name='delete_user'),
    path('live-radio/',views.live_radio,name='live-radio'),
    path('live-video/',views.live_video,name='live-video'),
    
    path('mixes/',views.mixes,name='Mixes'),
    path('mixes/add',views.add_mixes,name='add_mix'),
    path('mixes/edit/<int:id>',views.edit_mix,name='edit_mix'),
    path('mixes/delete/<int:id>',views.delete_mix,name='delete_mix'),

    path('playlists/',views.playlists,name='playlists'),
    
    path('terms_of_service',views.terms_of_service,name='terms_of_service'),
    path('privacy_policy',views.privacy_policy,name="privacy_policy"),
    #social media module
    path('social-media/',views.social_media,name="social-media"),
    path('add-social-media',views.add_social_media,name="add-social-media"),
    path('edit-social-media/<int:id>/', views.edit_social_media, name="edit-social-media"),
    path('delete-social-media/<int:id>/', views.delete_social_media, name="delete-social-media"),
    #path('song/<int:song_id>/update_trending/',views.update_trending,name="trending"),
    #share app module
    path('share-my-app', views.share_my_app, name='share_my_app'),
    path('add-share-my-app', views.add_share_my_app, name='add_share_my_app'),
    path('edit-share-my-app/<int:id>/', views.edit_share_my_app, name='edit_share_my_app'),
    path('delete-share-my-app/<int:id>/', views.delete_share_app, name='delete_share_app'),
    
    #Tranding 
    path('trending_artists/',views.trending_artists,name='trending_artists'),
    path('update_positions_artists/', views.update_positions_artists, name='update_positions_artists'),

    # path('trending_artists/<int:id>/lazy-scroll-genres/', views.lazy_scroll_genres, name='lazy_scroll_genres'),
    # path('update_positions_artists/', views.update_positions_genres, name='update_positions_artists'),
    
    path('trending_albums/',views.trending_albums,name='trending_albums'),
    path('update_positions_albums/', views.update_positions_albums, name='update_positions_albums'),
    # path('add_trending_artists/',views.add_trending_artists,name='add_trending_artists'),

    path('recommended/',views.recommended,name='recommended'),
    path('trending_geners/',views.trending_geners,name='trending_geners'),
    path('update_positions_geners/', views.update_positions_geners, name='update_positions_geners'),

    path('trending_mixes/',views.trending_mixes,name='trending_mixes'),
    path('update_positions_mixes/', views.update_positions_mixes, name='update_positions_mixes'),
    
    path('trending_tracks/',views.trending_tracks,name='trending_tracks'),
    path('update_positions_tracks/', views.update_positions_tracks, name='update_positions_tracks'),
    
    path('api/socialmedia',api_views.Socialmedia),
    path('api/videos',api_views.videos),
    path('api/sharemyapp',api_views.sharemyapp),
    path('api/logout',api_views.logout),
    path('api/login', api_views.user_login),
    path('api/register', api_views.user_register),
    path('api/uploads',api_views.uploads),
    path('api/profile',api_views.profile),
    path('api/update_profile',api_views.update_profile),
    path('api/countryandtimezone/', api_views.countryandtimezone),
    path('api/forgot_password', api_views.forgot_password),
    path('api/changepassword',api_views.changepassword),
    
    #playlist apis
    path('api/playlists',api_views.playlist),
    path('api/playlists/add',api_views.add_playlist),
    path('api/playlists/remove',api_views.remove_playlist),
    
    #playlist songs api
    path('api/playlistsongs',api_views.playlistsongs),
    path('api/playlistsongs/add',api_views.playlistsongadd),
    path('api/playlistsongs/remove',api_views.playlistsongremove),
    path('api/playlist/removeall',api_views.playlistsongremoveall),

    #playlist albums api
    path('api/playlistalbums',api_views.playlistalbums),
    path('api/playlistalbum/add',api_views.playlistalbums_add),
    path('api/playlistalbum/remove',api_views.playlistalbums_remove),
    path('api/playlistalbums/removeall',api_views.playlistalbums_removeall),
    
    
    
    path('api/albums', api_views.albums_list),
    path('api/albums/details',api_views.album_details),
    path('api/albums/songs',api_views.album_songs),
    
    #songs details,downloads,like,unline api
    path('api/songs', api_views.songs_list),
    path('api/songs/details',api_views.songdetail),
    path('api/songs/like_unlike',api_views.like_unlike),
    path('api/download',api_views.songdownload),
    path('api/download/remove',api_views.removefromdownloads),
    path('api/songs/recommended',api_views.recommended),

    path('api/artists', api_views.artists_list),
    path('api/artist_songs',api_views.artists_song),
    path('api/common_albums',api_views.common_albums),
    path('api/songsandalbums',api_views.songsandalbums),
    
    #recent add and get api
    path('api/recent',api_views.recent),
    path('api/recent/add',api_views.addrecent),
    
    #favourite songs api
    path('api/favourites/',api_views.favourite),
    path('api/favourites/add',api_views.addfavourite),
    path('api/favourites/remove',api_views.removefavourite),

    #live radio api
    path('api/liveradio',api_views.live_radio),

    #live video api
    path('api/videos',api_views.videos),

    #Trending API
    # path('api/trending',api_views.trending,name='trending'),
    path('api/trending-artists',api_views.Trending),

    path('api/introslider',api_views.introslider),
    # path('api/introslider/add',api_views.introslideradd),
    #path('api/songs/addrecommended',api_views.addrecommended),
    path('api/termsandpolicies',api_views.termsandpolicies),


    path('api/genres/get',api_views.genres),
    path('api/genres/save',api_views.genres_save),


    

    path('api/music/subcategoryandtracks',api_views.subcategoryandtracks),

    # path('api/songs/mostplayed',api_views.mostplayed),
    path('api/songs/mostplayed',MostPlayedSongsView.as_view(),name="mostplayed"),
    # path('api/test',api_views.test),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_URL)