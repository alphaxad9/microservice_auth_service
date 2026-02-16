# src/infrastructure/apps/users/urls.py
from django.urls import path
from .views import CsrfTokenView, CustomTokenObtainPairView, UserCreationView, UserProfileView, UserLogoutView, CustomTokenRefreshView, UserDeletionView,UserUpdateProfileView,  UserSoftDeleteView, UserByIdView,UserListView,  ChangeEmailView, ChangeUsernameView, ChangePasswordView, PublicKeyView

urlpatterns = [
    path('csrf/', CsrfTokenView.as_view(), name='csrf_token'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('register/', UserCreationView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('delete/', UserDeletionView.as_view(), name='delete_user'),  

    path('profile/update/', UserUpdateProfileView.as_view(), name='update_profile'),


    path('users/<uuid:user_id>/', UserByIdView.as_view(), name='user_by_id'),
    path('users/', UserListView.as_view(), name='user_list'),
    
    # New user update routes
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('change-username/', ChangeUsernameView.as_view(), name='change_username'),
    path('change-email/', ChangeEmailView.as_view(), name='change_email'),

    # Updated soft delete (password required)
    path('soft-delete/', UserSoftDeleteView.as_view(), name='soft_delete_user'),
    path("public_key/", PublicKeyView.as_view(), name="public_key"), 
]