from django.core.management.base import BaseCommand, CommandError
from core.models import Legislator, Session
from core.management.commands._private import update_legislators, update_bills,update_summaries

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
            choices=['bills','legislators','all', 'summaries']
        )
    def handle(self,*args,**options):
        if 'legislators' in options['only'] or 'all' in options['only']:
            new_reps = update_legislators(options['session'])
            self.stdout.write(self.style.SUCCESS(f'Added {new_reps["count"]} new legislators!'))
        if 'bills' in options['only'] or 'all' in options['only']:
            new_bills = update_bills(options['session'])
            self.stdout.write(self.style.SUCCESS(f'Added {new_bills["count"]} new bills!'))
        if 'summaries' in options['only'] or 'all' in options['only']:
            new_summaries = update_summaries(options['session'])
            self.stdout.write(self.style.SUCCESS(f'Added {new_summaries["count"]} new bills!'))
