from django.apps import AppConfig

class CatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # можно убрать для старых версий Django
    name = 'catalog'
