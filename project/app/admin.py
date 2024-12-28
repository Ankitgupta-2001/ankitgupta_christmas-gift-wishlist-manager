from django.contrib import admin
from .models import UserProfile, WishlistGroup, GroupMember, WishlistItem, Contribution, Product, UserBudget, Notification, Follow, Message

# Register UserProfile to the admin interface
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'dob', 'gender', 'bio')
    search_fields = ('user__username', 'full_name')
    list_filter = ('gender',)

# Register WishlistGroup to the admin interface
@admin.register(WishlistGroup)
class WishlistGroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'group_type', 'created_at', 'budget_limit', 'submission_deadline')
    search_fields = ('title', 'description')
    list_filter = ('group_type', 'created_at')
    readonly_fields = ('code',)  # Code is auto-generated, so it should be read-only

# Register GroupMember to the admin interface
@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'role', 'joined_at')
    search_fields = ('user__username', 'group__title')
    list_filter = ('role',)

# Register WishlistItem to the admin interface
@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'submitted_by', 'price', 'is_approved', 'submitted_at')
    search_fields = ('name', 'description', 'submitted_by__username')
    list_filter = ('is_approved', 'group__title')

# Register Contribution to the admin interface
@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('user', 'wishlist_item', 'amount', 'created_at')
    search_fields = ('user__username', 'wishlist_item__name')
    list_filter = ('created_at',)

# Register Product to the admin interface
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category')
    search_fields = ('name', 'category')
    list_filter = ('category',)

# Register UserBudget to the admin interface
@admin.register(UserBudget)
class UserBudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'monthly_budget', 'spending_cap')
    search_fields = ('user__username',)

# Register Notification to the admin interface
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    search_fields = ('user__username', 'message')
    list_filter = ('is_read', 'created_at')

# Register Follow to the admin interface
@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    search_fields = ('follower__username', 'following__username')
    list_filter = ('created_at',)

# Register Message to the admin interface
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'group', 'content', 'timestamp')
    search_fields = ('sender__username', 'group__title', 'content')
    list_filter = ('timestamp',)

from django.contrib import admin
from .models import GiftSelection

class GiftSelectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'wishlist_item', 'selected_at')  # Fields to display in the list view
    list_filter = ('user', 'selected_at')  # Filters to add on the right sidebar
    search_fields = ('user__username', 'wishlist_item__name')  # Fields to search in the admin search bar
    ordering = ('-selected_at',)  # Ordering by the selected_at field (newest first)
    list_per_page = 20  # How many items to display per page in the list view

admin.site.register(GiftSelection, GiftSelectionAdmin)
