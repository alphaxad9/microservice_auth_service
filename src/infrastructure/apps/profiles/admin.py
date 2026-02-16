from django.contrib import admin
from django.utils.html import format_html
from .models import ORMProfile


@admin.register(ORMProfile)
class ORMProfileAdmin(admin.ModelAdmin):
    # === Display ===
    list_display = (
        "user_id",
        "account_type_display",
        "username_preview",
        "email_preview",
        "followers_count",
        "following_count",
        "last_seen_ago",
        "is_deleted",
        "cover_image_tag",
    )
    list_display_links = ("user_id", "username_preview")
    
    # === Filtering ===
    list_filter = (
        "is_deleted",
        "account_type",
        "gender",
        "language",
        "theme",
        "profession",
        "location",
        "created_at",
    )
    
    # === Search ===
    # Note: UUID search is supported; you can also search related user info if you join
    search_fields = ("user_id", "bio", "profession", "phone", "location")

    # === Field Organization in Form ===
    fieldsets = (
        (None, {
            "fields": ("user_id", "is_deleted")
        }),
        ("Social Metrics", {
            "fields": ("followers_count", "following_count", "unread_notifications_count"),
            "classes": ("collapse",),
        }),
        ("Status & Timestamps", {
            "fields": ("last_seen_at", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
        ("Profile Details", {
            "fields": ("bio", "profession", "account_type", "date_of_birth", "gender", "phone", "location"),
        }),
        ("Preferences", {
            "fields": ("language", "theme"),
        }),
        ("Media", {
            "fields": ("cover_image", "cover_image_tag"),
            "classes": ("collapse",),
        }),
    )

    # === Read-only fields ===
    readonly_fields = (
        "user_id",
        "created_at",
        "updated_at",
        "last_seen_ago",
        "cover_image_tag",
        "username_preview",
        "email_preview",
    )

    # === Pagination & Performance ===
    list_per_page = 25
    show_full_result_count = False  # improves performance on large tables

    # === Custom Methods for Display ===

    def account_type_display(self, obj):
        return obj.get_account_type_display()
    account_type_display.short_description = "Account Type"
    account_type_display.admin_order_field = "account_type"

    def last_seen_ago(self, obj):
        from django.utils.timesince import timesince
        if obj.last_seen_at:
            return timesince(obj.last_seen_at) + " ago"
        return "Never"
    last_seen_ago.short_description = "Last Seen"

    def cover_image_tag(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-height: 60px; border-radius: 4px;" />',
                obj.cover_image
            )
        return "No image"
    cover_image_tag.short_description = "Cover Preview"

    def username_preview(self, obj):
        # Optional: Fetch real username if you have a user lookup
        # For now, return placeholder or integrate with User service if needed
        return "—"
    username_preview.short_description = "Username"

    def email_preview(self, obj):
        # Same as above — could be enriched via service lookup
        return "—"
    email_preview.short_description = "Email"

    # === Prevent creation/deletion if needed ===
    # def has_add_permission(self, request):
    #     return False  # Profiles are created by domain logic, not manually

    # def has_delete_permission(self, request, obj=None):
    #     return False  # Soft-delete only