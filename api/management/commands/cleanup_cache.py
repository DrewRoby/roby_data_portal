from django.core.management.base import BaseCommand
from api.models import PlacesSearchCache

class Command(BaseCommand):
    help = 'Clean up old cached search results'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Delete cache entries older than this many days (default: 7)'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        deleted_count = PlacesSearchCache.cleanup_old_cache(days=days)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {deleted_count} old cache entries (older than {days} days)')
        )