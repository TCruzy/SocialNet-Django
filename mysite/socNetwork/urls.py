from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views



app_name = 'soc'
urlpatterns = [
    path('', views.login, name='login'),
    path('home/', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('logout/',views.logout, name='logout'),
    path('create-post/', views.create_post, name='create_post'),
    path('my-posts/', views.my_posts, name='my_posts'),
    path('posts/<int:id>/', views.user_posts, name='user_posts'),
    path('like-post/', views.like_post, name='like_post'),
    path('edit-post/<int:post_id>/', views.edit_post, name='edit_post'),
    path('delete-post/<int:post_id>', views.delete_post, name='delete_post'),
    path('search/', views.search_name, name='search_name'),
    path('main_profile/<str:username>/', views.main_profile, name='main_profile'),
    path('edit_picture/<int:userid>/', views.edit_picture, name='edit_picture'),
    path('follow_user/<int:id>/', views.follow_user, name='follow_user'),
    path('liked_posts/', views.liked_posts, name='liked_posts'),
    path('user/<str:username>/', views.user, name='user'),
    path('user_main_profile/<int:userId>/', views.user_main_profile, name='user_main_profile'),
    path('users_liked_posts/<int:id>/', views.users_liked_posts, name='users_liked_posts'),
    path('profile_info_privacy/<int:id>/', views.profile_info_privacy, name='profile_info_privacy'),
    path('see_posts/<int:postid>/', views.go_to_post, name='go_to_post'),
    path('anonymous_profile/', views.anonymous_profile, name='anonymous_profile'),
    path('accounts/login/', auth_views.LoginView.as_view()),]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)