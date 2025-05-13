from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.utils import timezone
from itertools import chain
from datetime import datetime, date, time
from django.http import JsonResponse
from .models import *
import re
from django.db.models import Q
import requests
from django.db.models import Sum, Count
from django.http import HttpResponseRedirect
import qrcode
from io import BytesIO
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.sites.shortcuts import get_current_site
import json
import cv2
import numpy as np
from PIL import Image
from datetime import timedelta
from django.db.models.functions import TruncDate
import csv
from django.http import HttpResponse
from django.utils.text import slugify
from django.urls import reverse
from django.utils.timezone import now
# Create your views here.
CATEGORY_METADATA = {
    'Concerts': {
        'icon': 'fas fa-music',
        'description': 'Live music performances',
        'slug': 'concerts'
    },
    'Technology': {
        'icon': 'fas fa-laptop-code',
        'description': 'Conferences & workshops',
        'slug': 'technology'
    },
    'Food': {
        'icon': 'fas fa-utensils',
        'description': 'Festivals & tastings',
        'slug': 'food-drink'
    },
    'Sports': {
        'icon': 'fas fa-running',
        'description': 'Games & tournaments',
        'slug': 'sports'
    },
    'Education': {
        'icon': 'fas fa-graduation-cap',
        'description': 'Seminars & classes',
        'slug': 'education'
    },
    'Arts': {
        'icon': 'fas fa-theater-masks',
        'description': 'Exhibitions & shows',
        'slug': 'arts'
    },
    'Entertainment': {
        'icon': 'fas fa-film',
        'description': 'Movies, theater, culture',
        'slug': 'entertainment'
    }
}

def home(request):
    categories = []

    for key, label in Event.CATEGORY_CHOICES:
        metadata = CATEGORY_METADATA.get(key, {})
        categories.append({
            'name': key,
            'label': label,
            'icon': metadata.get('icon', ''),
            'description': metadata.get('description', ''),
            'slug': metadata.get('slug', '')
        })

    # Sample logic: Upcoming, not free events for Featured
    featured_events = Event.objects.filter(is_free=False, date__gte=now().date()).order_by('date')[:3]

    # Sample logic: Upcoming, free events
    free_events = Event.objects.filter(is_free=True, date__gte=now().date()).order_by('date')[:3]

    return render(request, 'home.html', {
        'categories': categories,
        'featured_events': featured_events,
        'free_events': free_events,
    })

def category_events(request, slug):
    # Find the category name based on the slug
    category_name = next((k for k, v in CATEGORY_METADATA.items() if v['slug'] == slug), None)
    
    # If the category is not found, return a 404 error
    if not category_name:
        return render(request, '404.html', status=404)
    
    # Redirect to the events page with the category as a query parameter
    events_url = reverse('events')  # Ensure 'event_list' is your event page URL name
    return redirect(f"{events_url}?category={slug}")

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        # Validate fields are not empty
        if not email or not password:
            messages.error(request, 'All fields are required.')
            return redirect('login')

        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Enter a valid email address.')
            return redirect('login')

        # Check if user with this email exists
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'No user with this email exists.')
            return redirect('login')

        # Authenticate using username (email is not the login field by default)
        user = authenticate(request, username=user_obj.username, password=password)

        if user is not None:
            login(request, user)
            # messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('home')  # Replace with your actual home page
        else:
            messages.error(request, 'Incorrect credentials')
            return redirect('login')

    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('home')


def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('fname', '').strip()
        last_name = request.POST.get('lname', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        cpassword = request.POST.get('cpassword', '')

        context = {
            'fname': first_name,
            'lname': last_name,
            'username': username,
            'email': email
        }

        if not first_name or not last_name or not email or not password or not cpassword:
            messages.error(request, "All fields are required.")
            return render(request, 'register.html', context)

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return render(request, 'register.html', context)

        if password != cpassword:
            messages.error(request, "Passwords do not match.")
            return render(request, 'register.html', context)

        if len(password) < 8 or not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            messages.error(request, "Password must be at least 8 characters long and include both letters and numbers.")
            return render(request, 'register.html', context)

        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, 'register.html', context)

        if User.objects.filter(username=username).exists():
            messages.error(request, "An account with this username already exists.")
            return render(request, 'register.html', context)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        user.save()

        UserProfile.objects.create(
            username=user,
            first_name=first_name,
            last_name=last_name,
            email=email
        )

        messages.success(request, "Registration successful! You can now log in.")
        return redirect('login')

    return render(request, 'register.html')
