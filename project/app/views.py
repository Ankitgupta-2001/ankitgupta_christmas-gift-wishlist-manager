from django.shortcuts import (
    render, redirect, get_object_or_404, HttpResponseRedirect
)
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum
from django.contrib import messages

from .models import (
    WishlistGroup, GroupMember, WishlistItem, UserProfile, Contribution,GiftSelection
)
from .forms import WishlistGroupForm, JoinGroupForm
 


# Landing Page
def landing_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, 'landing.html')


# User Authentication Views
def signup(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already in use.")
            return render(request, 'signup.html')

        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, "Account created successfully! Please sign in.")
        return redirect('signin')

    return render(request, 'signup.html')


def signin(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user and user.check_password(password):
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password.")
    
    return render(request, 'signin.html')


def logout_view(request):
    logout(request)
    return redirect('landing_page')


# Dashboard
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')


# Group Management Views
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserProfile

@login_required
def create_group(request):
    """
    Handles the creation of a new wishlist group.
    Ensures the user's profile is complete before allowing group creation.
    """
    # Check if the user has a profile and whether it is complete
    user_profile = UserProfile.objects.filter(user=request.user).first()
    if not user_profile or not user_profile.full_name or not user_profile.bio:
        messages.warning(request, "Please complete your profile before creating a group.")
        return redirect('profile_form')

    # Process form submission
    if request.method == 'POST':
        form = WishlistGroupForm(request.POST)
        if form.is_valid():
            new_group = form.save(commit=False)
            new_group.owner = request.user
            new_group.save()
            messages.success(request, "Group created successfully!")
            return redirect('group_details', group_id=new_group.id)
    else:
        form = WishlistGroupForm()

    return render(request, 'create_group.html', {'form': form})



@login_required
def group_details(request, group_id):
    group = get_object_or_404(WishlistGroup, id=group_id)
    return render(request, 'group_details.html', {'group': group})
@login_required
def join_group(request):
    """
    Handles joining a wishlist group using a unique code without using Django's messages framework.
    Feedback is passed directly to the template via context.
    """
    form = JoinGroupForm()
    error_message = None
    success_message = None

    if request.method == 'POST':
        form = JoinGroupForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            group = WishlistGroup.objects.filter(code=code).first()

            if not group:
                error_message = "Invalid group code. Please enter correct group code."
            elif GroupMember.objects.filter(group=group, user=request.user).exists():
                error_message = "You are already a member of this group."
            else:
                GroupMember.objects.create(group=group, user=request.user)
                success_message = "You have joined the group successfully!"
                return redirect('group_details', group_id=group.id)

    return render(request, 'join_group.html', {
        'form': form,
        'error_message': error_message,
        'success_message': success_message
    })


@login_required
def created_groups(request):
    created_groups = WishlistGroup.objects.filter(owner=request.user)
    return render(request, 'created_groups.html', {'created_groups': created_groups})


@login_required
def joined_groups(request):
    joined_groups = WishlistGroup.objects.filter(groupmember__user=request.user)
    return render(request, 'joined_groups.html', {'joined_groups': joined_groups})

@login_required
def group_view(request, group_id):
    group = get_object_or_404(WishlistGroup, id=group_id)

    # Redirect to launch_wishlist if the group is launched and the user hasn't selected a gift
    if group.is_launched and not group.has_user_selected_gift(request.user):
        return redirect('launch_wishlist', group_id=group.id)

    if request.method == 'POST' and request.user == group.owner:
        # Update budget limit
        if 'budget_limit' in request.POST:
            budget_limit = request.POST.get('budget_limit')
            try:
                group.budget_limit = None if budget_limit.lower() == 'unlimited' else float(budget_limit)
            except ValueError:
                messages.error(request, "Invalid budget value.")
                return redirect('group_view', group_id=group.id)
            group.save()

        # Update submission deadline
        if 'submission_deadline' in request.POST:
            group.submission_deadline = request.POST.get('submission_deadline')
            group.save()

        messages.success(request, "Group settings updated successfully!")
        return HttpResponseRedirect(request.path)
    wishlist_items_count = WishlistItem.objects.filter(group=group, is_approved="approved").count()
    group_members_count1 = GroupMember.objects.filter(group=group).count() 
    group_members_count=group_members_count1+1

    return render(request, 'group_view.html', {'group': group,'wishlist_items_count': wishlist_items_count,
        'group_members_count': group_members_count})

from django.utils.timezone import now
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import WishlistGroup, WishlistItem

@login_required
def wishlist_item_form(request, group_id):
    # Fetch the group and check if the deadline has passed
    group = get_object_or_404(WishlistGroup, id=group_id)
    current_time = now()  # Get current time
    
    if group.submission_deadline and current_time > group.submission_deadline:
        messages.error(request, "Submission deadline has passed.")
        return redirect('group_view', group_id=group_id)

    # Check if the user already submitted an item
    existing_item = WishlistItem.objects.filter(group=group, submitted_by=request.user).first()

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')

        # Validate input
        if not name:
            messages.error(request, "Item name is required.")
            return render(request, 'wishlist_item_form.html', {
                'group': group,
                'existing_item': existing_item,
                'current_time': current_time,
            })

        # Save or update the wishlist item
        if existing_item:
            existing_item.name = name
            existing_item.description = description
            existing_item.price = price
            existing_item.save()
        else:
            WishlistItem.objects.create(
                group=group,
                submitted_by=request.user,
                name=name,
                description=description,
                price=price
            )

        messages.success(request, "Your wishlist item has been saved!")
        return redirect('group_view', group_id=group_id)

    # Render the template with existing data
    return render(request, 'wishlist_item_form.html', {
        'group': group,
        'existing_item': existing_item,
        'current_time': current_time,  # Pass the current time to the template
    })



@login_required
def edit_wishlist_item(request, group_id, item_id):
    group = get_object_or_404(WishlistGroup, id=group_id)
    item = get_object_or_404(WishlistItem, id=item_id, group=group, submitted_by=request.user)

    if group.submission_deadline and timezone.now() > group.submission_deadline:
        messages.error(request, "Submission deadline has passed.")
        return redirect('group_view', group_id=group_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')

        if not name:
            messages.error(request, "Name is required.")
            return render(request, 'edit_wishlist_item.html', {'group': group, 'item': item})

        item.name = name
        item.description = description
        item.price = price
        item.save()

        messages.success(request, "Wishlist item updated successfully!")
        return redirect('group_view', group_id=group_id)

    return render(request, 'edit_wishlist_item.html', {'group': group, 'existing_item': item})


# Profile Management
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import UserProfile, GroupMember, Contribution

 
@login_required
def profile_view(request):
    user_profile = UserProfile.objects.get(user=request.user)
    followers_count = Follow.objects.filter(following=request.user).count()
    following_count = Follow.objects.filter(follower=request.user).count()
    joined_groups = GroupMember.objects.filter(user=request.user)
    contributions = Contribution.objects.filter(user=request.user)

    context = {
        'user_profile': user_profile,
        'joined_groups_count': joined_groups.count(),
        'followers_count': followers_count,
        'following_count': following_count,
        'total_contributions': contributions.aggregate(total=Sum("amount"))["total"] or 0,
    }
    return render(request, 'profile.html', context)


     

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from .forms import UserProfileForm

@login_required
def profile_form(request):
    """
    Handles the creation or update of a user's profile.
    Redirects to the profile view if the profile already exists.
    """
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)

    return render(request, 'profile_form.html', {'form': form})


@login_required
def edit_profile(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_profile.full_name = request.POST.get('full_name', user_profile.full_name)
        user_profile.dob = request.POST.get('dob', user_profile.dob)
        user_profile.gender = request.POST.get('gender', user_profile.gender)
        user_profile.bio = request.POST.get('bio', user_profile.bio)

        if 'profile_picture' in request.FILES:
            user_profile.profile_picture = request.FILES['profile_picture']

        user_profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')

    return render(request, 'edit_profile.html', {'user_profile': user_profile})



@login_required
def group_members(request, group_id):
    group = get_object_or_404(WishlistGroup, id=group_id)
    members = GroupMember.objects.filter(group=group)

    # Separate the logged-in user from other members
    logged_in_member = None
    other_members = []

    for member in members:
        if member.user == request.user:
            logged_in_member = member
        else:
            other_members.append(member)

    # Put the logged-in user last in the list
    members_to_display = other_members + [logged_in_member] if logged_in_member else other_members

    context = {
        'group': group,
        'members': members_to_display,  # Reordered members
        'user_id': request.user.id,  # Pass the logged-in user ID to template
    }

    return render(request, 'group_members.html', context)

from django.contrib import messages 
from django.contrib import messages  # Django's messaging framework
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages  # Ensure the messaging framework is imported
from django.shortcuts import render, redirect, get_object_or_404
from .models import WishlistGroup, GroupMember, Message
from django.contrib.auth.decorators import login_required

@login_required
def chats(request, group_id):
    group = get_object_or_404(WishlistGroup, id=group_id)
    
    # Check if the user is a member of the group
     

    # Fetch messages related to the group, ordered by timestamp
    chat_messages = Message.objects.filter(group=group).order_by('timestamp')

    if request.method == 'POST':
        # Get the message content and trim whitespace
        content = request.POST.get('message_content', '').strip()
        if content:
            # Save the new message
            Message.objects.create(
                group=group,
                sender=request.user,
                content=content
            )
            # Add a success message
            messages.success(request, "Message sent successfully!")
            return redirect('chats', group_id=group.id)  # Redirect to avoid resubmission
        else:
            # Add an error message for empty content
            messages.error(request, "Message content cannot be empty.")

    context = {
        'group': group,
        'messages': chat_messages,  # Use a distinct name to avoid conflicts
    }
    return render(request, 'group_chat.html', context)



@login_required
def group_info(request, id):
    # Fetch the group or return a 404 if not found
    group = get_object_or_404(WishlistGroup, id=id)

    # Check if the user is authorized to view the group
    is_member = GroupMember.objects.filter(group=group, user=request.user).exists()
    if not (group.owner == request.user or is_member):
        return HttpResponseForbidden("You are not authorized to view this group.")

    # Fetch relevant group details
    members = GroupMember.objects.filter(group=group).select_related('user')
    submitted_items = WishlistItem.objects.filter(group=group)
    remaining_members = members.exclude(user__wishlistitem__group=group)

    # Calculate remaining budget per person if budget limit exists
    total_budget = group.budget_limit
    total_submitted_cost = submitted_items.aggregate(total=Sum('price'))['total'] or 0
    remaining_budget = total_budget - total_submitted_cost if total_budget else None

    # Pass group details to the template
    context = {
        'group': group,
        'members': members,
        'submitted_items': submitted_items,
        'remaining_members': remaining_members,
        'total_budget': total_budget,
        'remaining_budget': remaining_budget,
        'submission_deadline': group.submission_deadline,
    }

    return render(request, 'group_info.html', context)


 

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseForbidden
from django.db.models import Sum
from .models import GroupMember, UserProfile, Contribution, Follow
@login_required
def member_view(request, member_id):
    # Fetch the group member or return a 404 if not found
    member = get_object_or_404(GroupMember, id=member_id)
    group = member.group

    # Check if the user is authorized to view the group member's details
    is_member_or_owner = (
        group.owner == request.user or
        GroupMember.objects.filter(group=group, user=request.user).exists()
    )
    if not is_member_or_owner:
        return HttpResponseForbidden("You are not authorized to view this member's details.")

    # Fetch the member's user profile
    user_profile = get_object_or_404(UserProfile, user=member.user)

    # Get the list of groups the member is part of
    joined_groups = GroupMember.objects.filter(user=member.user)

    # Get the list of contributions made by the member
    contributions = Contribution.objects.filter(user=member.user)

    # Calculate follower and following counts
    follower_count = Follow.objects.filter(following=member.user).count()
    following_count = Follow.objects.filter(follower=member.user).count()

    # Check if the current user is following the member
    is_following = Follow.objects.filter(follower=request.user, following=member.user).exists()

    # Check if the member is following the current user
    is_followed_by = Follow.objects.filter(follower=member.user, following=request.user).exists()

    # Prepare the context for rendering
    context = {
        'user_profile': user_profile,
        'joined_groups_count': joined_groups.count(),
        'total_contributions': contributions.aggregate(total=Sum("amount"))["total"] or 0,
        'is_following': is_following,
        'is_followed_by': is_followed_by,
        'follower_count': follower_count,
        'following_count': following_count,
        'member': member,  # Pass member context for URL or other purposes
    }
    return render(request, 'member_view.html', context)



 
def submitted_wishlist_items(request, group_id):
    group = get_object_or_404(WishlistGroup, id=group_id)

    # Ensure only the owner can access this page
    if request.user != group.owner:
        return redirect('group_info', group_id=group.id)

    # Fetch all wishlist items using the correct related name
    wishlist_items = group.wishlist_items.all()

    return render(request, 'submitted_wishlist_items.html', {
        'group': group,
        'wishlist_items': wishlist_items,
    })

# Approve wishlist item

from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from .models import WishlistItem

@login_required
def approve_wishlist_item(request, item_id):
    item = get_object_or_404(WishlistItem, id=item_id)

    # Ensure only the group owner can approve
    if request.user != item.group.owner:
 
        return redirect('submitted_wishlist_items', group_id=item.group.id)

    # Approve the wishlist item
    item.is_approved = "approved"
    item.save()
 

    return redirect('submitted_wishlist_items', group_id=item.group.id)



@login_required
def reject_wishlist_item(request, item_id):
    item = get_object_or_404(WishlistItem, id=item_id)

    # Ensure only the group owner can reject
    if request.user != item.group.owner:
        return redirect('submitted_wishlist_items', group_id=item.group.id)

    item.reject()
    return redirect('submitted_wishlist_items', group_id=item.group.id)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import WishlistGroup, WishlistItem, GroupMember
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .models import WishlistGroup, WishlistItem

@login_required
def launch_wishlist(request, group_id):
    group = get_object_or_404(WishlistGroup, id=group_id, owner=request.user)

    # Launch the wishlist if not already launched
    if not group.is_launched:
        group.is_launched = True
        group.save()

    # Handle the POST request for selecting an item
    if request.method == "POST":
        selected_item_id = request.POST.get("selected_item")
        if selected_item_id:
            selected_item = get_object_or_404(
                WishlistItem,
                id=selected_item_id,
                group=group,
                is_approved="approved",
                is_selected=False
            )
            # Mark the selected item as "selected"
            selected_item.is_selected = True
            selected_item.save()

            return render(request, 'launch_wishlist.html', {
                'group': group,
                'selected_item': selected_item
            })

    # Fetch all approved, unselected wishlist items excluding the owner's items
    items = WishlistItem.objects.filter(
        group=group,
        is_approved="approved",
        is_selected=False
    ).order_by('?')

    if not items.exists():
        return render(request, 'launch_wishlist.html', {
            'error': "No unselected wishlist items available.",
            'group': group
        })

    return render(request, 'launch_wishlist.html', {
        'group': group,
        'items': items
    })


@login_required
def select_gift(request, group_id):
    group = get_object_or_404(WishlistGroup, id=group_id)

    if request.method == 'POST':
        selected_item_id = request.POST.get('selected_item')
        
        # Use .first() to get a single object from the QuerySet
        item = WishlistItem.objects.filter(
            id=selected_item_id,
            group=group,
            is_approved="approved",
            is_selected=False  # Ensure the gift hasn't been selected already
        ).first()

        print(item)  # Debugging print to check if the item is fetched correctly

        # If no valid item is found, render the page with an error message
        if not item:
            return render(request, 'launch_wishlist.html', {
                'group': group,
                'items': WishlistItem.objects.filter(
                    group=group,
                    is_approved="approved",
                    is_selected=False
                ).exclude(submitted_by=request.user),
                'error': "Invalid selection. Please choose again."
            })

        # Mark the gift as selected
        item.is_selected = True
        item.save()

        # Optionally, save the selection to a `GiftSelection` model
        GiftSelection.objects.create(user=request.user, wishlist_item=item)

        return redirect('group_view', group_id=group.id)


from django.shortcuts import render, get_object_or_404
 

from django.shortcuts import render, get_object_or_404
from .models import WishlistGroup, GiftSelection, WishlistItem

def view_selected_item(request, group_id):
    # Retrieve the group using the group_id
    group = get_object_or_404(WishlistGroup, id=group_id)
    
    # Check if the group is launched; if not, redirect or display a message
 

    # Get the selected item for the user in this group
    gift_selection = GiftSelection.objects.filter(user=request.user, wishlist_item__group=group).first()

    # If a selection exists, retrieve the selected item, else set it to None
    if gift_selection:
        selected_item = gift_selection.wishlist_item
    else:
        selected_item = None

    # Pass the group and selected item to the template for rendering
    return render(request, 'view_selected_item.html', {'group': group, 'selected_item': selected_item})



 
from .models import Follow, User, GroupMember
from django.http import JsonResponse
from django.contrib import messages

@login_required
def follow_user(request, user_id):
    user_to_follow = get_object_or_404(User, id=user_id)

    if user_to_follow == request.user:
        return JsonResponse({'error': 'You cannot follow yourself.'}, status=400)

    _, created = Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
    message = (f'You are now following {user_to_follow.username}.' 
               if created else 'You are already following this user.')

    return JsonResponse({'message': message, 'is_following': created})


@login_required
def unfollow_user(request, user_id):
    user_to_unfollow = get_object_or_404(User, id=user_id)

    deleted, _ = Follow.objects.filter(follower=request.user, following=user_to_unfollow).delete()
    if deleted:
        return JsonResponse({'message': f'You have unfollowed {user_to_unfollow.username}.', 'is_following': False})
    else:
        return JsonResponse({'message': 'You were not following this user.', 'is_following': True})




