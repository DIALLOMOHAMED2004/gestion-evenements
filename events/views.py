from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Event, EventRegistration, Category
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal

@login_required
def create_event(request):
    if not request.user.is_organizer():
        messages.error(request, "Seuls les organisateurs peuvent créer des événements.")
        return redirect('event_list')

    # Récupérer toutes les catégories pour le formulaire
    categories = Category.objects.all()
    context = {'categories': categories}

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        location = request.POST.get('location')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        available_seats = request.POST.get('available_seats')
        event_type = request.POST.get('event_type')
        ticket_price = request.POST.get('ticket_price', '0.00')
        category_id = request.POST.get('category')
        visibility = request.POST.get('visibility', 'public')
        is_private = visibility == 'private'

        # Validation de base
        if not all([title, description, location, start_date, end_date, available_seats, category_id]):
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return render(request, 'events/create_event.html', context)

        try:
            category = get_object_or_404(Category, id=category_id)
            event = Event.objects.create(
                title=title,
                description=description,
                location=location,
                start_date=start_date,
                end_date=end_date,
                available_seats=available_seats,
                event_type=event_type,
                ticket_price=ticket_price,
                organizer=request.user,
                category=category,
                is_private=is_private
            )
            
            if is_private:
                event.generate_invitation_link()

            if 'image' in request.FILES:
                event.image = request.FILES['image']
                event.save()

            messages.success(request, "L'événement a été créé avec succès!")
            return redirect('events:event_detail', event_id=event.id)
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite lors de la création de l'événement: {str(e)}")
            return render(request, 'events/create_event.html', context)

    return render(request, 'events/create_event.html', context)

@login_required
def event_list(request):
    # Récupérer tous les événements à venir
    events = Event.objects.filter(start_date__gte=timezone.now())
    
    # Récupérer les catégories pour le filtre
    categories = Category.objects.all()
    
    # Filtrage par catégorie
    category_id = request.GET.get('category')
    if category_id:
        events = events.filter(category_id=category_id)
    
    # Filtrage par lieu
    location = request.GET.get('location')
    if location:
        events = events.filter(location__icontains=location)
    
    # Filtrage par date
    date = request.GET.get('date')
    if date:
        events = events.filter(start_date__date=date)
    
    # Filtrage par type d'événement
    event_type = request.GET.get('type')
    if event_type:
        events = events.filter(event_type=event_type)
    
    # Filtrage par visibilité
    if not request.user.is_organizer():
        events = events.filter(
            Q(is_private=False) |
            Q(organizer=request.user) |
            Q(registrations__participant=request.user)
        ).distinct()
    
    # Recherche
    search_query = request.GET.get('search')
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Tri par date
    events = events.order_by('start_date')
    
    # Pagination
    paginator = Paginator(events, 9)  # 9 événements par page
    page = request.GET.get('page')
    events = paginator.get_page(page)
    
    context = {
        'events': events,
        'categories': categories,
        'selected_category': category_id,
        'selected_location': location,
        'selected_date': date,
        'search_query': search_query,
        'event_type': event_type
    }
    
    return render(request, 'events/event_list.html', context)

@login_required
def event_detail(request, event_id, invitation_link=None):
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier si l'utilisateur a le droit d'accéder à l'événement
    if not event.is_public:
        # L'organisateur a toujours accès à son événement
        if event.organizer != request.user:
            # Vérifier si l'utilisateur a un lien d'invitation valide
            if not invitation_link or str(event.invitation_link) != invitation_link:
                messages.error(request, "Cet événement est privé. Vous avez besoin d'une invitation pour y accéder.")
                return redirect('events:event_list')
    is_registered = EventRegistration.objects.filter(event=event, participant=request.user).exists()
    
    return render(request, 'events/event_detail.html', {
        'event': event,
        'is_registered': is_registered
    })


