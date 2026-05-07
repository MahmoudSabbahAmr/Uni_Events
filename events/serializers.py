
from rest_framework import serializers
from .models import Event, Booking


class EventSerializer(serializers.ModelSerializer):
    seats_remaining = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'category',
            'location', 'date', 'time',
            'total_seats', 'available_seats',
            'seats_remaining', 'is_available',
            'created_at'
        ]

    def get_seats_remaining(self, obj):
        return obj.available_seats

    def get_is_available(self, obj):
        return obj.available_seats > 0


class BookingSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'username', 'event', 'event_title', 'booked_at']