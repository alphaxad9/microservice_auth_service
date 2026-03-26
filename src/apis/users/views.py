# src/infrastructure/apps/users/views.py
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated, AllowAny
from src.infrastructure.permissions.internal_service import IsInternalService
from uuid import UUID
from datetime import timedelta
from django.contrib.auth.signals import user_logged_in
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import UserCreationSerializer, UserProfileSerializer, CustomTokenObtainPairSerializer, ChangeEmailSerializer, ChangeUsernameSerializer, SoftDeleteUserSerializer,ChangePasswordSerializer
from django.contrib.auth import logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.conf import settings
import logging
from datetime import timedelta
logger = logging.getLogger(__name__)
from src.application.user.factory import create_user_use_case
from django.http import HttpResponse



@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request):
        return Response({'csrfToken': get_token(request)}, status=status.HTTP_200_OK)
    

class PublicKeyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        public_key_pem = settings.SIMPLE_JWT['VERIFYING_KEY']
        return HttpResponse(public_key_pem, content_type='text/plain')


@method_decorator(ensure_csrf_cookie, name='dispatch')
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        serializer = UserProfileSerializer(request.user)
        return Response({'user': serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request: Request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'user': UserProfileSerializer(user).data}, status=status.HTTP_200_OK)
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        tokens = serializer.validated_data

        # 🔔 Manually trigger the signal here
        user_logged_in.send(sender=user.__class__, request=request, user=user)
        try:
            user_use_case = create_user_use_case()
            user_use_case.log_user_in(
                user_id=user.id,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            logger.info(f"User login event published for user: {user.id}")
        except Exception as e:
            logger.error(f"Failed to publish user login event: {str(e)}")

        response_data = {
            'message': f'{user.username} logged in successfully',
            'user': tokens['user'],
            'access': tokens['access'],
            'refresh': tokens['refresh']
        }

        response = Response(response_data, status=status.HTTP_200_OK)
        response.set_cookie(
            key='access',
            value=tokens['access'],
            httponly=True,
            samesite='Strict',
            secure=False,
            max_age=timedelta(minutes=5).total_seconds()
        )
        response.set_cookie(
            key='refresh',
            value=tokens['refresh'],
            httponly=True,
            samesite='Strict',
            secure=False,
            max_age=timedelta(days=1).total_seconds()
        )

        return response


    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'unknown'


@method_decorator(ensure_csrf_cookie, name='dispatch')
class UserCreationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request):
        serializer = UserCreationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()

                try:
                    user_use_case = create_user_use_case()
                    user_dto = user_use_case.publish_user_created_event(user.id)
                    logger.info(f"User creation event published for user: {user.id}")
                except Exception as e:
                    logger.error(f"Failed to publish user creation event: {str(e)}")
                    
                refresh = RefreshToken.for_user(user)
                access = str(refresh.access_token)
                user_data = {
                    'id': str(user.id),
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'profile_picture': user.profile_picture or ''
                }

                response_data = {
                    'message': 'User created and logged in successfully',
                    'user': user_data,
                    'access': access,
                    'refresh': str(refresh)
                }

                response = Response(response_data, status=status.HTTP_201_CREATED)
                response.set_cookie(
                    key='access',  # Match JWTCookieAuthentication default
                    value=access,
                    httponly=True,
                    samesite='Strict',
                    secure=False,  # False for dev
                    max_age=timedelta(minutes=5).total_seconds()
                )
                response.set_cookie(
                    key='refresh',  # Match JWTCookieAuthentication default
                    value=str(refresh),
                    httponly=True,
                    samesite='Strict',
                    secure=False,
                    max_age=timedelta(days=1).total_seconds()
                )
                
                return response
            except Exception as e:
                logger.error(f"Error creating user: {str(e)}")
                return Response({'errors': {'non_field_errors': [str(e)]}}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    



@method_decorator(ensure_csrf_cookie, name='dispatch')
class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        try:
            refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
            if not refresh_token:
                return Response({'message': 'Refresh token cookie required'}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()

            logger.info(f"Logout user: id={request.user.id}, email={request.user.email}, username={request.user.username}, token_jti={token['jti']}")
            
            # 🔥 TEMPORARY FIX: Convert UUID to string for the method call
            try:
                user_use_case = create_user_use_case()
                user_use_case.log_user_out(
                    user_id=request.user.id,  # Keep as string for now
                    ip_address=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                logger.info(f"User logout event published for user: {request.user.id}")
            except Exception as e:
                logger.error(f"Failed to publish user logout event: {str(e)}")
                # Don't fail logout if event publishing fails

            logout(request)

            response = Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'], samesite='Strict')
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'], samesite='Strict')
            return response
        except TokenError as e:
            logger.error(f"Logout error: Invalid refresh token - {str(e)}")
            return Response({'message': 'Invalid or expired refresh token'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'unknown'
    



@method_decorator(ensure_csrf_cookie, name='dispatch')
class UserUpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request):
        try:
            user = request.user

            first_name = request.data.get("first_name")
            last_name = request.data.get("last_name")
            profile_picture = request.FILES.get("profile_picture")

            if first_name:
                user.first_name = first_name

            if last_name:
                user.last_name = last_name

            if profile_picture:
                user.profile_picture = profile_picture

            user.save()

            return Response({
                "message": "Profile updated successfully",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "profile_picture": user.profile_picture.url if user.profile_picture else None
                }
            }, status=200)

        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return Response({"error": "Failed to update profile"}, status=500)


class UserByIdView(APIView):
    # Change this line:
    # permission_classes = [IsAuthenticated]
    # To this:
    permission_classes = [IsInternalService]  # Only internal services can access

    def get(self, request: Request, user_id: UUID):
        """
        Get user by ID — INTERNAL USE ONLY (e.g., wallet_service fetching owner info)
        """
        try:
            user_use_case = create_user_use_case()
            user_dto = user_use_case.get_by_id(user_id)
           
            if not user_dto:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
           
            return Response({'user': user_dto.to_dict()}, status=status.HTTP_200_OK)
           
        except ValueError:
            return Response({'error': 'Invalid user ID format'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            return Response({'error': 'Failed to retrieve user'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



































































@method_decorator(ensure_csrf_cookie, name='dispatch')
class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        """
        List all users with pagination
        Query parameters: ?limit=100&offset=0&include_deleted=false
        """
        try:
            # Get query parameters with defaults
            limit = int(request.GET.get('limit', 100))
            offset = int(request.GET.get('offset', 0))
            include_deleted = request.GET.get('include_deleted', 'false').lower() == 'true'
            
            user_use_case = create_user_use_case()
            users = user_use_case.list_all_users(
                limit=limit,
                offset=offset,
                include_deleted=include_deleted
            )
            
            users_data = [user.to_dict() for user in users]
            return Response({
                'users': users_data,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'total': len(users_data)
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError:
            return Response({'error': 'Invalid limit or offset parameter'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}")
            return Response({'error': 'Failed to list users'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@method_decorator(ensure_csrf_cookie, name='dispatch')
class UserDeletionView(APIView):
    permission_classes = [IsAuthenticated]  # Must be logged in to delete

    def delete(self, request: Request):
        try:
            user = request.user

            # Optional: Blacklist refresh token if present
            refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except TokenError:
                    logger.warning(f"User deletion: refresh token invalid for user {user.id}")

            # Perform deletion
            user_id, user_email, user_username = user.id, user.email, user.username
            user.delete()

            # Log deletion
            logger.info(f"Deleted user: id={user_id}, email={user_email}, username={user_username}")

            # Prepare response
            response = Response({'message': 'User account deleted successfully'}, status=status.HTTP_200_OK)

            # Remove cookies
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'], samesite='Strict')
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'], samesite='Strict')

            return response

        except Exception as e:
            logger.error(f"User deletion error: {str(e)}")
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)





@method_decorator(ensure_csrf_cookie, name='dispatch')
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if not refresh_token:
            return Response({'message': 'Refresh token cookie required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            access_token = str(token.access_token)
            data = {'access': access_token}
            if settings.SIMPLE_JWT['ROTATE_REFRESH_TOKENS']:
                token.set_jti()
                token.set_exp()
                data['refresh'] = str(token)

            response = Response({
                'message': 'Token refreshed successfully',
                'access': data['access'],
                'refresh': data.get('refresh', refresh_token)
            }, status=status.HTTP_200_OK)
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                value=data['access'],
                httponly=True,
                samesite='Strict',
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                max_age=timedelta(minutes=5).total_seconds()
            )
            if 'refresh' in data:
                response.set_cookie(
                    key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
                    value=data['refresh'],
                    httponly=True,
                    samesite='Strict',
                    secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                    max_age=timedelta(days=1).total_seconds()
                )

            return response
        except TokenError as e:
            logger.error(f"Refresh error: Invalid refresh token - {str(e)}")
            return Response({'message': 'Invalid or expired refresh token'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Refresh error: {str(e)}")
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        




class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response({
            "message": "Password updated successfully"
        }, status=status.HTTP_200_OK)


class ChangeUsernameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = ChangeUsernameSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        return Response({
            "message": "Username updated successfully",
            "username": user.username
        }, status=status.HTTP_200_OK)

class ChangeEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = ChangeEmailSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        return Response({
            "message": "Email updated successfully",
            "email": user.email
        }, status=status.HTTP_200_OK)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class UserSoftDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = SoftDeleteUserSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            user_use_case = create_user_use_case()
            user_dto = user_use_case.soft_delete_user(
                user_id=request.user.id
            )

            logout(request)

            response = Response({
                'message': 'User account soft deleted successfully',
                'user': user_dto.to_dict()
            }, status=status.HTTP_200_OK)

            response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'], samesite='Strict')
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'], samesite='Strict')
            return response

        except Exception as e:
            logger.error(f"Soft delete error: {str(e)}")
            return Response({'error': 'Failed to delete user account'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

