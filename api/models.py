from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import hashlib
import json

class APIUsageLog(models.Model):
    """Track API usage for billing and monitoring"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    endpoint = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    request_data = models.JSONField(blank=True, null=True)
    response_count = models.IntegerField(default=0)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    used_cache = models.BooleanField(default=False)  # Track if result was cached
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['endpoint', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.endpoint} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class PlacesSearchCache(models.Model):
    """Cache Google Places API results to reduce API costs"""
    cache_key = models.CharField(max_length=255, unique=True, db_index=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    radius_meters = models.IntegerField()
    category = models.CharField(max_length=20)
    place_types = models.JSONField(default=list)
    results = models.JSONField()  # Store the actual results
    result_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    access_count = models.IntegerField(default=1)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cache_key']),
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['created_at']),
        ]
    
    @classmethod
    def generate_cache_key(cls, latitude, longitude, radius_meters, category, place_types):
        """Generate a consistent cache key for search parameters"""
        # Round coordinates to reduce cache misses for very close searches
        lat_rounded = round(float(latitude), 6)  # ~0.1 meter precision
        lon_rounded = round(float(longitude), 6)
        
        # Sort place_types for consistency
        sorted_types = sorted(place_types) if place_types else []
        
        key_data = {
            'lat': lat_rounded,
            'lon': lon_rounded,
            'radius': radius_meters,
            'category': category,
            'types': sorted_types
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @classmethod
    def get_cached_results(cls, latitude, longitude, radius_meters, category, place_types, max_age_hours=2):
        """Get cached results if they exist, aren't too old, and have meaningful data"""
        cache_key = cls.generate_cache_key(latitude, longitude, radius_meters, category, place_types)
        
        try:
            cutoff_time = timezone.now() - timezone.timedelta(hours=max_age_hours)
            cached_result = cls.objects.get(
                cache_key=cache_key,
                created_at__gte=cutoff_time
            )
            
            # Update access tracking
            cached_result.access_count += 1
            cached_result.save(update_fields=['access_count', 'last_accessed'])
            
            # Return results and metadata
            return {
                'results': cached_result.results,
                'has_results': cached_result.result_count > 0,
                'result_count': cached_result.result_count,
                'created_at': cached_result.created_at
            }
            
        except cls.DoesNotExist:
            return None
        
    @classmethod
    def cache_results(cls, latitude, longitude, radius_meters, category, place_types, results):
        """Cache search results"""
        cache_key = cls.generate_cache_key(latitude, longitude, radius_meters, category, place_types)
        
        # Delete old cache entry if it exists
        cls.objects.filter(cache_key=cache_key).delete()
        
        # Create new cache entry
        cls.objects.create(
            cache_key=cache_key,
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            category=category,
            place_types=place_types,
            results=results,
            result_count=len(results)
        )
    
    @classmethod
    def cleanup_old_cache(cls, days=7):
        """Clean up old cache entries"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        deleted_count = cls.objects.filter(created_at__lt=cutoff_date).delete()[0]
        return deleted_count
    
    def __str__(self):
        return f"Cache: {self.latitude},{self.longitude} r={self.radius_meters}m ({self.result_count} results)"
