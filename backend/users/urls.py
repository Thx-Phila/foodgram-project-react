from django.urls import include, path
from recipes.views import FollowGETAPIView, FollowViewSet
from rest_framework.routers import DefaultRouter

app_name = 'users'

router_v1 = DefaultRouter()

router_v1.register('users', FollowViewSet, basename='users')


urlpatterns = [
    path('users/subscriptions/',
         FollowGETAPIView.as_view(),
         name='subscriptions'),
    path('', include('djoser.urls')),
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
