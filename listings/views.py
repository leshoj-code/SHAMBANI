from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import EquipmentForm

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
        
    return render(request, 'listings/add_listing.html', {'form': form})