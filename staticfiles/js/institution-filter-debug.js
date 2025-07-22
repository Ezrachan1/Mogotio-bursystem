document.addEventListener('DOMContentLoaded', function() {
    console.log('=== Institution Filter Debug Script Loaded ===');
    
    const educationLevel = document.getElementById('id_education_level');
    const institutionSelect = document.getElementById('id_institution');
    
    if (!educationLevel || !institutionSelect) {
        console.error('Required elements not found!');
        console.log('Education Level element:', educationLevel);
        console.log('Institution Select element:', institutionSelect);
        return;
    }
    
    console.log('Form elements found successfully');
    
    // Store original options
    const originalOptions = Array.from(institutionSelect.options).map(opt => ({
        value: opt.value,
        text: opt.text
    }));
    console.log('Original institutions:', originalOptions);
    
    educationLevel.addEventListener('change', function() {
        const level = this.value;
        console.log('Education level changed to:', level);
        
        if (!level) {
            // Restore original options if no level selected
            institutionSelect.innerHTML = '';
            originalOptions.forEach(opt => {
                const option = new Option(opt.text, opt.value);
                institutionSelect.appendChild(option);
            });
            return;
        }
        
        // First, let's test if the AJAX endpoint is accessible
        console.log('Testing AJAX endpoint...');
        
        // Test the simple endpoint first
        fetch('/bursary/ajax/test-institutions/')
            .then(response => {
                console.log('Test endpoint response:', response);
                return response.json();
            })
            .then(data => {
                console.log('Test endpoint data:', data);
            })
            .catch(error => {
                console.error('Test endpoint error:', error);
            });
        
        // Now try the actual filter endpoint
        const url = `/bursary/ajax/filter-institutions/?education_level=${level}`;
        console.log('Fetching from:', url);
        
        institutionSelect.disabled = true;
        institutionSelect.innerHTML = '<option value="">Loading...</option>';
        
        fetch(url)
            .then(response => {
                console.log('Filter response status:', response.status);
                console.log('Filter response OK:', response.ok);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Filter response data:', data);
                
                // Clear select
                institutionSelect.innerHTML = '<option value="">---------</option>';
                
                if (data.institutions && data.institutions.length > 0) {
                    console.log(`Adding ${data.institutions.length} institutions`);
                    
                    data.institutions.forEach(inst => {
                        const option = new Option(inst.name, inst.id);
                        institutionSelect.appendChild(option);
                        console.log(`Added: ${inst.name} (${inst.id})`);
                    });
                } else {
                    console.log('No institutions returned');
                    institutionSelect.innerHTML = '<option value="">No institutions found</option>';
                }
                
                // Add "Other" option
                const otherOption = new Option('Other (specify below)', '');
                institutionSelect.appendChild(otherOption);
                
                institutionSelect.disabled = false;
            })
            .catch(error => {
                console.error('Filter error:', error);
                institutionSelect.innerHTML = '<option value="">Error loading institutions</option>';
                institutionSelect.disabled = false;
                
                // Restore original options as fallback
                console.log('Restoring original options due to error');
                institutionSelect.innerHTML = '';
                originalOptions.forEach(opt => {
                    const option = new Option(opt.text, opt.value);
                    institutionSelect.appendChild(option);
                });
            });
    });
});