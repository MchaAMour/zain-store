from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = "Create or update the non-admin customer account used in the demo."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="demo.customer")
        parser.add_argument("--password", required=True, help="A local/demo-only password; it is not printed or stored in source control.")

    def handle(self, *args, **options):
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(username=options["username"])
        user.set_password(options["password"])
        user.is_staff = False
        user.is_superuser = False
        user.save()
        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} demo customer '{user.username}'."))
