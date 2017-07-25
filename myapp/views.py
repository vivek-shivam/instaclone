from __future__ import unicode_literals
from myapp.forms import SignUpForm
from myapp.forms import LoginForm ,PostForm,LikeForm,CommentForm
from models import UserModel,SessionToken,PostModel,LikeModel,CommentModel,CategoryModel
from django.contrib.auth.hashers import make_password,check_password
from django.shortcuts import render,redirect
from intrest.settings import BASE_DIR
from imgurpython import ImgurClient
from clarifai import rest
from clarifai.rest import ClarifaiApp
from datetime import datetime,timedelta
from django.utils import timezone
import sendgrid

from sendgrid.helpers.mail import *
import ctypes
#keys not given!!!

clarafai_api_key='b97f3b583d9149798fbf429dc82277f2'
SENDGRID_API_KEY='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'
IMGUR_CLIENT_ID = "9c9bf0c17f4ac16"
IMGUR_CLIENT_SECRET = "cd2f3f14d28677368f0c26ee558ff6841e6e098a"

def signup_view(request):
  today = datetime.now()
  if request.method == "POST":
      signup_form=SignUpForm(request.POST)
      if signup_form.is_valid():
          username = signup_form.cleaned_data['username']
          name = signup_form.cleaned_data['name']
          email = signup_form.cleaned_data['email']
          password = signup_form.cleaned_data['password']
          if set('abcdefghijklmnopqrstuvwxyz').intersection(name) and set('abcdefghijklmnopqrstuvwxyz@_1234567890').intersection(username):
              if len(username) > 4 and len(password) > 5:  #and username==""== False and username.isdigit() == False:
                  user = UserModel(name=name, password=make_password(password), email=email, username=username)
                  user.save()
                  sg = sendgrid.SendGridAPIClient(apikey=(SENDGRID_API_KEY))
                  from_email = Email("vivekshivam007@gmail.com")
                  to_email = Email(signup_form.cleaned_data['email'])
                  subject = "Welcome "
                  content = Content("text/plain", "Thank you for signing up ")
                  mail = Mail(from_email, subject, to_email, content)
                  response = sg.client.mail.send.post(request_body=mail.get())
                  print(response.status_code)
                  print(response.body)
                  print(response.headers)
                  ctypes.windll.user32.MessageBoxW(0, u"successfully signed up", u"success", 0)
                  return render(request, 'login.html')
              else:
                  ctypes.windll.user32.MessageBoxW(0, u"invalid enteries. please try again", u"Error", 0)
                  signup_form= SignUpForm()

          else:
              ctypes.windll.user32.MessageBoxW(0, u"invalid name/username", u"error", 0)


  elif request.method == 'GET':
      signup_form= SignUpForm()
  return render(request, 'index.html', { 'date_to_show':today, 'form':signup_form})



def login_view(request):
    response_data = {}
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = UserModel.objects.filter(username=username).first()

            if user:
                if check_password(password, user.password):
                    token = SessionToken(user=user)
                    token.create_token()
                    token.save()
                    response = redirect('feed/')
                    response.set_cookie(key='session_token', value=token.session_token)
                    return response
                else:
                    ctypes.windll.user32.MessageBoxW(0, u"invalid username or password", u"Error", 0)
                    response_data['message'] = 'Incorrect Password! Please try again!'
            else:
                ctypes.windll.user32.MessageBoxW(0, u"invalid username/password", u"Error", 0)

    elif request.method == 'GET':
        form = LoginForm()
    response_data['form'] = form
    return render(request, 'login.html', response_data)

def add_category(post):
    app = ClarifaiApp(api_key=clarafai_api_key)
    model = app.models.get("general-v1.3")
    response = model.predict_by_url(url=post.image_url)

    if response["status"]["code"] == 10000:
        if response["outputs"]:
            if response["outputs"][0]["data"]:
                if response["outputs"][0]["data"]["concepts"]:
                    for index in range(0, len(response["outputs"][0]["data"]["concepts"])):
                        category = CategoryModel(post=post, category_text = response["outputs"][0]["data"]["concepts"][index]["name"])
                        category.save()
                else:
                    print "No Concepts List Error"
            else:
                print "No Data List Error"
        else:
            print "No Outputs List Error"
    else:
        print "Response Code Error"