@login_required
def event_register(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier si l'utilisateur est déjà inscrit
    if EventRegistration.objects.filter(event=event, participant=request.user).exists():
        messages.warning(request, "Vous êtes déjà inscrit à cet événement.")
        return redirect('events:event_detail', event_id=event.id)
    
    # Vérifier s'il reste des places
    if event.is_full():
        messages.error(request, "Désolé, cet événement est complet.")
        return redirect('events:event_detail', event_id=event.id)
    
    # Vérifier si l'événement est payant
    if event.event_type == Event.EventType.PAID:
        # Pour cet exemple, nous allons simplement marquer le paiement comme effectué
        # Dans un cas réel, vous devriez intégrer un système de paiement
        payment_status = True
    else:
        payment_status = True  # Gratuit, donc marqué comme payé
    
    # Créer l'inscription
    registration = EventRegistration.objects.create(
        event=event,
        participant=request.user,
        payment_status=payment_status
    )
    
    # Envoyer l'email de confirmation
    try:
        subject = f"Confirmation d'inscription - {event.title}"
        message = f"""Bonjour {request.user.first_name},

Votre inscription à l'événement '{event.title}' a été confirmée.

Détails de l'événement :
- Date : {event.start_date.strftime('%d/%m/%Y %H:%M')}
- Lieu : {event.location}
- Type : {'Gratuit' if event.event_type == Event.EventType.FREE else 'Payant'}

Merci de votre participation !

Cordialement,
L'équipe organisatrice"""
        
        from django.core.mail import send_mail
        send_mail(
            subject,
            message,
            'noreply@example.com',  # Remplacer par votre email d'envoi
            [request.user.email],
            fail_silently=False,
        )
    except Exception as e:
        # Logger l'erreur mais ne pas bloquer l'inscription
        print(f"Erreur d'envoi d'email : {str(e)}")
    
    messages.success(
        request,
        "Inscription réussie ! Un email de confirmation vous a été envoyé."
        if payment_status else
        "Inscription en attente de paiement."
    )
    
    return redirect('events:event_detail', event_id=event.id)

@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    categories = Category.objects.all()

    if request.method == 'POST':
        try:
            # Update event fields
            event.title = request.POST.get('title')
            event.description = request.POST.get('description')
            event.location = request.POST.get('location')
            event.start_date = request.POST.get('start_date')
            event.end_date = request.POST.get('end_date')
            event.available_seats = request.POST.get('available_seats')
            event.event_type = request.POST.get('event_type')
            event.ticket_price = request.POST.get('ticket_price', '0.00')
            
            # Gérer la visibilité
            visibility = request.POST.get('visibility')
            event.is_private = (visibility == 'private')
            
            # Gérer la catégorie
            category_id = request.POST.get('category')
            if category_id:
                event.category = get_object_or_404(Category, id=category_id)
            
            # Générer un nouveau lien d'invitation si l'événement devient privé
            if event.is_private and not event.invitation_link:
                event.generate_invitation_link()
            
            # Gérer l'image
            if 'image' in request.FILES:
                event.image = request.FILES['image']
            
            # Save changes
            event.save()
            messages.success(request, "L'événement a été modifié avec succès!")
            return redirect('events:event_detail', event_id=event.id)
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification de l'événement : {str(e)}")
    
    return render(request, 'events/edit_event.html', {
        'event': event,
        'categories': categories
    })

@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, organizer=request.user)

    if request.method == 'POST':
        event.delete()
        messages.success(request, "L'événement a été supprimé avec succès!")
        return redirect('events:event_list')

    return render(request, 'events/delete_event.html', {'event': event})

@login_required
def dashboard(request):
    if not request.user.is_organizer():
        messages.error(request, "Seuls les organisateurs ont accès au tableau de bord.")
        return redirect('index')
    
    # Récupérer tous les événements de l'organisateur
    events = Event.objects.filter(organizer=request.user).order_by('-start_date')
    
    # Calculer les statistiques globales
    total_events = events.count()
    
    # Calculer le nombre total d'inscriptions
    total_registrations = EventRegistration.objects.filter(event__organizer=request.user).count()
    
    # Calculer le nombre total de billets payants vendus
    total_paid_tickets = EventRegistration.objects.filter(
        event__organizer=request.user,
        event__event_type=Event.EventType.PAID,
        payment_status=True
    ).count()
    
    # Calculer le revenu total
    total_revenue = Decimal('0.00')
    for event in events.filter(event_type=Event.EventType.PAID):
        total_revenue += event.total_revenue()
    
    context = {
        'events': events,
        'total_events': total_events,
        'total_registrations': total_registrations,
        'total_paid_tickets': total_paid_tickets,
        'total_revenue': total_revenue,
        'now': timezone.now()
    }
    
    return render(request, 'events/dashboard.html', context)