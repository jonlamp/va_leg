from django.core.management.base import BaseCommand, CommandError
from core.models import Legislator, Session
from core.management.commands._private import update_legislators, update_bills

class Command(BaseCommand):
    help = 'Collects the data needed for website'
    def add_arguments(self, parser) -> None:
        parser.add_argument('session',type=str)
        parser.add_argument(
            '--only',
            help='Only updates the chosen data set',
            default='all',
            const='all',
            nargs='?',
            choices=['bills','legislators','all']
        )
    def handle(self,*args,**options):
        if 'legislators' in options['only'] or 'all' in options['only']:
            new_reps = update_legislators(options['session'])
            self.stdout.write(self.style.SUCCESS(f'Added {new_reps["new_legislators"]} new legislators!'))
        if 'bills' in options['only'] or 'all' in options['only']:
            new_bills = update_bills(options['session'])
            self.stdout.write(self.style.SUCCESS(f'Added {new_bills["new_bills"]} new bills!'))
    
