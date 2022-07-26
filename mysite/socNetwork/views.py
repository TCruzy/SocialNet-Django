from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.urls import reverse
from django.views import View
from .models import User, Posts, Likes, Followers
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth.backends import BaseBackend

# Create your views here.
class MyView(LoginRequiredMixin, View):
    login_url = '/'
    redirect_field_name = 'next'   
   
def user_is_authenticated(request):
    if 'username' in request.session:
        return True
    return False

@csrf_protect
def login(request):
    if not user_is_authenticated(request):
        csrfContext = RequestContext(request)
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('soc:home'))
        if request.method == "POST":
            username = request.POST['username']
            password = request.POST['password']
            user = User.objects.filter(username=username, password=password)
            if user:
                request.session['username'] = username
                return HttpResponseRedirect(reverse('soc:home'))
            else:
                print(request.user, 'tu sheeshalaa')
                return render(request, 'registration/login.html', {'error': 'Invalid username or password', 'csrfContext': csrfContext})
        print(request.user)
        request.session['signup'] = True
        return render(request, 'registration/login.html')
    return HttpResponseRedirect(reverse('soc:home'))


def register(request):
    if user_is_authenticated(request):
        return HttpResponseRedirect(reverse('soc:home'))
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = User.objects.filter(username=username)
        if user:
            return render(request, 'register.htm', {'error': 'Username already exists'})
        else:
            user = User(username=username, password=password)
            user.save()
            return HttpResponseRedirect('/')
    if request.method == "GET":
        request.session.pop('signup', None)
        return render(request, 'register.htm')

#@login_required(redirect_field_name='next')
def anonymous_profile(request):
    if user_is_authenticated(request):
        return render(request, 'anonymous.htm')
    return HttpResponseRedirect(reverse('soc:login'))

#@login_required(redirect_field_name='next')
def home(request):
    if user_is_authenticated(request):  
        posts = Posts.objects.all().order_by('-post_date')
        main_posts = []
        users = User.objects.all()

        logined_user_id = User.objects.get(username=request.session['username']).id
        for post in posts:
            user_id_from_likes = Likes.objects.filter(postId=post).values_list('userId', flat=True)
            liked_by_usernames = []
            for user_id in user_id_from_likes:
                liked_by_usernames.append({'username': User.objects.get(id=user_id).username, 'id': user_id,
                                            'profile_pic': User.objects.get(id=user_id).profile_pic})
            for user in users:
                if post.userId.id == user.id and Likes.objects.filter(userId=logined_user_id, postId=post.id):
                    main_posts.append({'post': post, 'user': user, 'liked_by_me': True, 'liked_by': liked_by_usernames})
                if post.userId.id == user.id and not Likes.objects.filter(userId=logined_user_id, postId=post.id):
                    main_posts.append(
                        {'post': post, 'user': user, 'liked_by_me': False, 'liked_by': liked_by_usernames})

        return render(request, 'home.htm', {'posts': main_posts})
    return HttpResponseRedirect(reverse('soc:login'))

#@login_required(redirect_field_name='next')
def edit_post(request, post_id):
    if user_is_authenticated(request):
        post = Posts.objects.get(id=post_id)
        if request.method == "POST":
            post.post_content = request.POST['post_content']
            post.poster_type = request.POST['poster_type']
            image = request.FILES.get('image', False)
            if image:
                post.image = image
                post.save()
            post.save()
            return HttpResponseRedirect(reverse('soc:home'))
        else:
            return render(request, 'edit_post.htm', {'post': post})
    return HttpResponseRedirect(reverse('soc:login'))

#@login_required(redirect_field_name='next')
def create_post(request):
    if user_is_authenticated(request):
        if request.method == 'POST':
            poster_type = request.POST['poster_type']
            post = request.POST['post_content']
            img = request.FILES.get('image', None)
            user = User.objects.get(username=request.session['username'])
            if poster_type == 'anonym':
                post = Posts(userId=user, poster_type=poster_type, post_content=post, image=img)
                post.save()
            elif poster_type == 'user':
                post = Posts(post_content=post, userId=user, image=img)
                post.save()

            return HttpResponseRedirect(reverse('soc:home'))
    return HttpResponseRedirect(reverse('soc:login'))
