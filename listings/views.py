from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import EquipmentForm
import json
from .models import Equipment
from .mpesa import initiate_stk_push
import time
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


# Create your views here.

@login_required
def add_equipment(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            # 1. Create the object but don't save to DB yet
            equipment = form.save(commit=False)
            
            # 2. Attach the currently logged-in user as the owner
            equipment.user = request.user 
            
            # 3. Now save it for real
            equipment.save()
            
            messages.success(request, "Tractor listed successfully! Check the map.")
            return redirect('map_view')
        else:
            print(form.errors)
    else:
        form = EquipmentForm()
    
    return render(request, 'add_listing.html', {'form': form})

def home (request):
    return render(request, 'index.html')

def starter(request):
    return render(request, 'starter.html')

def map_view(request):
    # Fetch all equipment from the database
    all_equipment = Equipment.objects.all()
    
    # We create a list of dictionaries to pass to JavaScript
    locations = []
    for item in all_equipment:
        locations.append({
            'id': item.id,
            'name': item.name,
            'type': item.get_type_display(),
            'price': str(item.price_per_hour),
            'lat': item.location.y,
            'lng': item.location.x,
        })
    
    # Convert the list to a JSON string
    context = {
        'equipment_json': json.dumps(locations)
    }
    return render(request, 'map.html', context)

def index(request):
    # Fetch units belonging to the logged-in owner
    all_units = Equipment.objects.filter(user=request.user)
    
    # Split them by status
    active_units = all_units.filter(status='Active')
    idle_units = all_units.filter(status='Idle')
    
    context = {
        'active_units': active_units,
        'idle_units': idle_units,
        'active_count': active_units.count(),
        'idle_count': idle_units.count(),
    }
    return render(request, 'index.html', context)

def toggle_status(request, pk):
    item = get_object_or_404(Equipment, pk=pk)
    item.is_rented = not item.is_rented
    # Quick hack: Add a dummy renter name if renting out
    if item.is_rented:
        item.current_renter = "Neighboring Farm"
    item.save()
    return redirect('index')

#Payment
def pay_for_machinery(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    # Get phone number from a form or user profile
    phone = "254712345678" # Start with 254
    
    response = initiate_stk_push(phone, equipment.price_per_hour)
    
    if response.get('ResponseCode') == '0':
        messages.success(request, "M-Pesa Push sent! Please enter your PIN.")
    else:
        messages.error(request, "Failed to initiate M-Pesa payment.")
        
    return redirect('index')

def pay_view(request, pk):
    # 1. Trigger the real M-Pesa push
    # initiate_stk_push(phone, amount) 
    
    # 2. Simulate the 'Waiting' and 'Success' UI
    messages.info(request, "Waiting for M-Pesa PIN entry...")
    
    equipment = Equipment.objects.get(pk=pk)
    equipment.is_rented = False # It's been returned and paid for
    equipment.save()
    
    messages.success(request, f"Payment of KES {equipment.price_per_hour} received! Equipment is now available.")
    return redirect('index')


def request_order(request, equipment_id):
    if request.method == "POST":
        equipment = get_object_or_404(Equipment, id=equipment_id)
        owner = equipment.user 
        
        channel_layer = get_channel_layer()
        
        # Send message to the owner's specific group
        async_to_sync(channel_layer.group_send)(
            f"user_{owner.id}", # This matches the group name in consumers.py
            {
                "type": "order_notification",
                "machine_name": equipment.name,
                "renter_name": request.user.username,
            }
        )
        
        return JsonResponse({"status": "success"})
    

    #Login and Registration Views
def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index') # Redirect to your home page
    else:
        form = UserCreationForm()
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

@csrf_exempt
def accept_order(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        machine_name = data.get('machine_name')
        
        # 1. Update the Database
        equipment = Equipment.objects.get(name=machine_name)
        equipment.status = 'Active'
        equipment.save()
        
        # 2. Prepare the notification
        channel_layer = get_channel_layer()
        
        # Notify the OWNER (to update their dashboard status live)
        async_to_sync(channel_layer.group_send)(
            f"user_{request.user.id}", 
            {
                "type": "status_update_message", # This MUST match the method name in consumers.py
                "machine_name": machine_name,
                "new_status": "Active"
            }
        )
        
        # TODO: Notify the RENTER 
        # (This requires passing the renter_id from the map to the modal to the view)
        
        return JsonResponse({'status': 'success'})