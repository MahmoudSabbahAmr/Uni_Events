from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Event, Booking
from django.db import models
from django.core.paginator import Paginator



def home(request):
    total_events = Event.objects.count()
    total_bookings = Booking.objects.count()
    upcoming_count = Event.objects.filter(date__gte=timezone.now().date()).count()
    latest_events = Event.objects.filter(date__gte=timezone.now().date()).order_by('date')[:3]

    return render(request, 'events/home.html', {
        'total_events': total_events,
        'total_bookings': total_bookings,
        'upcoming_count': upcoming_count,
        'latest_events': latest_events,
    })



def events_list(request):
    query = request.GET.get('q', '')
    events = Event.objects.filter(date__gte=timezone.now().date()).order_by('date')

    if query:
        events = events.filter(
            models.Q(title__icontains=query) |
            models.Q(description__icontains=query) |
            models.Q(location__icontains=query) |
            models.Q(category__icontains=query)
        )

    # Pagination — 3 events per page
    paginator = Paginator(events, 2)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'events/events_list.html', {
        'events': page_obj,
        'query': query,
        'page_obj': page_obj,
    })


def event_detail(request, id):
    event = get_object_or_404(Event, id=id)
    already_booked = False
    if request.user.is_authenticated:
        already_booked = Booking.objects.filter(user=request.user, event=event).exists()
    return render(request, 'events/event_detail.html', {
        'event': event,
        'already_booked': already_booked,
    })


@login_required
def book_event(request, id):
    event = get_object_or_404(Event, id=id)

    if Booking.objects.filter(user=request.user, event=event).exists():
        messages.warning(request, 'You already booked this event!')
        return redirect(f'/event/{id}/')

    if event.available_seats > 0:
        Booking.objects.create(user=request.user, event=event)
        event.available_seats -= 1
        event.save()
        messages.success(request, f'Successfully booked: {event.title}!')
    else:
        messages.error(request, 'Sorry, this event is Sold Out!')

    return redirect('/my-tickets/')


@login_required
def my_tickets(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-booked_at')
    return render(request, 'events/my_tickets.html', {'bookings': bookings})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('/')
        else:
            messages.error(request, 'Invalid username or password!')
    return render(request, 'events/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('/login/')

@login_required
def cancel_booking(request, id):
    event = get_object_or_404(Event, id=id)
    booking = Booking.objects.filter(user=request.user, event=event).first()

    if booking:
        booking.delete()
        event.available_seats += 1
        event.save()
        messages.success(request, f'Booking cancelled: {event.title}')
    else:
        messages.error(request, 'No booking found!')

    return redirect('/my-tickets/')

from django.contrib.auth.models import User

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return redirect('/register/')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken!')
            return redirect('/register/')

        user = User.objects.create_user(username=username, email=email, password=password1)
        login(request, user)
        messages.success(request, f'Welcome, {username}! Account created successfully!')
        return redirect('/')

    return render(request, 'events/register.html')


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .serializers import EventSerializer, BookingSerializer


@api_view(['GET'])
def api_events(request):
    """GET all upcoming events"""
    events = Event.objects.filter(
        date__gte=timezone.now().date()
    ).order_by('date')
    serializer = EventSerializer(events, many=True)
    return Response({
        'count': events.count(),
        'events': serializer.data
    })


@api_view(['GET'])
def api_event_detail(request, id):
    """GET single event by id"""
    event = get_object_or_404(Event, id=id)
    serializer = EventSerializer(event)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_book_event(request, id):
    """POST — book an event"""
    event = get_object_or_404(Event, id=id)

    if Booking.objects.filter(user=request.user, event=event).exists():
        return Response(
            {'error': 'You already booked this event!'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if event.available_seats <= 0:
        return Response(
            {'error': 'Event is fully booked!'},
            status=status.HTTP_400_BAD_REQUEST
        )

    booking = Booking.objects.create(user=request.user, event=event)
    event.available_seats -= 1
    event.save()

    return Response({
        'message': f'Successfully booked: {event.title}',
        'booking_id': booking.id,
        'event': event.title,
        'date': event.date,
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_my_bookings(request):
    """GET current user bookings"""
    bookings = Booking.objects.filter(user=request.user).order_by('-booked_at')
    serializer = BookingSerializer(bookings, many=True)
    return Response({
        'count': bookings.count(),
        'bookings': serializer.data
    })