def post_view(request):
    user = check_validation(request)

    if user:
        if request.method == 'POST':
            form = PostForm(request.POST, request.FILES)
            if form.is_valid():
                image = form.cleaned_data.get('image')
                caption = form.cleaned_data.get('caption')
                post = PostModel(user=user, image=image, caption=caption)
                post.save()

                path = str(BASE_DIR + post.image.url)

                client = ImgurClient( IMGUR_CLIENT_ID,IMGUR_CLIENT_SECRET)
                post.image_url = client.upload_from_path(path, anon=True)['link']
                post.save()

                add_category(post)

                return redirect('/feed/')


        else:
            form = PostForm()
        return render(request, 'post.html', {'form': form})
    else:
        return redirect('/login/')


def feed_view(request):
    user = check_validation(request)
    if user:

        posts = PostModel.objects.all().order_by('-created_on')

        for post in posts:
            existing_like = LikeModel.objects.filter(post_id=post.id, user=user).first()
            if existing_like:
                post.has_liked = True

        return render(request, 'feed.html', {'posts': posts})
    else:

        return redirect('/login/')


def like_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = LikeForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id

            existing_like = LikeModel.objects.filter(post_id=post_id, user=user).first()
            if not existing_like:
                like = LikeModel.objects.create(post_id=post_id, user=user)
                sg = sendgrid.SendGridAPIClient(apikey=(SENDGRID_API_KEY))
                from_email = Email("vivekshivam007@gmail.com")
                to_email = Email(like.post.user.email)
                subject = "like on your post!!"
                content = Content("text/plain", "someone just liked your post")
                mail = Mail(from_email, subject, to_email, content)
                response = sg.client.mail.send.post(request_body=mail.get())
                print(response.status_code)
                print(response.body)
                print(response.headers)
                ctypes.windll.user32.MessageBoxW(0, u"liked successfully", u"SUCCESS", 0)
            else:
                existing_like.delete()
                ctypes.windll.user32.MessageBoxW(0, u"unlike successfully", u"SUCCESS", 0)

            return redirect('feed/')

    else:
        return redirect('/login/')

def comment_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            comment_text = form.cleaned_data.get('comment_text')
            comment = CommentModel.objects.create(user=user, post_id=post_id, comment_text=comment_text)
            comment.save()
            sg = sendgrid.SendGridAPIClient(apikey=(SENDGRID_API_KEY))
            from_email = Email("vivekshivam007@gmail.com")
            to_email = Email(comment.post.user.email)
            subject = "comment on your post!!"
            content = Content("text/plain", "someone just commented on your post")
            mail = Mail(from_email, subject, to_email, content)
            response = sg.client.mail.send.post(request_body=mail.get())
            print(response.status_code)
            print(response.body)
            print(response.headers)
            ctypes.windll.user32.MessageBoxW(0, u"comment posted successfully", u"SUCCESS", 0)
            return redirect('/feed/    ')
        else:
            return redirect('/feed/')
    else:
        return redirect('/login')


# For validating the session
def check_validation(request):
    if request.COOKIES.get('session_token'):
        session = SessionToken.objects.filter(session_token=request.COOKIES.get('session_token')).first()
        if session:
            time_to_live = session.created_on + timedelta(days=10)
            if time_to_live > timezone.now():
                return session.user
    else:
        return None

def logout_view(request):
    if request.COOKIES.get('session_token'):
        session = SessionToken.objects.filter(session_token=request.COOKIES.get('session_token')).first()
        if session:
            session.delete()
            return render(request, 'logout.html')
    else:
        return None

def vivek_view(request):
    user = check_validation(request)
    if user:

        posts = PostModel.objects.filter().order_by('-created_on')

        for post in posts:
            existing_like = LikeModel.objects.filter(post_id=post.id, user=user).first()
            if existing_like:
                post.has_liked = True

        return render(request, 'vivek_shivam.html', {'posts': posts})
    else:

        return redirect('/login/')




def specific_user_post_view(request,user_name):
    user = check_validation(request)
    if user:
        posts=PostModel.objects.all().filter(user__username=user_name)
        return render(request,'specificuser.html',{'posts':posts,'user_name':user_name})
    else:
        return redirect('/login/')