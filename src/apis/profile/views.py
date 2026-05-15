from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from uuid import UUID
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from typing import Optional
import logging

from src.application.profile.factory import create_profile_use_case
from src.application.profile.dtos import MyUserProfileDTO
from src.domain.profile.exceptions import (
    ProfileNotFoundError,
    ProfileDomainError,
    InvalidProfileUpdateError,
    ProfileAccessDeniedError,
)

logger = logging.getLogger(__name__)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ProfileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, user_id: Optional[str] = None) -> Response:
        """
        Retrieve a profile.
        If user_id is provided, fetch that user's profile (as foreign).
        If not provided, fetch requester's own profile.
        """
        requester_id = request.user.id
        target_user_id = user_id if user_id else requester_id

        try:
            use_case = create_profile_use_case()
            dto = use_case.get_by_user_id(user_id=target_user_id, requester_id=requester_id)
            return Response(dto.to_dict(), status=status.HTTP_200_OK)
        except ProfileNotFoundError:
            return Response(
                {'error': 'Profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ProfileAccessDeniedError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            logger.error("Unexpected error in ProfileDetailView.get: %s", e, exc_info=True)
            return Response(
                {'error': 'Failed to retrieve profile.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request: Request) -> Response:
        """
        Update the requester's own profile.
        Handles both JSON fields AND file uploads (cover_image).
        """
        user_id = request.user.id
        data = request.data

        logger.info(f"🔍 PATCH /profile/ hit by user: {user_id}")  # DEBUG
        logger.info(f"🔍 Request FILES: {request.FILES.keys()}")   # DEBUG
        logger.info(f"🔍 Request DATA keys: {data.keys()}")        # DEBUG

        # Extract text fields from request.data
        update_fields = {
            'bio': data.get('bio'),
            'profession': data.get('profession'),
            'account_type': data.get('account_type'),
            'date_of_birth': data.get('date_of_birth'),
            'gender': data.get('gender'),
            'phone': data.get('phone'),
            'location': data.get('location'),
            'language': data.get('language'),
            'theme': data.get('theme'),
        }

        # ✅ Handle cover_image as REAL FILE upload (like profile_picture)
        cover_image_file = request.FILES.get('cover_image')
        if cover_image_file:
            logger.info(f"🔍 Cover image file received: {cover_image_file.name}")  # DEBUG
            update_fields['cover_image'] = cover_image_file  # Pass File object to use case
        elif data.get('cover_image') == '':
            # User explicitly cleared the image
            update_fields['cover_image'] = None
        # If cover_image is a string URL and no file, keep existing (don't override)

        try:
            use_case = create_profile_use_case()
            dto: MyUserProfileDTO = use_case.update_profile(user_id=user_id, **update_fields)
            
            # ✅ Build absolute URL for cover_image in response (if it's a file field)
            cover_image_url = None
            if hasattr(dto, 'cover_image') and dto.cover_image:
                if isinstance(dto.cover_image, str) and dto.cover_image.startswith(('http://', 'https://')):
                    # Already absolute URL
                    cover_image_url = dto.cover_image
                else:
                    # Relative path → build absolute
                    cover_image_url = request.build_absolute_uri(dto.cover_image)
                    logger.info(f"🔍 Cover image URL: {cover_image_url}")  # DEBUG

            # Prepare response data (merge DTO with absolute URL)
            response_data = dto.to_dict()
            if cover_image_url:
                response_data['cover_image'] = cover_image_url

            return Response(response_data, status=status.HTTP_200_OK)

        except InvalidProfileUpdateError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ProfileNotFoundError:
            return Response(
                {'error': 'Profile not found. Please ensure your profile exists.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ProfileDomainError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error("Unexpected error in ProfileDetailView.patch: %s", e, exc_info=True)
            return Response(
                {'error': 'Failed to update profile.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(ensure_csrf_cookie, name='dispatch')
class ClearNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        user_id = request.user.id
        try:
            use_case = create_profile_use_case()
            dto: MyUserProfileDTO = use_case.clear_unread_notifications(user_id=user_id)
            return Response(dto.to_dict(), status=status.HTTP_200_OK)
        except ProfileNotFoundError:
            return Response(
                {'error': 'Profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ProfileDomainError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error("Unexpected error in ClearNotificationsView: %s", e, exc_info=True)
            return Response(
                {'error': 'Failed to clear notifications.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ToggleProfileDeletionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        user_id = request.user.id
        try:
            use_case = create_profile_use_case()
            dto: MyUserProfileDTO = use_case.toggle_deleted(user_id=user_id)
            return Response(dto.to_dict(), status=status.HTTP_200_OK)
        except ProfileNotFoundError:
            return Response(
                {'error': 'Profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ProfileDomainError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error("Unexpected error in ToggleProfileDeletionView: %s", e, exc_info=True)
            return Response(
                {'error': 'Failed to toggle profile deletion status.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class TopProfilesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        try:
            limit = min(int(request.query_params.get('limit', 10)), 50)
            use_case = create_profile_use_case()
            dtos = use_case.list_top_profiles(requester_id=request.user.id, limit=limit)
            return Response([dto.to_dict() for dto in dtos], status=status.HTTP_200_OK)
        except ProfileDomainError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error("Unexpected error in TopProfilesView: %s", e, exc_info=True)
            return Response(
                {'error': 'Failed to fetch top profiles.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AllProfilesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        try:
            limit = min(int(request.query_params.get('limit', 50)), 100)
            offset = int(request.query_params.get('offset', 0))
            use_case = create_profile_use_case()
            dtos = use_case.list_all_profiles(
                requester_id=request.user.id,
                limit=limit,
                offset=offset
            )
            return Response([dto.to_dict() for dto in dtos], status=status.HTTP_200_OK)
        except ProfileDomainError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error("Unexpected error in AllProfilesView: %s", e, exc_info=True)
            return Response(
                {'error': 'Failed to fetch profiles.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )