from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
import string

# Helper function to generate a random group code
def generate_group_code():
    length = 10
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# User Profile
class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, blank=True)  # Full Name
    dob = models.DateField(null=True, blank=True)  # Date of Birth
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)  # Gender
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)

    def __str__(self):
        return self.user.username

# Signal to create or update UserProfile when User is created/updated
@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    # Ensure that a UserProfile is created only if it doesn't exist
    if created:
        UserProfile.objects.get_or_create(user=instance)  

# Wishlist Group
class WishlistGroup(models.Model):
    GROUP_TYPE_CHOICES = [
        ('anonymous', 'Anonymous'),
        ('surprise', 'Surprise Gift'),
    ]

    # Group fields
    title = models.CharField(max_length=255)
    description = models.TextField()
    code = models.CharField(max_length=10, unique=True, default=generate_group_code)  # Unique group code
    group_type = models.CharField(
        max_length=20, 
        choices=GROUP_TYPE_CHOICES, 
        default='anonymous'
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_groups")
    created_at = models.DateTimeField(auto_now_add=True)
    is_launched = models.BooleanField(default=False)

    # Budget limit for the group
    budget_limit = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    null=True,
    blank=True,
    default=None,  # Use None for "unlimited"
)

    # Add the submission deadline
    submission_deadline = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    def has_user_selected_gift(self, user):
        return GiftSelection.objects.filter(user=user, wishlist_item__group=self).exists()

# Group Membership
class GroupMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    group = models.ForeignKey(WishlistGroup, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[('member', 'Member'), ('manager', 'Manager')], default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} in {self.group.title}"

# Wishlist Item
class WishlistItem(models.Model):
    APPROVAL_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    group = models.ForeignKey(WishlistGroup, on_delete=models.CASCADE, related_name="wishlist_items")
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_approved = models.CharField(choices=APPROVAL_CHOICES, default='pending', max_length=10)
    
    is_selected = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.get_is_approved_display()}"

    def approve(self):
        self.is_approved = 'approved'
        self.save()

    def reject(self):
        self.is_approved = 'rejected'
        self.save()


    def __str__(self):
        return f"{self.name} ({'Approved' if self.is_approved == 'approved' else 'Pending'})"

# Contributions for Surprise Gift Groups
class Contribution(models.Model):
    wishlist_item = models.ForeignKey(WishlistItem, on_delete=models.CASCADE, related_name="contributions")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} contributed ₹{self.amount} to {self.wishlist_item.name}"

# Product (E-commerce Integration)
class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image_url = models.URLField()
    purchase_url = models.URLField()  # Link to external e-commerce platform
    category = models.CharField(max_length=100, blank=True, null=True)  # Optional category for better organization

    def __str__(self):
        return self.name

# User Budget Tracking
class UserBudget(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="budget")
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    spending_cap = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username}'s Budget"

    def remaining_budget(self):
        # Calculate remaining budget (assuming spending_cap is the limit)
        return self.spending_cap - self.total_spent()

    def total_spent(self):
        # Calculate total amount spent (example, could be contributions)
        total = self.contributions.aggregate(total_spent=models.Sum('amount'))['total_spent'] or 0
        return total

# Notifications
# Notification for new followers
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:50]}"


class Follow(models.Model):
    follower = models.ForeignKey(User, related_name="following", on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name="followers", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

    class Meta:
        unique_together = ('follower', 'following') 


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(WishlistGroup, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} in {self.group.title}"

from django.db import models
from django.contrib.auth.models import User

class GiftSelection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    wishlist_item = models.OneToOneField('WishlistItem', on_delete=models.CASCADE)
    selected_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} selected {self.wishlist_item.name}"
