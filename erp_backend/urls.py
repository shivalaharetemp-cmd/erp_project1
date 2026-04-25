from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('masters/', include('masters.urls')),
    path('vehicles/', include('vehicles.urls')),
    path('freight/', include('freight.urls')),
    path('sales/', include('sales.urls')),
    path('inventory/', include('inventory.urls')),
    path('accounts/', include('accounts.urls')),
    path('audit/', include('audit.urls')),
]

admin.site.site_header = 'ERP Admin'
admin.site.site_title = 'ERP Administration'
admin.site.index_title = 'Dashboard'
