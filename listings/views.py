from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import EquipmentForm
import json
from .models import Equipment

# Create your views here.

def add_equipment(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tractor listed successfully! Check the map.")
            return redirect('map_view') # We will create this next
        else:
            # This helps debug if the map click didn't send the right data
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
    all_units = Equipment.objects.all()
    active_units = all_units.filter(is_rented=True)
    idle_units = all_units.filter(is_rented=False)
    
    context = {
        'active_units': active_units,
        'idle_count': idle_units.count(),
        'active_count': active_units.count(),
        'total_count': all_units.count(),
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