
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
import notifications.urls
urlpatterns = [
    path('admin/', admin.site.urls),
    path('password-reset/',include('password_reset.urls')),
    path('userprofile/',include('userprofile.urls')),
    path('comment/', include('comment.urls', namespace='comment')),
    path('inbox/notifications/',include(notifications.urls,namespace='notifications')),
    path('notice/',include('notice.urls',namespace='notice')),
    path('accounts/', include('allauth.urls')),
    path('', include('article.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)