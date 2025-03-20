# main_app/utils.py

import requests
from io import BytesIO
from mutagen.mp3 import MP3
from django.core.cache import cache
from background_task import background
# yourapp/utils.py
from django.core.mail import send_mail
from django.utils.html import strip_tags

def send_email(subject, message, recipient_list):
    try:
        send_mail(
            subject,
            message,
            'harsh.stegowl@gmail.com',  # Sender's email
            recipient_list,
            fail_silently=False,
        )
    except Exception as e:
        print(e)

@background()
def send_html_email(to_email, subject, html_message):
    # Create a plain text version of the HTML content (optional)
    plain_text_message = strip_tags(html_message)

    # Send the HTML email
    send_mail(subject, plain_text_message, 'harsh.stegowl@gmail.com', [to_email], html_message=html_message)
    print("Email sent to user")



def get_song_duration_from_url(song_url):
    """
    Helper function to calculate the duration of a song from a URL.
    This function checks if the song's duration is cached first. If not, it downloads
    the full file and calculates the duration using the Mutagen library.
    """
    from requests.exceptions import RequestException
    from mutagen.mp3 import MP3
    from io import BytesIO

    # Check if the duration is cached
    cached_duration = cache.get(song_url)
    if cached_duration:
        print(f"Duration cached for {song_url}: {cached_duration}")
        return cached_duration

    try:
        print(f"Attempting to download the full song from URL: {song_url}")
        response = requests.get(song_url, timeout=60)  # Timeout for larger files
        response.raise_for_status()  # Raise an error for bad status codes

        # Validate the Content-Type header
        content_type = response.headers.get('Content-Type', '')
        if 'audio/mpeg' not in content_type:
            raise ValueError(f"Invalid content type for URL: {content_type}")

        # Load the audio from the response content
        audio = MP3(BytesIO(response.content))
        duration_in_seconds = audio.info.length  # Get the duration in seconds

        if duration_in_seconds:
            formatted_duration = format_duration(duration_in_seconds)

            # Cache the duration for future use (timeout 3600 seconds = 1 hour)
            cache.set(song_url, formatted_duration, timeout=3600)

            print(f"Calculated duration for {song_url}: {formatted_duration}")
            return formatted_duration
        else:
            print(f"Error: No duration found for {song_url}.")
            return None

    except RequestException as re:
        print(f"HTTP request error for URL {song_url}: {re}")
        return None
    except Exception as e:
        print(f"Error calculating duration for song from URL {song_url}: {e}")
        return None

def format_duration(duration_in_seconds):
    """Helper function to format the duration to HH:MM:SS format."""
    hours, remainder = divmod(duration_in_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
