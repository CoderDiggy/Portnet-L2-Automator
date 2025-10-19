// Export Results Function
function exportResults() {
    // Get data from the page
    const results = {
        incident: {
            id: document.querySelector('code').textContent,
            description: document.querySelector('.description-box p').textContent.trim(),
            source: document.querySelectorAll('.info-item strong')[0]?.textContent.trim(),
            reported_at: document.querySelectorAll('.info-item strong')[1]?.textContent.trim()
        },
        analysis: {
            incident_type: document.querySelectorAll('.analysis-value')[0]?.textContent.trim(),
            pattern_match: document.querySelectorAll('.analysis-value')[1]?.textContent.trim(),
            urgency: document.querySelector('.urgency-badge')?.textContent.trim(),
            impact: document.querySelectorAll('.analysis-value')[2]?.textContent.trim(),
            root_cause: document.querySelectorAll('.analysis-value')[3]?.textContent.trim(),
            affected_systems: Array.from(document.querySelectorAll('.system-tag')).map(el => el.textContent.trim())
        },
        resolution_plan: {
            summary: document.querySelector('.summary-box p')?.textContent.trim(),
            steps: Array.from(document.querySelectorAll('.timeline-item')).map((item, index) => ({
                order: index + 1,
                description: item.querySelector('h6')?.textContent.trim(),
                type: item.querySelector('.badge')?.textContent.trim(),
                query: item.querySelector('.query-box code')?.textContent.trim() || null
            }))
        },
        exported_at: new Date().toISOString()
    };
    
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(results, null, 2));
    const downloadElement = document.createElement('a');
    downloadElement.setAttribute("href", dataStr);
    downloadElement.setAttribute("download", `incident_analysis_${Date.now()}.json`);
    document.body.appendChild(downloadElement);
    downloadElement.click();
    downloadElement.remove();
    
    // Show success message
    showToast('Results exported successfully!', 'success');
}

// Toast Notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3 shadow-lg`;
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <i class="fas fa-check-circle me-2"></i>
        ${message}
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.5s ease';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

// Smooth Scroll Animation
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.results-card');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1
    });
    
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = `all 0.6s ease ${index * 0.1}s`;
        observer.observe(card);
    });
});

// Copy Incident ID to Clipboard
document.addEventListener('DOMContentLoaded', function() {
    const codeElements = document.querySelectorAll('code');
    codeElements.forEach(code => {
        code.style.cursor = 'pointer';
        code.title = 'Click to copy';
        code.addEventListener('click', function() {
            navigator.clipboard.writeText(this.textContent).then(() => {
                showToast('Incident ID copied to clipboard!', 'success');
            });
        });
    });
});
