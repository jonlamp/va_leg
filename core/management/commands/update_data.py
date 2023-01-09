from django.core.management.base import BaseCommand, CommandError
from core.models import Legislator, Session
from _private import update_legislators

class Command(BaseCommand):
    help = 'Collects the data needed for website'
    def handle(self,*args,**options):
        new_reps = update_legislators()
        self.stdout.write(self.style.SUCCESS(f'Added {new_reps} new legislators!'))
    