#@login_required(redirect_field_name='next')
def edit_picture(request, userid):
    if user_is_authenticated(request):
        user = User.objects.get(id=userid)
        username = user.username
        if request.method == "POST":
            image = request.FILES.get('profile_picture', False)
            if image:
                user.profile_pic = image
                user.save()

            return HttpResponseRedirect(reverse('soc:main_profile', args=(username,)))
    return HttpResponseRedirect(reverse('soc:login'))


#@login_required(redirect_field_name='next')
def my_posts(request):
    if user_is_authenticated(request):
        posts = Posts.objects.filter(userId__username=request.session['username']).order_by('-post_date')
        main_posts = []
        for post in posts:
            main_posts.append({'post': post, 'user': {'username': request.session['username'],
                                                    'id': User.objects.get(username=request.session['username']).id,
                                                    'pic': User.objects.get(
                                                        username=request.session['username']).profile_pic}})

        return render(request, 'my_posts.htm', {'posts': main_posts})
    return HttpResponseRedirect(reverse('soc:login'))

#@login_required(redirect_field_name='next')
def main_profile(request, username):
    if user_is_authenticated(request):
        if username != request.session['username']:
            return HttpResponseRedirect(reverse('soc:home'))      
        try:
            user = User.objects.get(username=username)
            
            posts_count = Posts.objects.filter(userId=user).count()
            likes_amount = Likes.objects.filter(userId=user).count()
            liked_amount = Likes.objects.filter(postId__userId=user).count()
            follower_amount = Followers.objects.filter(userId=user.id).count()
            follower_images = []
            for follower in Followers.objects.filter(userId=user.id):
                follower_id = follower.followerId
                follower_images.append({'pic': User.objects.get(id=follower.followerId).profile_pic})
            followed_amount = Followers.objects.filter(followerId=user.id).count()
            followed_images = []
            for followed in Followers.objects.filter(followerId=user.id):
                followed_images.append({'pic': User.objects.get(id=followed.userId).profile_pic})

            post_content_from_liked_posts = Likes.objects.filter(userId=user).values_list('postId__post_content', flat=True)
            user_id_from_follower = Followers.objects.filter(userId=user.id).values_list('followerId', flat=True)
            follower_usernames = []
            for user_id in user_id_from_follower:
                follower_usernames.append({'username': User.objects.get(id=user_id).username, 'id': user_id})
            user_id_from_following = Followers.objects.filter(followerId=user.id).values_list('userId', flat=True)
            following_usernames = []
            for user_id in user_id_from_following:
                following_usernames.append({'username': User.objects.get(id=user_id).username, 'id': user_id})

            followers = zip(follower_usernames, follower_images)
            following = zip(following_usernames, followed_images)
            data = {'user': user, 'posts_count': posts_count, 'likes_amount': likes_amount,
                    'liked_amount': liked_amount, 'follower_amount': follower_amount,
                    'followed_amount': followed_amount, 'followers': followers,
                    'following': following, 'post_content': post_content_from_liked_posts}
            return render(request, 'main_profile.htm', data)
        except:
            return HttpResponseRedirect(reverse('soc:home'))
    return HttpResponseRedirect(reverse('soc:login'))

