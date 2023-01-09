from django.core.management.base import BaseCommand, CommandError
from core.models import Legislator, Session
from core.management.commands._private import update_legislators

class Command(BaseCommand):
    help = 'Collects the data needed for website'
    def add_arguments(self, parser) -> None:
        parser.add_argument('session',type=str)
    def handle(self,*args,**options):
        new_reps = update_legislators(options['session'])
        if new_reps['new_legislators'] > 0:
            self.stdout.write(self.style.SUCCESS(f'Added {new_reps["new_legislators"]} new legislators!'))
        else:
            self.stdout.write(str(new_reps['csv_legislators']),ending='')
    
