from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_text
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail, EmailMessage
from config import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from . tokens import generateToken
from django.contrib.auth.decorators import login_required
from .models import Profile, User  # Import our custom User model


# Create your views here.


def home(request, *args, **kwargs):
    return render(request, 'authentification/index.html')


def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        email = request.POST['email']
        password = request.POST['password']
        confirmpwd = request.POST['comfirmpwd']
        
        # Validation checks
        if User.objects.filter(username=username):
            messages.add_message(request,messages.ERROR, 'username already taken please try another.')
            return render(request,'authentification/signup.html',{'messages':messages.get_messages(request)})
            
        if User.objects.filter(email=email):
            messages.add_message(request,messages.ERROR, 'This email has an account.')
            return render(request,'authentification/signup.html',{'messages':messages.get_messages(request)})
            
        if len(username)>10:
            messages.add_message(request,messages.ERROR, 'Please the username must not be more than 10 character.')
            return render(request,'authentification/signup.html',{'messages':messages.get_messages(request)})
            
        if len(username)<5:
            messages.add_message(request,messages.ERROR, 'Please the username must be at leat 5 characters.')
            return render(request,'authentification/signup.html',{'messages':messages.get_messages(request)})
            
        if not username.isalnum():
            messages.add_message(request,messages.ERROR, 'username must be alphanumeric')
            return render(request,'authentification/signup.html',{'messages':messages.get_messages(request)})

        if password != confirmpwd:
            messages.add_message(request,messages.ERROR, 'The password did not match! ')
            return render(request,'authentification/signup.html',{'messages':messages.get_messages(request)})

        # Create new user
        my_user = User.objects.create_user(username=username, email=email, password=password)
        my_user.first_name = firstname
        my_user.last_name = lastname
        my_user.is_active = False
        my_user.role = User.Role.PARTICIPANT  # Set default role as participant
        my_user.save()

        # Create user profile
        profile = Profile.objects.create(user=my_user)
        
        messages.add_message(request,messages.SUCCESS, 'Your account has been successfully created. we have sent you an email You must comfirm in order to activate your account.')

        # Send welcome email
        subject = "Welcome to django-application donaldPro"
        message = "Welcome "+ my_user.first_name + " " + my_user.last_name + "\n thank for chosing Dprogrammeur website for test login.\n To order login you need to comfirm your email account.\n thanks\n\n\n donald programmeur"
        from_email = settings.EMAIL_HOST_USER
        to_list = [my_user.email]
        send_mail(subject, message, from_email, to_list, fail_silently=False)

        # Send confirmation email
        current_site = get_current_site(request) 
        email_suject = "confirm your email DonaldPro Django Login!"
        messageConfirm = render_to_string("emailConfimation.html", {
            'name': my_user.first_name,
            'domain':current_site.domain,
            'uid':urlsafe_base64_encode(force_bytes(my_user.pk)),
            'token': generateToken.make_token(my_user)
        })       

        email = EmailMessage(
            email_suject,
            messageConfirm,
            settings.EMAIL_HOST_USER,
            [my_user.email]
        )

        email.fail_silently = False
        email.send()
        
        return render(request,'authentification/signin.html',{'messages':messages.get_messages(request)})
        
    return render(request, 'authentification/signup.html')    


def signin(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        my_user = User.objects.get(username=username)

        if user is not None:
            login(request, user)
            firstname = user.first_name
            return render(request, 'authentification/index.html', {"firstname":firstname})
        elif my_user.is_active == False:
            messages.add_message(request,messages.ERROR, 'you have not confirm your  email do it, in order to activate your account')
            return render(request,'authentification/signin.html')
        else:
            messages.add_message(request,messages.ERROR, 'bad authentification')
            return render(request,'authentification/index.html',{'messages':messages.get_messages(request)})

    return render(request, 'authentification/signin.html')    

def signout(request):
    logout(request)
    messages.success(request, 'logout successfully!')
    return redirect('home')

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        my_user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        my_user = None

    if my_user is not None and generateToken.check_token(my_user, token):
        my_user.is_active  = True        
        my_user.save()
        messages.add_message(request,messages.SUCCESS, "You are account is activated you can login by filling the form below.")
        return render(request,"authentification/signin.html",{'messages':messages.get_messages(request)})
    else:
        messages.add_message(request,messages.ERROR, 'Activation failed please try again')
        return render(request,'authentification/index.html',{'messages':messages.get_messages(request)})

@login_required
def profile(request):
    if request.method == 'POST':
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = Profile(user=request.user)

        # Mise à jour des informations du profil
        profile.bio = request.POST.get('bio', '')
        profile.address = request.POST.get('address', '')
        profile.phone_number = request.POST.get('phone_number', '')
        
        # Gestion de la date de naissance
        birth_date = request.POST.get('date_of_birth')
        if birth_date:
            profile.date_of_birth = birth_date

        # Gestion de la photo de profil
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        
        profile.save()
        
        # Mise à jour des informations utilisateur
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        
        # Mise à jour du rôle
        new_role = request.POST.get('role')
        if new_role in [User.Role.PARTICIPANT, User.Role.ORGANIZER]:
            if new_role != user.role:
                user.role = new_role
                messages.info(request, f'Votre rôle a été changé en {user.get_role_display()}')
        
        user.save()
        
        messages.success(request, 'Votre profil a été mis à jour avec succès!')
        return redirect('profile')
    
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile(user=request.user)
        profile.save()
    
    return render(request, 'authentification/profile.html', {'profile': profile})

@login_required
def change_role(request):
    if not request.user.is_superuser:
        messages.error(request, "Vous n'avez pas la permission de changer les rôles.")
        return redirect('profile')
        
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_role = request.POST.get('role')
        
        try:
            user = User.objects.get(id=user_id)
            if new_role in [role[0] for role in User.Role.choices]:
                user.role = new_role
                user.save()
                messages.success(request, f'Le rôle de {user.username} a été mis à jour.')
            else:
                messages.error(request, 'Rôle invalide.')
        except User.DoesNotExist:
            messages.error(request, 'Utilisateur non trouvé.')
            
    return redirect('admin:index')
