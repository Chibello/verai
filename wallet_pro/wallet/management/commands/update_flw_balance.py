from django.core.management.base import BaseCommand
from wallet.utils import update_flutterwave_wallet_balance

class Command(BaseCommand):
    help = 'Update Flutterwave wallet balances'

    def handle(self, *args, **kwargs):
        success = update_flutterwave_wallet_balance()
        if success:
            self.stdout.write(self.style.SUCCESS('Flutterwave wallet balances updated'))
        else:
            self.stdout.write(self.style.ERROR('Failed to update FLW balances'))
