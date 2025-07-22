document.addEventListener('DOMContentLoaded', function() {
    const educationLevel = document.getElementById('id_education_level');
    const institutionSelect = document.getElementById('id_institution');
    const newInstitutionDiv = document.querySelector('[id*="new_institution"]')?.parentElement || document.getElementById('new_institution_div');
    const newInstitutionField = document.getElementById('id_new_institution_name');
    
    if (!educationLevel || !institutionSelect) {
        console.log('Required form elements not found');
        return;
    }
    
    // Store the current selection
    let currentSelection = institutionSelect.value;
    
    function filterInstitutions() {
        const level = educationLevel.value;
        
        if (!level) {
            console.log('No education level selected');
            return;
        }
        
        console.log('Filtering institutions for level:', level);
        
        // Show loading state
        institutionSelect.disabled = true;
        institutionSelect.innerHTML = '<option value="">Loading institutions...</option>';
        
        // Build the URL
        const url = `/bursary/ajax/filter-institutions/?education_level=${level}`;
        console.log('Fetching from URL:', url);
        
        // Fetch filtered institutions
        fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
            },
            credentials: 'same-origin'
        })
        .then(response => {
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Received data:', data);
            
            // Clear and repopulate the select
            institutionSelect.innerHTML = '<option value="">---------</option>';
            
            if (!data.institutions || data.institutions.length === 0) {
                institutionSelect.innerHTML += '<option value="" disabled>No institutions found for this level</option>';
            } else {
                data.institutions.forEach(inst => {
                    const option = document.createElement('option');
                    option.value = inst.id;
                    option.textContent = inst.name;
                    
                    // Restore selection if it exists in the filtered list
                    if (inst.id == currentSelection) {
                        option.selected = true;
                    }
                    
                    institutionSelect.appendChild(option);
                });
            }
            
            // Add "Other" option
            const otherOption = document.createElement('option');
            otherOption.value = '';
            otherOption.textContent = 'Other (Please specify below)';
            institutionSelect.appendChild(otherOption);
            
            institutionSelect.disabled = false;
            
            // Trigger change event
            institutionSelect.dispatchEvent(new Event('change'));
        })
        .catch(error => {
            console.error('Error filtering institutions:', error);
            
            // Show error in select
            institutionSelect.innerHTML = '<option value="">Error loading institutions</option>';
            institutionSelect.disabled = false;
        });
    }
    
    // Add event listener for education level change
    educationLevel.addEventListener('change', filterInstitutions);
    
    // Show/hide new institution field
    institutionSelect.addEventListener('change', function() {
        if (!newInstitutionDiv) {
            return;
        }
        
        if (this.value === '' && this.selectedIndex > 0 && this.options[this.selectedIndex].text.includes('Other')) {
            newInstitutionDiv.style.display = 'block';
            if (newInstitutionField) {
                newInstitutionField.required = true;
            }
        } else if (this.value) {
            newInstitutionDiv.style.display = 'none';
            if (newInstitutionField) {
                newInstitutionField.required = false;
                newInstitutionField.value = '';
            }
        }
    });
    
    // Calculate suggested amount
    const totalFees = document.getElementById('id_total_fees');
    const otherSupport = document.getElementById('id_other_support');
    const amountRequested = document.getElementById('id_amount_requested');
    
    function calculateSuggestedAmount() {
        const total = parseFloat(totalFees.value) || 0;
        const support = parseFloat(otherSupport.value) || 0;
        const suggested = Math.max(0, total - support);
        
        if (amountRequested && !amountRequested.value) {
            amountRequested.value = suggested.toFixed(2);
        }
    }
    
    if (totalFees) {
        totalFees.addEventListener('input', calculateSuggestedAmount);
    }
    if (otherSupport) {
        otherSupport.addEventListener('input', calculateSuggestedAmount);
    }
    
    // Log initialization
    console.log('Institution filter script loaded successfully');
});