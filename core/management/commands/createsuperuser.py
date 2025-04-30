from django.contrib.auth.management.commands import createsuperuser

class Command(createsuperuser.Command):
    def handle(self, *args, **options):
        options['username'] = input('Username: ')
        rut = input('RUT: ')
        super().handle(*args, **options)
        user = self.UserModel._default_manager.get(username=options['username'])
        user.rut = rut
        user.save()