#@login_required(redirect_field_name='next')
def user_main_profile(request, userId):
    if user_is_authenticated(request):
        user = User.objects.get(id=userId)
        posts_count = Posts.objects.filter(userId=user, poster_type='user').count()
        likes_amount = Likes.objects.filter(userId=user).count()
        liked_amount = Likes.objects.filter(postId__userId=user).count()
        follower_amount = Followers.objects.filter(userId=user.id).count()
        follower_images = []
        for follower in Followers.objects.filter(userId=user.id):
            follower_id = follower.followerId
            follower_images.append({'pic': User.objects.get(id=follower.followerId).profile_pic})
        followed_amount = Followers.objects.filter(followerId=user.id).count()
        followed_images = []
        for followed in Followers.objects.filter(followerId=user.id):
            followed_images.append({'pic': User.objects.get(id=followed.userId).profile_pic})

        post_content_from_liked_posts = Likes.objects.filter(userId=user).values_list('postId__post_content', flat=True)
        user_id_from_follower = Followers.objects.filter(userId=user.id).values_list('followerId', flat=True)
        follower_usernames = []
        follower_names_list = []
        for user_id in user_id_from_follower:
            follower_names_list.append(User.objects.get(id=user_id).username)
            follower_usernames.append({'username': User.objects.get(id=user_id).username, 'id': user_id})
        user_id_from_following = Followers.objects.filter(followerId=user.id).values_list('userId', flat=True)
        following_usernames = []
        for user_id in user_id_from_following:
            following_usernames.append({'username': User.objects.get(id=user_id).username, 'id': user_id})

        followers = zip(follower_usernames, follower_images)
        following = zip(following_usernames, followed_images)
        # unzip followers and print them

        data = {'user': user, 'posts_count': posts_count, 'likes_amount': likes_amount,
                'liked_amount': liked_amount, 'follower_amount': follower_amount,
                'followed_amount': followed_amount, 'followers': followers,
                'following': following, 'post_content': post_content_from_liked_posts,
                'follower_usernames': follower_names_list}
        return render(request, 'user_main_profile.htm', data)
    return HttpResponseRedirect(reverse('soc:login'))



#@login_required(redirect_field_name='next')
def user_posts(request, id):
    if user_is_authenticated(request):
        user = User.objects.get(id=id)
        posts_count = Posts.objects.filter(userId=user, poster_type='user').count()
        posts = Posts.objects.filter(userId__username=user.username).order_by('-post_date')
        main_posts = []
        logined_user_id = User.objects.get(username=request.session['username']).id
        for post in posts:
            user_id_from_likes = Likes.objects.filter(postId=post).values_list('userId', flat=True)
            liked_by_usernames = []
            for user_id in user_id_from_likes:
                liked_by_usernames.append(User.objects.get(id=user_id).username)
            for users in User.objects.all():
                if post.userId.id == users.id and Likes.objects.filter(userId=logined_user_id, postId=post.id):
                    main_posts.append(
                        {'post': post, 'user': users, 'liked_by_me': True, 'liked_by': liked_by_usernames})
                if post.userId.id == users.id and not Likes.objects.filter(userId=logined_user_id, postId=post.id):
                    main_posts.append(
                        {'post': post, 'user': users, 'liked_by_me': False, 'liked_by': liked_by_usernames})

        return render(request, 'user_posts.htm', {'posts': main_posts, 'user': user, 'posts_count': posts_count})
    return HttpResponseRedirect(reverse('soc:login'))

#@login_required(redirect_field_name='next')
def user(request, username):
    if user_is_authenticated(request):
        user_id = User.objects.get(username=username).id
        return HttpResponseRedirect(reverse('soc:user_posts', args=(user_id,)))
    return HttpResponseRedirect(reverse('soc:login'))


#@login_required(redirect_field_name='next')
def liked_posts(request):
    if user_is_authenticated(request):
        user = User.objects.get(username=request.session['username'])  # დალოგინებული იუზერის  გაფილტრული ობიექტი
        likes = Likes.objects.filter(userId=user).order_by(
            '-postId__post_date')  # დალოგინებული იუზერის მიერ დალაიქებული პოსტები
        main_posts = []
        logined_user_id = User.objects.get(username=request.session['username']).id
        for like in likes:
            user_id_from_likes = Likes.objects.filter(postId=like.postId).values_list('userId', flat=True)
            liked_by_usernames = []
            for user_id in user_id_from_likes:
                liked_by_usernames.append(User.objects.get(id=user_id).username)
            for users in User.objects.all():
                if like.postId.userId.id == users.id and Likes.objects.filter(userId=logined_user_id,
                                                                            postId=like.postId):
                    main_posts.append(
                        {'post': like, 'user': users, 'liked_by_me': True, 'liked_by': liked_by_usernames})
                if like.postId.userId.id == users.id and not Likes.objects.filter(userId=logined_user_id,
                                                                                postId=like.postId):
                    main_posts.append(
                        {'post': like, 'user': users, 'liked_by_me': False, 'liked_by': liked_by_usernames})
        return render(request, 'liked_posts.htm', {'posts': main_posts})      
    return HttpResponseRedirect(reverse('soc:login'))



