from django.urls import path
from src.apis.profile.views import (
    ProfileDetailView,
    ClearNotificationsView,
    ToggleProfileDeletionView,
    TopProfilesView,
    AllProfilesView,
)

urlpatterns = [
    # GET /api/profile/ — get own profile
    # GET /api/profile/<uuid:user_id>/ — get foreign profile
    # PATCH /api/profile/ — update own profile
    path('', ProfileDetailView.as_view(), name='profile-detail'),
    path('<uuid:user_id>/', ProfileDetailView.as_view(), name='foreign-profile-detail'),

    # POST /api/profile/clear-notifications/
    path('clear-notifications/', ClearNotificationsView.as_view(), name='clear-notifications'),

    # POST /api/profile/toggle-deletion/
    path('toggle-deletion/', ToggleProfileDeletionView.as_view(), name='toggle-profile-deletion'),

    # GET /api/profile/top/?limit=10
    path('top/', TopProfilesView.as_view(), name='top-profiles'),

    # GET /api/profile/all/?limit=50&offset=0
    path('all/', AllProfilesView.as_view(), name='all-profiles'),
]