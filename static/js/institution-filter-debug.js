document.addEventListener('DOMContentLoaded', function() {
    console.log('=== Institution Filter Debug Script Loaded ===');
    
    const educationLevel = document.getElementById('id_education_level');
    const institutionSelect = document.getElementById('id_institution');
    
    if (!educationLevel || !institutionSelect) {
        console.error('Required elements not found!');
        return;
    }
    
    // Log the education level options
    console.log('Education Level Options:');
    Array.from(educationLevel.options).forEach(opt => {
        console.log(`  Value: "${opt.value}", Text: "${opt.text}"`);
    });
    
    // Store original institutions
    const originalOptions = Array.from(institutionSelect.options).map(opt => ({
        value: opt.value,
        text: opt.text
    }));
    console.log('Original institutions:', originalOptions);
    
    educationLevel.addEventListener('change', function() {
        const level = this.value;
        const levelText = this.options[this.selectedIndex].text;
        console.log(`Education level changed to: "${level}" (${levelText})`);
        
        if (!level) {
            return;
        }
        
        // Show loading state
        institutionSelect.disabled = true;
        institutionSelect.innerHTML = '<option value="">Loading...</option>';
        
        // Fetch institutions
        const url = `/bursary/ajax/filter-institutions/?education_level=${level}`;
        console.log('Fetching URL:', url);
        
        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
            },
            credentials: 'same-origin'
        })
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Response data:', data);
            
            // Clear and rebuild options
            institutionSelect.innerHTML = '<option value="">---------</option>';
            
            if (data.institutions && data.institutions.length > 0) {
                console.log(`Adding ${data.institutions.length} institutions:`);
                
                data.institutions.forEach(inst => {
                    const option = new Option(inst.name, inst.id);
                    institutionSelect.appendChild(option);
                    console.log(`  Added: ${inst.name} (ID: ${inst.id}, Type: ${inst.type})`);
                });
            } else {
                console.log('No institutions returned!');
                console.log('Debug info:', data.debug);
                
                // Show all institutions as fallback
                console.log('Showing all original institutions as fallback...');
                originalOptions.forEach(opt => {
                    if (opt.value) {  // Skip empty option
                        const option = new Option(opt.text, opt.value);
                        institutionSelect.appendChild(option);
                    }
                });
            }
            
            // Add "Other" option
            const otherOption = new Option('Other (specify below)', '');
            institutionSelect.appendChild(otherOption);
            
            institutionSelect.disabled = false;
        })
        .catch(error => {
            console.error('Fetch error:', error);
            
            // On error, restore original options
            institutionSelect.innerHTML = '';
            originalOptions.forEach(opt => {
                const option = new Option(opt.text, opt.value);
                institutionSelect.appendChild(option);
            });
            institutionSelect.disabled = false;
        });
    });
    
    // Trigger change event if education level is pre-selected
    if (educationLevel.value) {
        console.log('Initial education level:', educationLevel.value);
        // Don't auto-trigger to preserve existing selection
        // educationLevel.dispatchEvent(new Event('change'));
    }
});