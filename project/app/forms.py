from django import forms
from .models import WishlistGroup

class WishlistGroupForm(forms.ModelForm):
    class Meta:
        model = WishlistGroup
        fields = ['group_type', 'title', 'description']  # Code is auto-generated

from django import forms

class JoinGroupForm(forms.Form):
    code = forms.CharField(max_length=10, required=True, label="Group Code")

from django import forms
from .models import WishlistGroup

class BudgetForm(forms.ModelForm):
    class Meta:
        model = WishlistGroup
        fields = ['budget_limit']

class DeadlineForm(forms.ModelForm):
    class Meta:
        model = WishlistGroup
        fields = ['submission_deadline']

from django import forms
from .models import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['full_name', 'dob', 'gender', 'bio', 'profile_picture']  