#@login_required(redirect_field_name='next')
def users_liked_posts(request, id):
    if user_is_authenticated(request):
        user = User.objects.get(id=id)
        likes = Likes.objects.filter(userId=user).order_by(
            '-postId__post_date')
        main_posts = []
        logined_user_id = User.objects.get(username=request.session['username']).id
        for like in likes:
            user_id_from_likes = Likes.objects.filter(postId=like.postId).values_list('userId', flat=True)
            liked_by_usernames = []
            for user_id in user_id_from_likes:
                liked_by_usernames.append(User.objects.get(id=user_id).username)
            for users in User.objects.all():
                if like.postId.userId.id == users.id and Likes.objects.filter(userId=logined_user_id,
                                                                            postId=like.postId):
                    main_posts.append(
                        {'post': like, 'user': users, 'liked_by_me': True, 'liked_by': liked_by_usernames})
                if like.postId.userId.id == users.id and not Likes.objects.filter(userId=logined_user_id,
                                                                                postId=like.postId):
                    main_posts.append(
                        {'post': like, 'user': users, 'liked_by_me': False, 'liked_by': liked_by_usernames})
        return render(request, 'liked_posts.htm', {'posts': main_posts})
    return HttpResponseRedirect(reverse('soc:login'))



#@login_required(redirect_field_name='next')
def search_name(request):
    if user_is_authenticated(request):
        if request.method == "POST":
            name = request.POST['search']
            search_filter = request.POST['search_filter']
            if search_filter == 'users':
                request.session['search'] = name
                logged_user_id = User.objects.get(username=request.session['username']).id
                users = User.objects.filter(username__icontains=name)
                users_list = []
                for user in users:
                    logged_user_following = Followers.objects.filter(userId=user.id, followerId=logged_user_id)
                    if logged_user_following:
                        users_list.append({'user': user, 'followed_by_me': True})
                    else:
                        users_list.append({'user': user, 'followed_by_me': False})
                return render(request, 'search_name.htm', {'users': users_list})
            if search_filter == 'posts':
                request.session['search'] = name
                posts = Posts.objects.filter(post_content__icontains=name,poster_type='user').order_by('-post_date')
                post_owner = []
                for post in posts:
                    post_owner.append({'post': post, 'user': User.objects.get(id=post.userId_id)})
                return render(request, 'search_post.htm', {'posts': post_owner})
            else:
                return HttpResponseRedirect(reverse('soc:search_name'))
        if request.method == "GET":
            if 'search' in request.session:
                try:
                    name = request.session['search']
                    logged_user_id = User.objects.get(username=request.session['username']).id
                    users = User.objects.filter(username__icontains=name)
                except:
                    return HttpResponseRedirect(reverse('soc:home'))
                finally:
                    users_list = []
                    for user in users:
                        logged_user_following = Followers.objects.filter(userId=user.id, followerId=logged_user_id)
                        if logged_user_following:
                            users_list.append({'user': user, 'followed_by_me': True})
                        else:
                            users_list.append({'user': user, 'followed_by_me': False})
                    return render(request, 'search_name.htm', {'users': users_list})
            else:
                return HttpResponseRedirect(reverse('soc:home'))
    return HttpResponseRedirect(reverse('soc:login'))


