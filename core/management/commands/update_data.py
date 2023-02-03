from django.core.management.base import BaseCommand, CommandError
from core.models import Legislator, Session
from django.core.mail import send_mail
from django.conf import settings
import datetime as dt
import re
from core.management.commands._private import update_legislators, update_bills,update_summaries, update_actions, update_patrons

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
        parser.add_argument(
            '--email',
            help='Sends an email to the specified address',
            type=str
        )
    def handle(self,*args,**options):
        log = ""
        if 'legislators' in options['only'] or 'all' in options['only']:
            new_reps = update_legislators(options['session'])
            message = f'Added {new_reps["count"]} new legislators!'
            log += message + "\n"
            self.stdout.write(self.style.SUCCESS(message))
        if 'bills' in options['only'] or 'all' in options['only']:
            new_bills = update_bills(options['session'])
            message = f'Added {new_bills["count"]} new bills!'
            log += message + "\n"
            self.stdout.write(self.style.SUCCESS(message))
            new_summaries = update_summaries(options['session'])
            message = f'Added {new_summaries["count"]} new summaries!'
            new_actions = update_actions(options['session'])
            message=f'Added {new_actions["count"]} new actions!'
            log += message + "\n"
            self.stdout.write(self.style.SUCCESS(message))
            new_patrons = update_patrons(options['session'])
            f'Added {new_patrons["count"]} new patrons!'
            log += message + "\n"
            self.stdout.write(self.style.SUCCESS(message))
        if 'email' in options.keys():
            #do a little check to make sure the email is valid
            regex=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
            if not re.fullmatch(regex,options['email']):
                self.stdout.write(self.style.ERROR('I think you forgot something in your email address...'))
            else:
                now = dt.datetime.now().strftime('%m/%d/%Y %H:%M:%S')
                subject = "Scraper " + now
                body = "Update finished running at " + now + "\n\n" + log
                email_from = settings.EMAIL_HOST_USER
                email_to = options['email']
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=email_from,
                    recipient_list=[email_to]
                )
                self.stdout.write(self.style.SUCCESS(f'Message sent to {options["email"]}'))
