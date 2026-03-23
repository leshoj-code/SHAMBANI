from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import *
from .models import *
from .mpesa import initiate_stk_push, format_phone
import json
from django.http import JsonResponse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def home(request):
    if request.user.is_authenticated:
        return redirect('index')   
    return render(request, 'landing.html')


def starter(request):
    return render(request, 'starter.html')


@login_required
def index(request):
    all_units    = Equipment.objects.filter(user=request.user)
    active_units = all_units.filter(status='Active')
    idle_units   = all_units.filter(status='Idle')
    context = {
        'equipment_list': all_units,          # used by owner_dashboard.html
        'active_units':   active_units,
        'idle_units':     idle_units,
        'active_count':   active_units.count(),
        'idle_count':     idle_units.count(),
    }
    return render(request, 'index.html', context)


@login_required
def add_equipment(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            equipment       = form.save(commit=False)
            equipment.user  = request.user
            equipment.save()
            messages.success(request, "Tractor listed successfully! Check the map.")
            return redirect('map_view')
        else:
            print(form.errors)
    else:
        form = EquipmentForm()
    return render(request, 'add_listing.html', {'form': form})


@login_required
def map_view(request):
    all_equipment = Equipment.objects.select_related('user__profile').all()
    locations = []
    for item in all_equipment:
        locations.append({
            'id':          item.id,
            'name':        item.name,
            'type':        item.get_type_display(),
            'price':       str(item.price_per_hour),
            'lat':         item.location.y,
            'lng':         item.location.x,
            'owner_phone': item.user.profile.phone if hasattr(item.user, 'profile') else '',
        })
    return render(request, 'map.html', {'equipment_json': json.dumps(locations)})


@login_required
def request_order(request, equipment_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    equipment                  = get_object_or_404(Equipment, id=equipment_id)
    equipment.current_renter   = request.user
    equipment.save()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{equipment.user.id}",
        {
            "type":         "order_notification",
            "order_id":     equipment.id,         # JS stores this for acceptOrder()
            "machine_name": equipment.name,
            "renter_name":  request.user.username,
        }
    )
    return JsonResponse({'status': 'sent'})


@login_required
def accept_order(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data         = json.loads(request.body)
    equipment_id = data.get('order_id')
    equipment    = get_object_or_404(Equipment, id=equipment_id, user=request.user)

    equipment.status = 'Active'
    equipment.save()

    channel_layer = get_channel_layer()

    # Notify Owner — badge update
    async_to_sync(channel_layer.group_send)(
        f"user_{request.user.id}",
        {
            "type":         "status_update_message",
            "equipment_id": equipment.id,
            "machine_name": equipment.name,
            "new_status":   "Active",
        }
    )

    # Notify Renter
    if equipment.current_renter:
        async_to_sync(channel_layer.group_send)(
            f"user_{equipment.current_renter.id}",
            {
                "type":    "renter_message",
                "message": f"Great news! Your request for {equipment.name} was accepted.",
            }
        )

    return JsonResponse({'status': 'success'})


@login_required
def pay_for_machinery(request, pk):
    if request.method != 'POST':
        return redirect('index')

    equipment = get_object_or_404(Equipment, pk=pk)

    # Read phone from the renter's profile instead of hardcoded number
    try:
        raw_phone = equipment.current_renter.profile.phone
    except AttributeError:
        messages.error(request, "Renter phone number not found.")
        return redirect('index')

    phone    = format_phone(raw_phone)
    response = initiate_stk_push(phone, equipment.price_per_hour)

    if response.get('ResponseCode') == '0':
        messages.success(request, "Check your phone! M-Pesa PIN prompt sent.")
    else:
        messages.error(request, "Error: " + response.get('CustomerMessage', 'Could not reach Safaricom.'))

    return redirect('index')

@login_required
def pay_view(request, pk):
    equipment            = get_object_or_404(Equipment, pk=pk)
    equipment.is_rented  = False
    equipment.save()
    messages.success(request, f"Payment of KES {equipment.price_per_hour} received! Equipment is now available.")
    return redirect('index')


@login_required
def toggle_status(request, pk):
    item          = get_object_or_404(Equipment, pk=pk)
    item.is_rented = not item.is_rented
    if item.is_rented:
        item.current_renter = "Neighboring Farm"
    item.save()
    return redirect('index')

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user            = form.save(commit=False)
            user.email      = form.cleaned_data['email']
            user.first_name = form.cleaned_data['full_name'].split()[0]
            user.last_name  = ' '.join(form.cleaned_data['full_name'].split()[1:])
            user.save()

            # Save extra fields to profile
            UserProfile.objects.create(
                user      = user,
                phone     = form.cleaned_data['phone'],
                role      = form.cleaned_data['role'],
                full_name = form.cleaned_data['full_name'],
            )

            login(request, user)

            # Route based on role
            if form.cleaned_data['role'] == 'owner':
                return redirect('index')
            else:
                return redirect('map_view')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')