def userProfile(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('home')  # Redirect to a home page or another appropriate page.

    try:
        profile = UserProfile.objects.get(username=user)
    except UserProfile.DoesNotExist:
        profile = None

    # Get avatars
    avatars = UserAvatar.objects.filter(profile=profile) if profile else []
    current_avatar = avatars.filter(is_current=True).first() if avatars else None
    previous_avatars = avatars.exclude(is_current=True) if avatars else []

    if request.method == 'POST':
        # Restrict updates to authenticated user who owns the profile
        if not request.user.is_authenticated or request.user.username != username:
            messages.error(request, 'You are not authorized to edit this profile.')
            return redirect('user-profile', username=username)

        avatar = request.FILES.get('avatar')
        first_name = request.POST.get('first-name')
        last_name = request.POST.get('last-name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        country = request.POST.get('country')
        city = request.POST.get('city')
        facebook = request.POST.get('facebook')
        instagram = request.POST.get('instagram')
        twitter = request.POST.get('twitter')

        # Validate avatar file
        if avatar and not avatar.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            messages.error(request, 'Please upload a valid image file (jpg, jpeg, or png).')
            return redirect('user-profile', username=username)

        # Ensure profile exists
        if not profile:
            profile = UserProfile.objects.create(username=user)

        # Handle avatar upload
        if avatar:
            # Mark existing current avatar as non-current
            if current_avatar:
                current_avatar.is_current = False
                current_avatar.save()
            # Create new avatar
            UserAvatar.objects.create(
                profile=profile,
                avatar=avatar,
                is_current=True
            )

        # Update User model fields
        user.first_name = first_name or user.first_name
        user.last_name = last_name or user.last_name
        user.email = email or user.email
        user.save()

        # Update UserProfile fields
        profile.phone = phone or profile.phone
        profile.country = country or profile.country
        profile.city = city or profile.city
        profile.facebook_link = facebook or profile.facebook_link
        profile.instagram_link = instagram or profile.instagram_link
        profile.twitter_link = twitter or profile.twitter_link
        profile.save()

        messages.success(request, 'Profile updated successfully.')
        return redirect('user-profile', username=username)

    context = {
        'profile': profile,
        'username': username,
        'userdata': user,
        'user': request.user,
        'current_avatar': current_avatar,
        'previous_avatars': previous_avatars
    }

    return render(request, 'user-profile.html', context)


def get_event_status(event):
    now = timezone.now()
    event_datetime = timezone.make_aware(datetime.combine(event.date, event.time))

    delta_days = (event_datetime.date() - now.date()).days

    if now.date() == event.date:
        return (
            "Ongoing",
            "badge bg-warning text-dark",
            "Happening today"
        )
    elif delta_days > 0:
        return (
            "Upcoming",
            "badge bg-success",
            f"{delta_days} day{'s' if delta_days != 1 else ''} remaining"
        )
    else:
        past_days = abs(delta_days)
        return (
            "Past",
            "badge bg-secondary",
            f"{past_days} day{'s' if past_days != 1 else ''} ago"
        )

@login_required(login_url='/login/')
def dashboard(request):
    today = timezone.now().date()

    # Upcoming events: today or later, ordered soonest first
    upcoming_events = Event.objects.filter(
        created_by=request.user,
        date__gte=today
    ).order_by('date')

    # Past events: before today, ordered latest first
    past_events = Event.objects.filter(
        created_by=request.user,
        date__lt=today
    ).order_by('-date')

    # Combine both, upcoming first
    all_events = list(chain(upcoming_events, past_events))

    paginator = Paginator(all_events, 6)
    page_number = request.GET.get('page')
    events = paginator.get_page(page_number)

    # Add status and badge class
    for event in events:
        event.status, event.badge_class, event.day_info = get_event_status(event)

    return render(request, 'dashboard.html', {
        'events': events,
        'today': today
    })
def my_tickets(request):
    # Get orders that belong to the logged-in user and have a completed payment status
    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related('items__ticket_type', 'event')
        .order_by('-created_at')
    )

    # Paginate the orders with a maximum of 9 per page
    paginator = Paginator(orders, 6)  # Show 6 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'my-tickets.html', {'page_obj': page_obj})

@login_required(login_url='/login/')
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, created_by=request.user)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        date = request.POST.get('date')
        time = request.POST.get('time')
        location = request.POST.get('location', '').strip()
        map_link = request.POST.get('map_link', '').strip()
        image = request.FILES.get('image')

        # Validate image formats
        allowed_extensions = ['jpg', 'jpeg', 'png']
        images_to_validate = [image]
        for i in range(1, 5):
            img = request.FILES.get(f'carousel_image_{i}')
            if img:
                images_to_validate.append(img)

        for img in images_to_validate:
            if img:
                ext = img.name.split('.')[-1].lower()
                if ext not in allowed_extensions:
                    messages.error(request, 'Images must be in JPG, JPEG, or PNG format.')
                    return redirect('edit-event', event_id=event.id)

        # Required field validation
        if not all([name, description, date, time, location, map_link]):
            messages.error(request, 'Please fill all required fields.')
            return redirect('edit-event', event_id=event.id)

        if len(description) > 500:
            messages.error(request, 'Description cannot exceed 500 characters.')
            return redirect('edit-event', event_id=event.id)

        # Update event fields
        event.name = name
        event.description = description
        event.date = date
        event.time = time
        event.location = location
        event.map_link = map_link

        if image:
            event.image = image

        # Update carousel images
        for i in range(1, 5):
            delete_flag = request.POST.get(f'delete_carousel_{i}') == 'on'
            new_image = request.FILES.get(f'carousel_image_{i}')

            field_name = f'carousel_image_{i}'
            if delete_flag:
                setattr(event, field_name, None)
            elif new_image:
                setattr(event, field_name, new_image)

        event.save()

        # Handle guest face deletions
        for face in event.faces.all():
            if request.POST.get(f'delete_face_{face.id}') == 'on':
                face.delete()

        # Add new guest faces
        for file in request.FILES.getlist('new_faces'):
            if file.name.split('.')[-1].lower() in allowed_extensions:
                EventFace.objects.create(event=event, image=file)

        # Update existing highlights
        for highlight in event.highlights.all():
            new_text = request.POST.get(f'highlight_{highlight.id}', '').strip()
            if new_text:
                highlight.text = new_text
                highlight.save()

        messages.success(request, 'Event updated successfully.')
        return redirect('edit-event', event_id=event.id)

    return render(request, 'edit-event.html', {'event': event})

@login_required(login_url='/login/')
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, created_by=request.user)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully.')
        return redirect('dashboard')
    return redirect('dashboard')  # fallback

def ticket_purchase(request):
    return render(request, 'tickets-purchase.html')


