document.addEventListener('DOMContentLoaded', function() {
    // Initialize image upload preview
    const imageInput = document.getElementById('image');
    const imagePreview = document.getElementById('image-preview');
    
    if (imageInput && imagePreview) {
        imageInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    imagePreview.innerHTML = '';
                    imagePreview.appendChild(img);
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Handle outfit item selection in outfit creation/edit form
    const outfitForm = document.getElementById('outfit-form');
    if (outfitForm) {
        const selectedItems = new Map();
        const clothingItems = document.querySelectorAll('.clothing-item-select');
        
        clothingItems.forEach(item => {
            item.addEventListener('click', function() {
                const itemId = this.dataset.itemId;
                
                if (this.classList.contains('selected')) {
                    // Remove from selection
                    this.classList.remove('selected');
                    this.querySelector('.selection-indicator').classList.add('d-none');
                    selectedItems.delete(itemId);
                } else {
                    // Add to selection
                    this.classList.add('selected');
                    this.querySelector('.selection-indicator').classList.remove('d-none');
                    
                    // Get layer order
                    const layerOrder = document.getElementById('layer-order').value;
                    selectedItems.set(itemId, layerOrder);
                }
                
                // Update hidden input field with selections
                updateSelections();
            });
        });
        
        // Update hidden field with selected items
        function updateSelections() {
            const selectedItemsInput = document.getElementById('selected-items');
            const itemsArray = [];
            
            selectedItems.forEach((layerOrder, itemId) => {
                itemsArray.push(`${itemId},${layerOrder}`);
            });
            
            selectedItemsInput.value = itemsArray.join('|');
        }
    }
    
    // Toggle favorite status for outfits
    const favoriteToggles = document.querySelectorAll('.favorite-toggle');
    
    favoriteToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            
            const outfitId = this.dataset.outfitId;
            const starIcon = this.querySelector('i');
            
            fetch(`/outfits/${outfitId}/toggle-favorite`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.is_favorite) {
                        starIcon.classList.remove('inactive');
                        starIcon.classList.add('active');
                    } else {
                        starIcon.classList.remove('active');
                        starIcon.classList.add('inactive');
                    }
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
    
    // Filter toggling on mobile
    const filterToggle = document.getElementById('filter-toggle');
    const filterSection = document.getElementById('filter-section');
    
    if (filterToggle && filterSection) {
        filterToggle.addEventListener('click', function() {
            filterSection.classList.toggle('d-none');
            filterSection.classList.toggle('d-block');
        });
    }
    
    // Weather location update
    const weatherLocationForm = document.getElementById('weather-location-form');
    
    if (weatherLocationForm) {
        weatherLocationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const location = document.getElementById('weather-location').value;
            
            fetch(`/api/weather?location=${encodeURIComponent(location)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                        return;
                    }
                    
                    // Update weather display
                    document.getElementById('weather-location-display').textContent = data.location;
                    document.getElementById('weather-temperature').textContent = `${data.temperature}°C`;
                    document.getElementById('weather-condition').textContent = data.condition;
                    
                    // Update weather icon
                    const weatherIcon = document.getElementById('weather-icon');
                    
                    // Set icon based on condition
                    if (data.condition.toLowerCase().includes('rain')) {
                        weatherIcon.className = 'fas fa-cloud-rain';
                    } else if (data.condition.toLowerCase().includes('cloud')) {
                        weatherIcon.className = 'fas fa-cloud';
                    } else if (data.condition.toLowerCase().includes('sun') || 
                              data.condition.toLowerCase().includes('clear')) {
                        weatherIcon.className = 'fas fa-sun';
                    } else if (data.condition.toLowerCase().includes('snow')) {
                        weatherIcon.className = 'fas fa-snowflake';
                    } else {
                        weatherIcon.className = 'fas fa-cloud-sun';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Failed to fetch weather data. Please try again.');
                });
        });
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}); 