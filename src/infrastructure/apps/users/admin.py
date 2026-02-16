from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe

from src.infrastructure.apps.users.models import ORMUser


@admin.register(ORMUser)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for the custom ORMUser model."""

    # Fields to display in the list view
    list_display = (
        'id',
        'email',
        'username',
        'first_name',
        'last_name',
        'profile_picture_preview',  # 👈 Add preview to list view (optional)
        'is_active',
        'is_deleted',
        'is_staff',
        'created_at',
    )
    
    # Fields that can be clicked to edit the user
    list_display_links = ('id', 'email', 'username')
    
    # Filters, search, etc. (unchanged)
    list_filter = (
        'is_active',
        'is_deleted',
        'is_staff',
        'is_superuser',
        'created_at',
    )
    
    search_fields = (
        'id',
        'email',
        'username',
        'first_name',
        'last_name',
    )
    
    list_editable = ('is_active', 'is_deleted')
    list_per_page = 25
    date_hierarchy = 'created_at'

    # ➕ Add profile picture preview method
    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return mark_safe(
                f'<img src="{obj.profile_picture.url}" style="width: 45px; height: 45px; object-fit: cover; border-radius: 50%;" />'
            )
        return "—"
    
    profile_picture_preview.short_description = "Profile Picture"  # Column header
    profile_picture_preview.admin_order_field = 'profile_picture'  # Optional: allow sorting

    # Fieldsets: include the preview in detail view
    fieldsets = (
        (None, {'fields': ('id', 'email', 'username', 'password')}),
        (_('Personal info'), {
            'fields': (
                'first_name',
                'last_name',
                'profile_picture',
                'profile_picture_preview',  # 👈 Show preview in detail form
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_deleted',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            ),
        }),
        (_('Important dates'), {
            'fields': (
                'last_login',
                'created_at',
                'updated_at',
            )
        }),
    )
    
    # Creation form (no image preview needed here)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'password1',
                'password2',
                'first_name',
                'last_name',
            ),
        }),
    )
    
    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
        'last_login',
        'profile_picture_preview',  # 👈 Must be in readonly_fields to appear in fieldsets
    )
    
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request)
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly_fields.extend(['id', 'created_at'])
        return readonly_fields


# Admin site branding
admin.site.site_header = "User Management Administration"
admin.site.site_title = "User Management Admin Portal"
admin.site.index_title = "Welcome to User Management Admin"