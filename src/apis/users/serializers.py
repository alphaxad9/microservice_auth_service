# src/infrastructure/apps/users/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from src.infrastructure.apps.users.models import ORMUser
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    identifier = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('username', None)
        self.fields.pop('email', None)

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        password = attrs.get("password")

        user = (
            User.objects.filter(email__iexact=identifier).first()
            or User.objects.filter(username__iexact=identifier).first()
        )

        if not user:
            raise serializers.ValidationError({"identifier": "No user found with this email or username."})

        auth_user = authenticate(username=user.email, password=password)
        if not auth_user:
            raise serializers.ValidationError({"password": "Incorrect password."})

        # Use parent validation (generates tokens)
        data = super().validate({User.USERNAME_FIELD: getattr(user, User.USERNAME_FIELD), "password": password})

        # ✅ CORRECT: Use .url if image exists
        data["user"] = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "profile_picture": user.profile_picture.url if user.profile_picture else None,
        }

        self.user = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ORMUser
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'profile_picture')
        extra_kwargs = {
            'id': {'read_only': True},
            'email': {'read_only': True},
            'username': {'read_only': True},
            # ⚠️ Do NOT validate profile_picture as URL
        }

    # ✅ REMOVE URL VALIDATION — it's a file upload
    # def validate_profile_picture(self, value):
    #     ...  # ← DELETE THIS METHOD

    def update(self, instance, validated_data):
        # Only update non-file fields here
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)

        # Handle profile_picture ONLY if it's a file (not a string)
        # This will work if view passes request.FILES['profile_picture']
        if 'profile_picture' in validated_data:
            instance.profile_picture = validated_data['profile_picture']

        instance.save()
        return instance


class UserCreationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = ORMUser
        fields = ('id', 'email', 'username', 'password', 'password2', 'first_name', 'last_name', 'profile_picture')
        extra_kwargs = {
            'id': {'read_only': True},
            'password': {'write_only': True},
            'password2': {'write_only': True},
            # ⚠️ profile_picture should NOT be validated as URL
        }

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': 'Passwords must match.'})
        if len(data['password']) < 8:
            raise serializers.ValidationError({'password': 'Password must be at least 8 characters.'})
        if not any(c.isupper() for c in data['password']):
            raise serializers.ValidationError({'password': 'Password must contain at least one uppercase letter.'})
        if not any(c.isdigit() for c in data['password']):
            raise serializers.ValidationError({'password': 'Password must contain at least one digit.'})
        if not any(c in '!@#$%^&*()' for c in data['password']):
            raise serializers.ValidationError({'password': 'Password must contain at least one special character.'})
        if ORMUser.objects.filter(email__iexact=data['email']).exists():
            raise serializers.ValidationError({'email': 'This email is already in use.'})
        if ORMUser.objects.filter(username__iexact=data['username']).exists():
            raise serializers.ValidationError({'username': 'This username is already in use.'})
        return data

    # ✅ REMOVE URL VALIDATION — profile_picture is a file
    # def validate_profile_picture(self, value):
    #     ...  # ← DELETE THIS METHOD

    def create(self, validated_data):
        validated_data.pop('password2')
        
        # ⚠️ DO NOT pass profile_picture as string!
        # If it's a file (from request.FILES), Django handles it.
        # If it's a string (from JSON), it will break.
        user = ORMUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            profile_picture=validated_data.get('profile_picture', ''),  # ← This is OK *only if* it's a file
        )
        return user



# --- NEW SERIALIZER ---
class ChangeEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user

        # Check password
        if not user.check_password(attrs['password']):
            raise serializers.ValidationError({"password": "Incorrect password."})

        # Ensure new email is not taken
        if User.objects.filter(email__iexact=attrs['new_email']).exclude(id=user.id).exists():
            raise serializers.ValidationError({"new_email": "This email is already in use."})

        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.email = self.validated_data['new_email']
        user.save()
        return user




# --- NEW SERIALIZER ---
class ChangeUsernameSerializer(serializers.Serializer):
    new_username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user

        if not user.check_password(attrs['password']):
            raise serializers.ValidationError({"password": "Incorrect password."})

        if User.objects.filter(username__iexact=attrs['new_username']).exclude(id=user.id).exists():
            raise serializers.ValidationError({"new_username": "This username is already taken."})

        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.username = self.validated_data['new_username']
        user.save()
        return user




# --- NEW SERIALIZER ---
class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user

        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError({"current_password": "Incorrect password."})

        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password2": "Passwords must match."})

        new = attrs['new_password']
        if len(new) < 8:
            raise serializers.ValidationError({"new_password": "Password must be at least 8 characters."})
        if not any(c.isupper() for c in new):
            raise serializers.ValidationError({"new_password": "Must contain at least one uppercase letter."})
        if not any(c.isdigit() for c in new):
            raise serializers.ValidationError({"new_password": "Must contain at least one number."})
        if not any(c in '!@#$%^&*()' for c in new):
            raise serializers.ValidationError({"new_password": "Must contain at least one special character."})

        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user



# --- NEW SERIALIZER ---
class SoftDeleteUserSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user

        if not user.check_password(attrs['password']):
            raise serializers.ValidationError({"password": "Incorrect password."})

        return attrs