@login_required(login_url='/login/')
def create_event(request):
    if request.method == 'POST':
        name = request.POST.get('event-name', '').strip()
        category = request.POST.get('category', '').strip()
        description = request.POST.get('description', '').strip()
        date = request.POST.get('date', '')
        time = request.POST.get('time', '')
        address = request.POST.get('location', '').strip()
        city = request.POST.get('city', '').strip()
        country = 'Pakistan'  # Fixed to Pakistan
        map_link = request.POST.get('map_link', '').strip()
        capacity = request.POST.get('capacity', '').strip()
        image = request.FILES.get('image')
        carousel_image_1 = request.FILES.get('carousel_image_1')
        carousel_image_2 = request.FILES.get('carousel_image_2')
        carousel_image_3 = request.FILES.get('carousel_image_3')
        carousel_image_4 = request.FILES.get('carousel_image_4')
        is_free = request.POST.get('is-free-event') == 'on'

        # Validate image type for event image and carousel images
        allowed_extensions = ['jpg', 'jpeg', 'png']
        images_to_validate = [image, carousel_image_1, carousel_image_2, carousel_image_3, carousel_image_4]
        
        for img in images_to_validate:
            if img:
                ext = img.name.split('.')[-1].lower()
                if ext not in allowed_extensions:
                    messages.error(request, 'Images must be in JPG, JPEG, or PNG format.')
                    # Prepare context for re-rendering
                    context = {
                        'form_data': {
                            'event_name': name,
                            'category': category,
                            'description': description,
                            'date': date,
                            'time': time,
                            'location': address,
                            'city': city,
                            'map_link': map_link,
                            'capacity': capacity,
                            'is_free_event': is_free,
                        },
                        'ticket_types': [
                            {
                                'name': name,
                                'quantity': qty,
                                'price': price if not is_free else '0'
                            }
                            for name, qty, price in zip(
                                request.POST.getlist('ticket-name') or [''],
                                request.POST.getlist('ticket-quantity') or [''],
                                request.POST.getlist('ticket-price') or ['']
                            )
                        ] or [{'name': '', 'quantity': '', 'price': ''}],
                        'highlights': request.POST.getlist('highlights')[:3] or ['', '', ''],
                        'bank_accounts': [
                            {
                                'bank_name': name,
                                'account_title': title,
                                'iban_number': iban
                            }
                            for name, title, iban in zip(
                                request.POST.getlist('bank-name') or [''],
                                request.POST.getlist('account-title') or [''],
                                request.POST.getlist('iban-number') or ['']
                            )
                        ] or [{'bank_name': '', 'account_title': '', 'iban_number': ''}]
                    }
                    return render(request, 'create-event.html', context)

        # Handle empty capacity
        capacity = int(capacity) if capacity else 0

        # Required fields validation
        if not all([name, description, date, time, address, city, map_link, image]):
            messages.error(request, 'Please fill all required fields.')
            # Prepare context for re-rendering
            context = {
                'form_data': {
                    'event_name': name,
                    'category': category,
                    'description': description,
                    'date': date,
                    'time': time,
                    'location': address,
                    'city': city,
                    'map_link': map_link,
                    'capacity': capacity,
                    'is_free_event': is_free,
                },
                'ticket_types': [
                    {
                        'name': name,
                        'quantity': qty,
                        'price': price if not is_free else '0'
                    }
                    for name, qty, price in zip(
                        request.POST.getlist('ticket-name') or [''],
                        request.POST.getlist('ticket-quantity') or [''],
                        request.POST.getlist('ticket-price') or ['']
                    )
                ] or [{'name': '', 'quantity': '', 'price': ''}],
                'highlights': request.POST.getlist('highlights')[:3] or ['', '', ''],
                'bank_accounts': [
                    {
                        'bank_name': name,
                        'account_title': title,
                        'iban_number': iban
                    }
                    for name, title, iban in zip(
                        request.POST.getlist('bank-name') or [''],
                        request.POST.getlist('account-title') or [''],
                        request.POST.getlist('iban-number') or ['']
                    )
                ] or [{'bank_name': '', 'account_title': '', 'iban_number': ''}]
            }
            return render(request, 'create-event.html', context)

        # Description validation (check length according to model field)
        max_description_length = 500
        if len(description) > max_description_length:
            messages.error(request, f'Description cannot be longer than {max_description_length} characters.')
            # Prepare context for re-rendering
            context = {
                'form_data': {
                    'event_name': name,
                    'category': category,
                    'description': description,
                    'date': date,
                    'time': time,
                    'location': address,
                    'city': city,
                    'map_link': map_link,
                    'capacity': capacity,
                    'is_free_event': is_free,
                },
                'ticket_types': [
                    {
                        'name': name,
                        'quantity': qty,
                        'price': price if not is_free else '0'
                    }
                    for name, qty, price in zip(
                        request.POST.getlist('ticket-name') or [''],
                        request.POST.getlist('ticket-quantity') or [''],
                        request.POST.getlist('ticket-price') or ['']
                    )
                ] or [{'name': '', 'quantity': '', 'price': ''}],
                'highlights': request.POST.getlist('highlights')[:3] or ['', '', ''],
                'bank_accounts': [
                    {
                        'bank_name': name,
                        'account_title': title,
                        'iban_number': iban
                    }
                    for name, title, iban in zip(
                        request.POST.getlist('bank-name') or [''],
                        request.POST.getlist('account-title') or [''],
                        request.POST.getlist('iban-number') or ['']
                    )
                ] or [{'bank_name': '', 'account_title': '', 'iban_number': ''}]
            }
            return render(request, 'create-event.html', context)

        ticket_names = request.POST.getlist('ticket-name')
        ticket_quantities = request.POST.getlist('ticket-quantity')
        ticket_prices = request.POST.getlist('ticket-price') if not is_free else [0] * len(ticket_names)
        highlights = request.POST.getlist('highlights')
        guest_faces = [
            request.FILES.get('guest_face_1'),
            request.FILES.get('guest_face_2'),
            request.FILES.get('guest_face_3')
        ]

        # Validate if free event has more than one ticket type
        if is_free and len(ticket_names) > 1:
            messages.error(request, 'Free events can only have one ticket type.')
            # Prepare context for re-rendering
            context = {
                'form_data': {
                    'event_name': name,
                    'category': category,
                    'description': description,
                    'date': date,
                    'time': time,
                    'location': address,
                    'city': city,
                    'map_link': map_link,
                    'capacity': capacity,
                    'is_free_event': is_free,
                },
                'ticket_types': [
                    {
                        'name': name,
                        'quantity': qty,
                        'price': price if not is_free else '0'
                    }
                    for name, qty, price in zip(
                        request.POST.getlist('ticket-name') or [''],
                        request.POST.getlist('ticket-quantity') or [''],
                        request.POST.getlist('ticket-price') or ['']
                    )
                ] or [{'name': '', 'quantity': '', 'price': ''}],
                'highlights': request.POST.getlist('highlights')[:3] or ['', '', ''],
                'bank_accounts': [
                    {
                        'bank_name': name,
                        'account_title': title,
                        'iban_number': iban
                    }
                    for name, title, iban in zip(
                        request.POST.getlist('bank-name') or [''],
                        request.POST.getlist('account-title') or [''],
                        request.POST.getlist('iban-number') or ['']
                    )
                ] or [{'bank_name': '', 'account_title': '', 'iban_number': ''}]
            }
            return render(request, 'create-event.html', context)

        # Create event with city and country
        event = Event.objects.create(
            name=name,
            category=category,
            description=description,
            date=date,
            time=time,
            location=address,
            city=city,
            country=country,
            created_by=request.user,
            image=image,
            map_link=map_link,
            capacity=capacity,
            is_free=is_free,
            carousel_image_1=carousel_image_1,
            carousel_image_2=carousel_image_2,
            carousel_image_3=carousel_image_3,
            carousel_image_4=carousel_image_4
        )

        # Create TicketTypes
        for i in range(len(ticket_names)):
            t_name = ticket_names[i].strip()
            t_qty = ticket_quantities[i].strip()
            try:
                t_price = float(ticket_prices[i]) if not is_free else 0
            except ValueError:
                t_price = 0

            if not t_name or not t_qty:
                continue

            if t_price < 0:
                messages.error(request, 'Ticket prices cannot be negative.')
                event.delete()
                # Prepare context for re-rendering
                context = {
                    'form_data': {
                        'event_name': name,
                        'category': category,
                        'description': description,
                        'date': date,
                        'time': time,
                        'location': address,
                        'city': city,
                        'map_link': map_link,
                        'capacity': capacity,
                        'is_free_event': is_free,
                    },
                    'ticket_types': [
                        {
                            'name': name,
                            'quantity': qty,
                            'price': price if not is_free else '0'
                        }
                        for name, qty, price in zip(
                            request.POST.getlist('ticket-name') or [''],
                            request.POST.getlist('ticket-quantity') or [''],
                            request.POST.getlist('ticket-price') or ['']
                        )
                    ] or [{'name': '', 'quantity': '', 'price': ''}],
                    'highlights': request.POST.getlist('highlights')[:3] or ['', '', ''],
                    'bank_accounts': [
                        {
                            'bank_name': name,
                            'account_title': title,
                            'iban_number': iban
                        }
                        for name, title, iban in zip(
                            request.POST.getlist('bank-name') or [''],
                            request.POST.getlist('account-title') or [''],
                            request.POST.getlist('iban-number') or ['']
                        )
                    ] or [{'bank_name': '', 'account_title': '', 'iban_number': ''}]
                }
                return render(request, 'create-event.html', context)

            TicketType.objects.create(
                event=event,
                name=t_name,
                price=t_price,
                quantity=int(t_qty)
            )

        # Create EventFace entries
        for face in guest_faces:
            if face:
                EventFace.objects.create(event=event, image=face)

        # Create EventHighlight entries
        for text in highlights[:3]:
            if text.strip():
                EventHighlight.objects.create(event=event, text=text.strip())

        # Create BankAccount entries
        bank_names = request.POST.getlist('bank-name')
        account_titles = request.POST.getlist('account-title')
        iban_numbers = request.POST.getlist('iban-number')

        for i in range(len(bank_names)):
            bank_name = bank_names[i].strip()
            account_title = account_titles[i].strip()
            iban_number = iban_numbers[i].strip()

            if bank_name and account_title and iban_number:
                BankAccount.objects.create(
                    event=event,
                    bank_name=bank_name,
                    account_title=account_title,
                    iban_number=iban_number
                )

        messages.success(request, 'Event created successfully!')
        return render(request, 'create-event.html', {
            'form_data': {
                'event_name': '',
                'category': '',
                'description': '',
                'date': '',
                'time': '',
                'location': '',
                'city': '',
                'map_link': '',
                'capacity': '',
                'is_free_event': False,
            },
            'ticket_types': [{'name': '', 'quantity': '', 'price': ''}],
            'highlights': ['', '', ''],
            'bank_accounts': [{'bank_name': '', 'account_title': '', 'iban_number': ''}]
        })

    # Initial GET request
    context = {
        'form_data': {
            'event_name': '',
            'category': '',
            'description': '',
            'date': '',
            'time': '',
            'location': '',
            'city': '',
            'map_link': '',
            'capacity': '',
            'is_free_event': False,
        },
        'ticket_types': [{'name': '', 'quantity': '', 'price': ''}],
        'highlights': ['', '', ''],
        'bank_accounts': [{'bank_name': '', 'account_title': '', 'iban_number': ''}]
    }
    return render(request, 'create-event.html', context)

