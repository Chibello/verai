from django.apps import AppConfig


class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'
    def ready(self):
        import myapp.signals  # Import the signals


#class YourAppConfig(AppConfig):
 #   name = 'yourapp'

  #  def ready(self):
   #     import yourapp.signals  # Import the signals
