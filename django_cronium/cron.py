from django.conf import settings
from django.core.mail import send_mail

from django_cronium import CronJobBase, Schedule
from django_cronium.models import CronJobLog
from django_cronium.management.commands.runcrons import get_class


class FailedRunsNotificationCronJob(CronJobBase):
    """
        Send email if cron failed to run X times in a row
    """
    RUN_EVERY_MINS = 30

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'django_cronium.FailedRunsNotificationCronJob'

    def do(self):

        CRONS_TO_CHECK = map(lambda x: get_class(x), settings.CRON_CLASSES)
        EMAILS = [admin[1] for admin in settings.ADMINS]

        try:
            FAILED_RUNS_CRONJOB_EMAIL_PREFIX = settings.FAILED_RUNS_CRONJOB_EMAIL_PREFIX
        except:
            FAILED_RUNS_CRONJOB_EMAIL_PREFIX = ''

        for cron in CRONS_TO_CHECK:

            try:
                min_failures = cron.MIN_NUM_FAILURES
            except AttributeError:
                min_failures = 10

            failures = 0

            jobs = CronJobLog.objects.filter(code=cron.code).order_by('-end_time')[:min_failures]

            message = ''

            for job in jobs:
                if not job.is_success:
                    failures += 1
                    message += 'Job ran at %s : \n\n %s \n\n' % (job.start_time, job.message)

            if failures == min_failures:

                send_mail(
                    '%s%s failed %s times in a row!' % (FAILED_RUNS_CRONJOB_EMAIL_PREFIX, cron.code, \
                        min_failures), message,
                    settings.DEFAULT_FROM_EMAIL, EMAILS
                )