def get_remaining_days(event):
    now = timezone.now()
    event_datetime = timezone.make_aware(datetime.combine(event.date, event.time))
    
    if now < event_datetime:
        # Calculate the remaining days for upcoming events
        remaining_days = (event_datetime - now).days
        return f"{remaining_days} days left"
    elif now.date() > event.date:
        # Calculate the past days for past events
        past_days = (now - event_datetime).days
        return f"{past_days} days ago"
    else:
        return "Today"

def events(request):
    events = Event.objects.prefetch_related('highlights', 'faces', 'tickets').all()

    # Get filter parameters
    search = request.GET.get('search')
    event_type = request.GET.get('type')
    location_filter = request.GET.get('location')
    category_filter = request.GET.get('category')  # Get category from the URL query parameter
    print("Category filter:", category_filter)  
    show_filter = request.GET.get('show')

    # Apply search filter
    if search:
        events = events.filter(
            Q(name__icontains=search) |
            Q(location__icontains=search) |
            Q(highlights__text__icontains=search)
        ).distinct()

    # Apply type filter
    if event_type == 'free':
        events = events.filter(is_free=True)
    elif event_type == 'paid':
        events = events.filter(is_free=False)

    # Apply location filter
    if location_filter:
        events = events.filter(location__icontains=location_filter)

    # Apply category filter (use slug to filter)
    if category_filter:
        events = events.filter(category=category_filter)

    # Filter by upcoming or past events
    now = timezone.now()
    if show_filter == 'past':
        events = events.filter(date__lt=now)
    elif not show_filter:
        events = events.filter(date__gte=now)

    # Annotate and enrich events
    for event in events:
        event_datetime = timezone.make_aware(datetime.combine(event.date, event.time))
        delta_days = (event_datetime.date() - now.date()).days

        if delta_days > 0:
            event.remaining_days = f"{delta_days} days remaining"
        elif delta_days == 0:
            event.remaining_days = "Today"
        else:
            event.remaining_days = f"{abs(delta_days)} days ago"

        # Ticket info
        ticket_info = []
        for ticket in event.tickets.all():
            total_quantity = ticket.quantity
            sold_quantity = OrderItem.objects.filter(ticket_type=ticket).aggregate(models.Sum('quantity'))['quantity__sum'] or 0
            remaining_quantity = total_quantity - sold_quantity
            ticket_info.append({
                'name': ticket.name,
                'total_quantity': total_quantity,
                'remaining_quantity': remaining_quantity
            })
        event.ticket_info = ticket_info
        event.is_past = delta_days < 0

    # Sorting
    sort_by = request.GET.get('sort_by', 'least_remaining')
    is_past = request.GET.get('show') == 'past'

    if is_past:
        events = sorted(events, key=lambda x: (date.today() - x.date).days)
        if sort_by == 'most_remaining':
            events = sorted(events, key=lambda x: (date.today() - x.date).days, reverse=True)
    else:
        if sort_by == 'most_remaining':
            events = sorted(events, key=lambda x: x.remaining_days, reverse=True)
        elif sort_by == 'least_remaining':
            events = sorted(events, key=lambda x: x.remaining_days)

    # Pagination
    paginator = Paginator(events, 12)
    page = request.GET.get('page')
    events = paginator.get_page(page)

    # Locations
    locations = Event.objects.exclude(location__isnull=True).exclude(location__exact='').values_list('location', flat=True).distinct()
    print(Event.CATEGORY_CHOICES)
    context = {
        'events': events,
        'locations': locations,
        'sort_by': sort_by,
        'category_choices': Event.CATEGORY_CHOICES,
        'selected_category': category_filter,  # Selected category filter passed to template
    }

    return render(request, 'events.html', context)



