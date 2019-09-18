from django.contrib import admin
from rbac import models
from django.conf import global_settings


class PermissionConfig(admin.ModelAdmin):
    list_display = ['id', 'url', 'title', 'menu']
    list_editable = ['url', 'title', 'menu']


admin.site.register(models.Permission, PermissionConfig)
admin.site.register(models.Role)
# admin.site.register(models.User)
admin.site.register(models.Menu)