#@login_required(redirect_field_name='next')
def go_to_post(request, postid):
    if user_is_authenticated(request):
        posts = Posts.objects.filter(id=postid)
        main_posts = []
        users = User.objects.all()

        logined_user_id = User.objects.get(username=request.session['username']).id
        for post in posts:
            user_id_from_likes = Likes.objects.filter(postId=post).values_list('userId', flat=True)
            liked_by_usernames = []
            for user_id in user_id_from_likes:
                liked_by_usernames.append({'username': User.objects.get(id=user_id).username, 'id': user_id,
                                            'profile_pic': User.objects.get(id=user_id).profile_pic})
            for user in users:
                if post.userId.id == user.id and Likes.objects.filter(userId=logined_user_id, postId=post.id):
                    main_posts.append({'post': post, 'user': user, 'liked_by_me': True, 'liked_by': liked_by_usernames})
                if post.userId.id == user.id and not Likes.objects.filter(userId=logined_user_id, postId=post.id):
                    main_posts.append(
                        {'post': post, 'user': user, 'liked_by_me': False, 'liked_by': liked_by_usernames})
                    
        return render(request, 'home.htm', {'posts': main_posts})
    return HttpResponseRedirect(reverse('soc:login'))

#@login_required(redirect_field_name='next')
def like_post(request):
    if user_is_authenticated(request):
        if request.method == "POST":
        
            page = request.POST['page']
            like_status = request.POST['like_status']
            post_id = request.POST['postid']
            user = User.objects.get(username=request.session['username'])
            post = Posts.objects.get(id=post_id)
            if like_status == 'like':
                like = Likes(userId=user, postId=post)
                like.save()
                if page == 'home':
                    return HttpResponseRedirect(reverse('soc:home'))
                elif page == 'liked_posts':
                    return HttpResponseRedirect(reverse('soc:liked_posts'))
                return HttpResponseRedirect(reverse('soc:user_posts', args=(post.userId.id,)))
            elif like_status == 'unlike':
                like = Likes.objects.filter(userId=user, postId=post)
                like.delete()
                if page == 'home':
                    return HttpResponseRedirect(reverse('soc:home'))
                elif page == 'liked_posts':
                    return HttpResponseRedirect(reverse('soc:liked_posts'))
                return HttpResponseRedirect(reverse('soc:user_posts', args=(post.userId.id,)))
        return HttpResponseRedirect(reverse('soc:login'))
    return HttpResponseRedirect(reverse('soc:login'))



#@login_required(redirect_field_name='next')
def follow_user(request, id):
    if user_is_authenticated(request):
        user_on_screen = User.objects.get(id=id).id
        logged_user = User.objects.get(username=request.session['username']).id
        if Followers.objects.filter(userId=user_on_screen, followerId=logged_user):
            Followers.objects.filter(userId=user_on_screen, followerId=logged_user).delete()
            return HttpResponseRedirect(reverse('soc:search_name'))
        else:
            follow = Followers(userId=user_on_screen, followerId=logged_user)
            follow.save()
            return HttpResponseRedirect(reverse('soc:search_name'))
    return HttpResponseRedirect(reverse('soc:login'))



#@login_required(redirect_field_name='next')
def profile_info_privacy(request, id):
    if user_is_authenticated(request):
        user = User.objects.get(id=id)
        if request.method == "POST":
            if request.POST['info_privacy'] == 'public':
                user.profile_info = 'Public'
                user.save()
            elif request.POST['info_privacy'] == 'followers':
                user.profile_info = 'Followers'
                user.save()
            elif request.POST['info_privacy'] == 'private':
                user.profile_info = 'Private'
                user.save()

            return HttpResponseRedirect(reverse('soc:main_profile', args=(request.session['username'],)))
        if request.method == "GET":
            return HttpResponseRedirect(reverse('soc:main_profile', args=(request.session['username'],)))
    return HttpResponseRedirect(reverse('soc:login'))


#@login_required(redirect_field_name='next')
def delete_post(request, post_id):
    if user_is_authenticated(request):
        post = Posts.objects.get(id=post_id)
        post.delete()
        return HttpResponseRedirect(reverse('soc:home'))
    return HttpResponseRedirect(reverse('soc:login'))



def logout(request):
    request.session.pop('username', None)
    request.session.pop('search', None)
    return HttpResponseRedirect(reverse('soc:login'))