def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    today = timezone.now().date()
    
     # Fetch the UserProfile associated with the created_by user (ForeignKey lookup)
    user_profile = UserProfile.objects.filter(username=event.created_by).first()  # 'event.created_by' is a User instance

    # Retrieve the current avatar for the user profile (if any)
    current_avatar = UserAvatar.objects.filter(profile=user_profile, is_current=True).first()

    is_past = event.date < today  # No need for .date()

   # Initialize ticket information
    ticket_info = []

    # Iterate over tickets related to the event and calculate sold and remaining tickets
    for ticket in event.tickets.all():
        # Calculate sold tickets by aggregating the quantity from the OrderItem model
        sold_tickets = OrderItem.objects.filter(ticket_type=ticket).aggregate(models.Sum('quantity'))['quantity__sum'] or 0
        remaining_tickets = ticket.quantity - sold_tickets
        
        ticket_info.append({
            'ticket': ticket,
            'sold_tickets': sold_tickets,
            'remaining_tickets': remaining_tickets
        })

    # Calculate total tickets and remaining tickets for the event
    total_tickets = sum(ticket['ticket'].quantity for ticket in ticket_info)
    remaining_tickets_total = sum(ticket['remaining_tickets'] for ticket in ticket_info)

    return render(request, 'event-detail.html', {
        'event': event,
        'is_past': is_past,
        'ticket_info': ticket_info,
        'total_tickets': total_tickets,
        'remaining_tickets_total': remaining_tickets_total,
        'current_avatar': current_avatar
    })



def buy_ticket(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    today = timezone.now().date()

    is_past = event.date < today  # No need for .date()

   # Initialize ticket information
    ticket_info = []

    # Iterate over tickets related to the event and calculate sold and remaining tickets
    for ticket in event.tickets.all():
        # Calculate sold tickets by aggregating the quantity from the OrderItem model
        sold_tickets = OrderItem.objects.filter(ticket_type=ticket).aggregate(models.Sum('quantity'))['quantity__sum'] or 0
        remaining_tickets = ticket.quantity - sold_tickets
        
        ticket_info.append({
            'ticket': ticket,
            'sold_tickets': sold_tickets,
            'remaining_tickets': remaining_tickets
        })

    # Calculate total tickets and remaining tickets for the event
    total_tickets = sum(ticket['ticket'].quantity for ticket in ticket_info)
    remaining_tickets_total = sum(ticket['remaining_tickets'] for ticket in ticket_info)

    return render(request, 'buy-ticket.html', {
        'event': event,
        'is_past': is_past,
        'ticket_info': ticket_info,
        'total_tickets': total_tickets,
        'remaining_tickets_total': remaining_tickets_total,
    })

@login_required
def purchase_ticket(request):
    if request.method == 'POST':
        ticket_type_id = request.POST.get('ticket_type')
        quantity = int(request.POST.get('quantity', 1))

        if not ticket_type_id:
            messages.error(request, 'Ticket type is required.')
            return redirect('event_list')  # Or wherever you want to send them back

        ticket_type = get_object_or_404(TicketType, id=ticket_type_id)
        total_sold = OrderItem.objects.filter(ticket_type=ticket_type).aggregate(Sum('quantity'))['quantity__sum'] or 0
        available = ticket_type.quantity - total_sold

        if available <= 0:
            messages.error(request, f"No tickets available for '{ticket_type.name}' at the moment.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if quantity > available:
            messages.error(request, f"Only {available} tickets are available for '{ticket_type.name}'.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        # Create order
        order = Order.objects.create(
            user=request.user,
            event=ticket_type.event,
            full_name=request.user.get_full_name(),
            email=request.user.email,
            phone=request.user.userprofile_set.first().phone if request.user.userprofile_set.exists() else '',
            total_price=0,  # will update later
            payment_status='completed'
        )

        # Create OrderItem
        order_item = OrderItem.objects.create(
            order=order,
            ticket_type=ticket_type,
            quantity=quantity,
            item_price=ticket_type.price
        )

        total_price = quantity * ticket_type.price

        # Update order price
        order.total_price = total_price
        order.save()

         # --- Start of Sales Logic for Single Item ---
        ticket_sale = TicketSale.objects.create(
            event=order.event,
            ticket=ticket_type,
            quantity=quantity,
            total_price=total_price
        )
        ticket_sale.save()
        # --- End of Sales Logic for Single Item ---        

        # Generate QR Code data
        qr_code_data = {
            'order_number': str(order.id),
            'user_email': order.user.email,
            'event_name': order.event.name,
            'event_date': order.event.date.strftime('%Y-%m-%d'),
            'ticket_details': [
                {
                    'ticket_type': ticket_type.name,
                    'quantity': quantity,
                    'total_price': str(total_price)
                }
            ],
            'total_price': str(total_price)
        }

        qr_code_data_str = json.dumps(qr_code_data)

        # Generate QR code with better quality
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )

        qr.add_data(qr_code_data_str)
        qr.make(fit=True)

        qr_code = qr.make_image(fill_color="black", back_color="white")

        qr_code_file = BytesIO()
        qr_code.save(qr_code_file, format='PNG')
        qr_code_file.seek(0)
        qr_code_filename = f"order_{order.id}_qr.png"
        qr_code_path = default_storage.save(f"qr_codes/{qr_code_filename}", ContentFile(qr_code_file.read()))

        qr_code_url = f"{settings.SITE_URL}{default_storage.url(qr_code_path)}"

        order.qr_code = default_storage.url(qr_code_path) 
        order.save()

        # Prepare the email context
        email_context = {
            'event': ticket_type.event,
            'order': order,
            'order_items': [order_item],
            'total_price': total_price,
            'qr_code_url': qr_code_url,
            'order_number': order.id,
        }

        email_body = render_to_string('ticket_purchase_confirmation.html', email_context)

        # Send the email
        send_mail(
            subject=f"Ticket Purchase Confirmation - Order #{order.id}",
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email],
            html_message=email_body,
        )

        messages.success(request, 'Ticket purchased successfully!')
        return redirect('home')

    else:
        messages.error(request, 'Invalid request.')
        return redirect('events')

@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.get_total_price() for item in cart_items)
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total,
    })


