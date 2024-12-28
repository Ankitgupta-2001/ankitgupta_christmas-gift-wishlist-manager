from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
     path('signup/', views.signup, name='signup'),
     path('signin/', views.signin, name='signin'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('create-group/', views.create_group, name='create_group'),
    path('group/<int:group_id>/details/', views.group_details, name='group_details'),
     path('join-group/', views.join_group, name='join_group'),
     path('created-groups/', views.created_groups, name='created_groups'),
    path('joined-groups/', views.joined_groups, name='joined_groups'),
    path('group/<int:group_id>/', views.group_view, name='group_view'),
     path('group/<int:id>/info/', views.group_info, name='group_info'),
    path('group/<int:group_id>/wishlist-item/', views.wishlist_item_form, name='wishlist_item_form'),
    path('group/<int:group_id>/wishlist-item/edit/<int:item_id>/', views.edit_wishlist_item, name='edit_wishlist_item'),
    path('group/<int:group_id>/members/', views.group_members, name='group_members'),
    
      path('profile/',views.profile_view, name='profile'),
       path('create-profile/', views.profile_form, name='profile_form'),
      
    path('profile/edit/',views.edit_profile, name='edit_profile'),
     
        path('member/<int:member_id>/', views.member_view, name='member_view'),

      path('group/<int:group_id>/submitted_wishlist_items/', views.submitted_wishlist_items, name='submitted_wishlist_items'),
    path('wishlist_item/<int:item_id>/approve/', views.approve_wishlist_item, name='approve_wishlist_item'),
    path('wishlist_item/<int:item_id>/reject/', views.reject_wishlist_item, name='reject_wishlist_item'),
   path('group/<int:group_id>/launch-wishlist/', views.launch_wishlist, name='launch_wishlist'),

    # Random Gift Selection
    path('group/<int:group_id>/select-random-gift/', views.select_gift, name='select_gift'),
     path('group/<int:group_id>/view-selected-item/', views.view_selected_item, name='view_selected_item'),
     
     path('chats/<int:group_id>/', views.chats, name='chats'),
         path('follow/<int:user_id>/', views.follow_user, name='follow_user'),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow_user'),

 
]