@login_required
def add_to_cart(request, event_id):
    if request.method == 'POST':
        ticket_id = request.POST.get('ticket_type')
        quantity = int(request.POST.get('quantity', 1))
        ticket_type = get_object_or_404(TicketType, id=ticket_id)
        event = get_object_or_404(Event, id=event_id)

        # Calculate sold tickets (confirmed orders)
        total_sold = OrderItem.objects.filter(ticket_type=ticket_type).aggregate(Sum('quantity'))['quantity__sum'] or 0
        
        # Calculate tickets currently in carts
        total_in_carts = CartItem.objects.filter(ticket=ticket_type).aggregate(Sum('quantity'))['quantity__sum'] or 0
        
        # Available tickets considering both sold and in carts
        available = ticket_type.quantity - total_sold - total_in_carts

        if available <= 0:
            messages.error(request, f"No tickets available for '{ticket_type.name}' at the moment.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if quantity > available:
            messages.error(request, f"Only {available} tickets are available for '{ticket_type.name}'. Please adjust your quantity.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        # Now add to cart
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            event=event,
            ticket=ticket_type,
            defaults={'quantity': quantity}
        )

        if not created:
            if cart_item.quantity + quantity > available:
                messages.error(request, f"Adding {quantity} more exceeds available tickets ({available}). Please adjust your quantity.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

            cart_item.quantity += quantity
            cart_item.save()

        messages.success(request, 'Item added to cart successfully.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return redirect('event-detail', event_id=event_id)


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart')

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')

    total_price = 0
    order_items = []
    insufficient_stock = False

    # First, create the order with total_price = 0
    order = Order.objects.create(
        user=request.user,
        event=cart_items[0].event,
        full_name=request.user.get_full_name(),
        email=request.user.email,
        phone=request.user.userprofile_set.first().phone if request.user.userprofile_set.exists() else '',
        total_price=0,  # We will update this later
        payment_status='completed'
    )

    # Loop through each cart item to calculate the total price and create the OrderItems
    for item in cart_items:
        ticket_type = get_object_or_404(TicketType, id=item.ticket.id)
        total_sold = OrderItem.objects.filter(ticket_type=ticket_type).aggregate(Sum('quantity'))['quantity__sum'] or 0
        available = ticket_type.quantity - total_sold

        if item.quantity > available:
            messages.error(request, f"Only {available} tickets are remaining for '{ticket_type.name}'.")
            insufficient_stock = True
            break

        # Create order item and calculate total price
        order_item = OrderItem.objects.create(
            order=order,  # Associate with the created order
            ticket_type=ticket_type,
            quantity=item.quantity,
            item_price=ticket_type.price
        )

        order_items.append(order_item)
        total_price += order_item.quantity * order_item.item_price  # Calculate total price after adding the item

    # If there is insufficient stock, delete the order and order items
    if insufficient_stock:
        order.delete()
        return redirect('cart')

    # Update the order's total price after adding all items
    order.total_price = total_price
    order.save()

      # --- Start of Sales Logic ---
    # Create sales records for each ticket type sold
    for order_item in order_items:
        ticket_sale = TicketSale.objects.create(
            event=order.event,
            ticket=order_item.ticket_type,
            quantity=order_item.quantity,
            total_price=order_item.quantity * order_item.item_price
        )
        ticket_sale.save()
    # --- End of Sales Logic ---

    # Generate QR code data for the order
    qr_code_data = {
        'order_number': str(order.id), 
        'user_email': order.user.email,
        'event_name': order.event.name,
        'event_date': order.event.date.strftime('%Y-%m-%d'),  # Convert date to string format
        'ticket_details': [
            {
                'ticket_type': item.ticket_type.name,
                'quantity': item.quantity,
                'total_price': str(item.quantity * item.item_price)  # Convert Decimal to string
            }
            for item in order_items
        ],
        'total_price': str(total_price)  # Convert Decimal to string
    }
    # Convert QR data to a string format (JSON for structured data)
   
    qr_code_data_str = json.dumps(qr_code_data)

    # Generate QR code with better quality
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    qr.add_data(qr_code_data_str)
    qr.make(fit=True)

    qr_code = qr.make_image(fill_color="black", back_color="white")

    # Save QR code image to a temporary file
    qr_code_file = BytesIO()
    qr_code.save(qr_code_file, format='PNG')
    qr_code_file.seek(0)
    qr_code_filename = f"order_{order.id}_qr.png"
    qr_code_path = default_storage.save(f"qr_codes/{qr_code_filename}", ContentFile(qr_code_file.read()))

    qr_code_url = f"{settings.SITE_URL}{default_storage.url(qr_code_path)}"

    order.qr_code = default_storage.url(qr_code_path) 
    order.save()


    # Prepare the email context
    email_context = {
        'event': cart_items[0].event,
        'order': order,
        'order_items': order_items,  # All order items
        'total_price': total_price,
        'qr_code_url': qr_code_url,  # Full URL for QR code
        'order_number': order.id,
    }

    # Render the email body from the template
    email_body = render_to_string('ticket_purchase_confirmation.html', email_context)

    # Send the email
    send_mail(
        subject=f"Ticket Purchase Confirmation - Order #{order.id}", 
        message=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        html_message=email_body,
    )

    # Clear the cart after purchase
    cart_items.delete()

    messages.success(request, 'Purchase completed successfully.')
    return redirect('home')
  
@login_required
def validate_qr(request):
    if request.method == 'POST':
        if request.FILES.get('qr_image'):
            # Uploaded QR Image
            image = Image.open(request.FILES['qr_image'])
            # Convert PIL image to numpy array for OpenCV
            image_np = np.array(image)
            # Convert RGB to BGR (OpenCV uses BGR format)
            image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

            # Decode the QR code using OpenCV
            detector = cv2.QRCodeDetector()
            retval, decoded_data, points, straight_qrcode = detector(image_bgr)

            if retval:
                qr_data_str = decoded_data
            else:
                return render(request, 'qr_validation_failed.html', {'error': 'No QR code detected'})
        else:
            # JSON from scanner
            try:
                body = json.loads(request.body)
                qr_data_str = body.get('qr_code')
                if qr_data_str is None:
                    return JsonResponse({'error': 'Invalid QR code data'}, status=400)
            except:
                return JsonResponse({'error': 'Invalid request body'}, status=400)

        try:
            qr_data = json.loads(qr_data_str)
            order_id = qr_data.get('order_id')
            email = qr_data.get('user_email')

            order = Order.objects.filter(id=order_id, email=email).first()

            if order:
                if order.is_redeemed:
                    return render(request, 'qr_validation_failed.html', {'error': 'This ticket has already been redeemed.'})
                else:
                    order.is_redeemed = True
                    order.redeemed_at = timezone.now()
                    order.save()
                    return render(request, 'qr_validation_success.html', {'qr_data': qr_data})
            else:
                return render(request, 'qr_validation_failed.html', {'error': 'Order not found'})

        except json.JSONDecodeError:
            return render(request, 'qr_validation_failed.html', {'error': 'Invalid QR code format'})

    return render(request, 'validate_qr.html')

def event_sales(request):
    # Default time range is "All Time"
    time_range = request.GET.get('time_range', 'all')

    # Fetch all events created by the logged-in user
    all_user_events = Event.objects.filter(created_by=request.user).order_by('-date')

    # Filter only events with at least one ticket sale
    events_with_sales = []
    for event in all_user_events:
        if TicketSale.objects.filter(event=event).exists():
            events_with_sales.append(event)

    # Paginate events with sales (12 per page)
    paginator = Paginator(events_with_sales, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Total events created (regardless of sales)
    total_events = all_user_events.count()

    # Calculate overall total sales and revenue
    total_sales = 0
    total_revenue = 0
    for event in all_user_events:
        sales = TicketSale.objects.filter(event=event)
        total_sales += sum(sale.quantity for sale in sales)
        total_revenue += sum(sale.total_price for sale in sales)

    # Calculate last month's sales and revenue
    last_month_start = timezone.now() - timedelta(days=30)
    last_month_end = timezone.now() - timedelta(days=1)
    last_month_events = all_user_events.filter(date__gte=last_month_start, date__lte=last_month_end)

    last_month_total_sales = 0
    last_month_total_revenue = 0
    for event in last_month_events:
        sales = TicketSale.objects.filter(event=event)
        last_month_total_sales += sum(sale.quantity for sale in sales)
        last_month_total_revenue += sum(sale.total_price for sale in sales)

    # Calculate percentage changes
    event_percentage_change = ((total_events - last_month_events.count()) / last_month_events.count()) * 100 if last_month_events.count() > 0 else 0
    sales_percentage_change = ((total_sales - last_month_total_sales) / last_month_total_sales) * 100 if last_month_total_sales > 0 else 0
    revenue_percentage_change = ((total_revenue - last_month_total_revenue) / last_month_total_revenue) * 100 if last_month_total_revenue > 0 else 0

    # Build event-wise sales data for the current page
    event_sales_data = []
    for event in page_obj:
        total_sales_event = 0
        total_revenue_event = 0
        remaining_tickets = 0

        for ticket in event.tickets.all():
            ticket_sales = TicketSale.objects.filter(event=event, ticket=ticket)
            quantity_sold = sum(sale.quantity for sale in ticket_sales)
            revenue = sum(sale.total_price for sale in ticket_sales)

            total_sales_event += quantity_sold
            total_revenue_event += revenue
            remaining_tickets += ticket.quantity - quantity_sold

        event_sales_data.append({
            'event': event,
            'total_sales': total_sales_event,
            'revenue': total_revenue_event,
            'remaining_tickets': remaining_tickets,
        })

    return render(request, 'event-sales.html', {
        'event_sales_data': event_sales_data,
        'time_range': time_range,
        'total_events': total_events,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'event_percentage_change': event_percentage_change,
        'sales_percentage_change': sales_percentage_change,
        'revenue_percentage_change': revenue_percentage_change,
        'page_obj': page_obj,
    })


def event_sales_detail(request, event_id):
    event = Event.objects.get(id=event_id)

    # Find the previous event (same user or organizer)
    previous_event = Event.objects.filter(
        created_by=event.created_by,  
        created_at__lt=event.created_at  # Use created_at instead of date
    ).order_by('-created_at').first()

    # Current event metrics
    total_sales = 0
    total_revenue = 0
    remaining_tickets = 0
    ticket_sales_summary = []

    ticket_sales_all = TicketSale.objects.filter(event=event)
    total_sales = sum(s.quantity for s in ticket_sales_all)
    total_revenue = sum(float(s.total_price) for s in ticket_sales_all)

    for ticket in event.tickets.all():
        ticket_sales = ticket_sales_all.filter(ticket=ticket)
        quantity_sold = sum(s.quantity for s in ticket_sales)
        revenue = sum(float(s.total_price) for s in ticket_sales)
        remaining = ticket.quantity - quantity_sold

        ticket_sales_summary.append({
            'ticket': ticket,
            'ticket_sales_quantity': quantity_sold,
            'ticket_sales_revenue': revenue,
            'remaining_tickets': remaining
        })
        remaining_tickets += remaining

    # Sort and top performers based on revenue
    ticket_sales_summary.sort(key=lambda x: x['ticket_sales_revenue'], reverse=True)
    top_tickets = ticket_sales_summary[:3]

    # Add percentage values for pie chart and bars
    for item in ticket_sales_summary:
        item['percentage'] = (item['ticket_sales_quantity'] / total_sales) * 100 if total_sales > 0 else 0

    # Ticket distribution data (by revenue or quantity)
    ticket_distribution_labels = []
    ticket_distribution_data = []
    for item in ticket_sales_summary:
        ticket_distribution_labels.append(item['ticket'].name)
        ticket_distribution_data.append(item['ticket_sales_revenue'])

    # Default values if no previous event
    sales_change = revenue_change = remaining_change = 0

    if previous_event:
        prev_sales = TicketSale.objects.filter(event=previous_event)
        prev_total_sales = sum(s.quantity for s in prev_sales)
        prev_total_revenue = sum(float(s.total_price) for s in prev_sales)
        prev_remaining = sum(t.quantity for t in previous_event.tickets.all()) - prev_total_sales

        sales_change = ((total_sales - prev_total_sales) / prev_total_sales * 100) if prev_total_sales > 0 else 0
        revenue_change = ((total_revenue - prev_total_revenue) / prev_total_revenue * 100) if prev_total_revenue > 0 else 0
        remaining_change = ((remaining_tickets - prev_remaining) / prev_remaining * 100) if prev_remaining > 0 else 0

    context = {
        'event': event,
        'ticket_sales_data': ticket_sales_summary,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'remaining_tickets': remaining_tickets,
        'top_tickets': top_tickets,
        'sales_change': sales_change,
        'revenue_change': revenue_change,
        'remaining_change': remaining_change,
        'ticket_distribution_labels': ticket_distribution_labels,
        'ticket_distribution_data': ticket_distribution_data,
    }

    return render(request, 'event-sales-detail.html', context)



def event_attendees(request):
    # Get the range filter from the query params (defaults to 'all')
    range_filter = request.GET.get('range', 'all')
    user_events = Event.objects.filter(created_by=request.user)
    

    # Get current month and previous month ranges
    current_date = timezone.now()
    current_month_start = current_date.replace(day=1)
    previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)


    # Order events by date (latest to oldest)
    user_events = user_events.order_by('-date')

    total_events = user_events.count()
    total_attendees = OrderItem.objects.filter(order__event__in=user_events).aggregate(
        total=Sum('quantity')
    )['total'] or 0

    # Get event and attendee data for the previous month
    previous_month_events = Event.objects.filter(created_by=request.user, date__gte=previous_month_start)
    previous_month_total_events = previous_month_events.count()

    previous_month_attendees = OrderItem.objects.filter(order__event__in=previous_month_events).aggregate(
        total=Sum('quantity')
    )['total'] or 0

    # Calculate percentage change from last month
    event_percentage_change = 0
    if previous_month_total_events > 0:
        event_percentage_change = ((total_events - previous_month_total_events) / previous_month_total_events) * 100

    attendee_percentage_change = 0
    if previous_month_attendees > 0:
        attendee_percentage_change = ((total_attendees - previous_month_attendees) / previous_month_attendees) * 100

    top_location_data = Order.objects.filter(event__in=user_events).values(
        'event__location'
    ).annotate(count=Count('id')).order_by('-count').first()

    top_location = top_location_data['event__location'] if top_location_data else 'N/A'

    top_city_data = Order.objects.filter(event__in=user_events).values(
        'event__city'
    ).annotate(count=Count('id')).order_by('-count').first()

    top_city = top_city_data['event__city'] if top_location_data else 'N/A'

    # Paginate events
    paginator = Paginator(user_events, 12)  # 10 events per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

 

    return render(request, 'event-attendees.html', {
        'total_events': total_events,
        'total_attendees': total_attendees,
        'top_location': top_location,
        'top_city': top_city,
        'user_events': page_obj,  # Pass the paginated page object
        'range_filter': range_filter,  # Pass the selected range filter to the template
        'event_percentage_change': event_percentage_change,
        'attendee_percentage_change': attendee_percentage_change
       
    })

def event_attendee_stats(request, event_id):
    event = get_object_or_404(Event, id=event_id, created_by=request.user)

    # Filter by time range
    range_filter = request.GET.get('range', 'all')
    orderitem_qs = OrderItem.objects.filter(order__event=event)

    # Ticket Stats: Calculate total quantity and total revenue per ticket type
    ticket_stats = orderitem_qs.values(
        'ticket_type__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('item_price')
    )

    # Total Tickets Sold
    total_tickets = sum(item['total_quantity'] for item in ticket_stats)

    # Total Revenue
    total_revenue = sum(item['total_revenue'] for item in ticket_stats)

    # Unique Attendees
    unique_attendees = orderitem_qs.values('order__email').distinct().count()

    # Recent Attendees (Last 10 Orders)
    recent_attendees = orderitem_qs.select_related('order', 'ticket_type').order_by('-order__created_at')[:10]
    all_attendees = orderitem_qs.select_related('order', 'ticket_type').order_by('-order__created_at')
    
    # Calculate trends (compare to previous event if available)
    last_event = Event.objects.filter(created_by=request.user).exclude(id=event.id).order_by('-created_at').first()
    last_event_total_tickets = 0
    last_event_total_revenue = 0
    last_event_unique_attendees = 0

    if last_event:
        last_event_orderitem_qs = OrderItem.objects.filter(order__event=last_event)

        last_event_ticket_stats = last_event_orderitem_qs.values(
            'ticket_type__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('item_price')
        )

        last_event_total_tickets = sum(item['total_quantity'] for item in last_event_ticket_stats)
        last_event_total_revenue = sum(item['total_revenue'] for item in last_event_ticket_stats)
        last_event_unique_attendees = last_event_orderitem_qs.values('order__email').distinct().count()

    # Calculate percentage trends for tickets, revenue, and unique attendees
    tickets_trend = calculate_percentage_change(last_event_total_tickets, total_tickets)
    revenue_trend = calculate_percentage_change(last_event_total_revenue, total_revenue)
    attendees_trend = calculate_percentage_change(last_event_unique_attendees, unique_attendees)

    # Sales Over Time (grouped by day)
    sales_over_time = orderitem_qs.annotate(
        date=TruncDate('order__created_at')
    ).values('date').annotate(
        total_sales=Sum('item_price')
    ).order_by('date')

    sales_chart_labels = [entry['date'].strftime('%Y-%m-%d') for entry in sales_over_time]
    sales_chart_data = [entry['total_sales'] for entry in sales_over_time]

    # Ticket Type Distribution (pie chart)
    ticket_distribution = orderitem_qs.values(
        'ticket_type__name'
    ).annotate(
        count=Sum('quantity')
    )

    ticket_labels = [item['ticket_type__name'] for item in ticket_distribution]
    ticket_data = [item['count'] for item in ticket_distribution]

    return render(request, 'event-attendee-stats.html', {
        'event': event,
        'ticket_stats': ticket_stats,
        'total_tickets': total_tickets,
        'total_revenue': total_revenue,
        'unique_attendees': unique_attendees,
        'recent_attendees': recent_attendees,
        'range_filter': range_filter,
        'tickets_trend': tickets_trend,
        'revenue_trend': revenue_trend,
        'attendees_trend': attendees_trend,
        'all_attendees': all_attendees,
        'sales_chart_labels': sales_chart_labels,
        'sales_chart_data': sales_chart_data,
        'ticket_labels': ticket_labels,
        'ticket_data': ticket_data,
    })

def calculate_percentage_change(previous, current):
    if previous == 0:
        return 100 if current > 0 else 0
    return ((current - previous) / previous) * 100


def export_event_sales_report(request, event_id):
    event = Event.objects.get(id=event_id)
    all_sales = TicketSale.objects.filter(event=event)

    response = HttpResponse(content_type='text/csv')
    filename = f"{slugify(event.name)}_sales_report.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'Ticket Type',
        'Ticket Price',
        'Capacity',
        'Quantity Sold',
        'Remaining Tickets',
        'Revenue (PKR)',
        '% of Total Sales',
        '% of Revenue'
    ])

    # Totals for % calculations
    total_quantity = sum(s.quantity for s in all_sales)
    total_revenue = sum(float(s.total_price) for s in all_sales)

    for ticket in event.tickets.all():
        ticket_sales = all_sales.filter(ticket=ticket)
        quantity_sold = sum(s.quantity for s in ticket_sales)
        revenue = sum(float(s.total_price) for s in ticket_sales)
        remaining = ticket.quantity - quantity_sold

        percent_sales = (quantity_sold / total_quantity * 100) if total_quantity > 0 else 0
        percent_revenue = (revenue / total_revenue * 100) if total_revenue > 0 else 0

        writer.writerow([
            ticket.name,
            f"{ticket.price:.2f}",
            ticket.quantity,
            quantity_sold,
            remaining,
            f"{revenue:.2f}",
            f"{percent_sales:.1f}%",
            f"{percent_revenue:.1f}%"
        ])

    return response
def export_event_attendees_report(request, event_id):
    event = Event.objects.get(id=event_id)
    orders = Order.objects.filter(event=event, payment_status='completed')  # Only completed orders

    response = HttpResponse(content_type='text/csv')
    filename = f"{slugify(event.name)}_attendees_report.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'Full Name',
        'Email',
        'Phone Number',
        'Ticket Type',
        'Ticket Quantity',
        'Total Paid (PKR)',
        'Order Date',
        'City',
        'Country'
    ])

    for order in orders:
        profile = UserProfile.objects.filter(username=order.user).first()
        city = profile.city if profile else ''
        country = profile.country if profile else ''

        for item in order.items.all():
            writer.writerow([
                order.full_name,
                order.email,
                order.phone,
                item.ticket_type.name,
                item.quantity,
                f"{order.total_price:.2f}",
                order.created_at.strftime('%Y-%m-%d %H:%M'),
                city,
                country
            ])

    return response