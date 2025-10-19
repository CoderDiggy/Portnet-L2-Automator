/**
 * Training Data Page JavaScript
 */

// Filter state
let filters = {
    urgency: [],
    categories: [],
    sortBy: 'newest',
    searchTerm: ''
};

let deleteTrainingId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeFilters();
    populateCategories();
    calculateStats();
    setupSearch();
    setupDropdownArrows();
});

// ========================================
// INITIALIZATION
// ========================================

function initializeFilters() {
    // Prevent dropdown from closing when clicking inside
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
    
    // Setup urgency "All" checkbox logic
    setupUrgencyCheckboxes();
}

function setupUrgencyCheckboxes() {
    const allCb = document.getElementById('urgAll');
    const urgencyCbs = document.querySelectorAll('.urgency-cb');
    
    if (!allCb) return;
    
    allCb.addEventListener('change', function() {
        if (this.checked) {
            urgencyCbs.forEach(cb => cb.checked = false);
        }
    });
    
    urgencyCbs.forEach(cb => {
        cb.addEventListener('change', function() {
            if (this.checked) {
                allCb.checked = false;
            }
        });
    });
}

function setupDropdownArrows() {
    const btn = document.getElementById('tdFilterBtn');
    if (!btn) return;
    
    btn.addEventListener('shown.bs.dropdown', function() {
        this.closest('.dropdown').classList.add('show');
    });
    
    btn.addEventListener('hidden.bs.dropdown', function() {
        this.closest('.dropdown').classList.remove('show');
    });
}

// ========================================
// POPULATE CATEGORIES
// ========================================

function populateCategories() {
    const items = document.querySelectorAll('.training-item');
    const categories = new Set();
    
    items.forEach(item => {
        const cat = item.dataset.category;
        if (cat && cat !== 'none') {
            categories.add(cat);
        }
    });
    
    const container = document.getElementById('categoryFilters');
    if (!container) return;
    
    // Add "All Categories" option
    container.innerHTML = `
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="catAll" value="all" checked>
            <label class="form-check-label" for="catAll">All Categories</label>
        </div>
    `;
    
    // Add individual categories
    let index = 0;
    categories.forEach(cat => {
        const div = document.createElement('div');
        div.className = 'form-check';
        div.innerHTML = `
            <input class="form-check-input category-cb" type="checkbox" id="cat${index}" value="${cat}">
            <label class="form-check-label" for="cat${index}">${cat}</label>
        `;
        container.appendChild(div);
        index++;
    });
    
    // Setup "All" checkbox logic
    const allCb = document.getElementById('catAll');
    const catCbs = document.querySelectorAll('.category-cb');
    
    allCb.addEventListener('change', function() {
        if (this.checked) {
            catCbs.forEach(cb => cb.checked = false);
        }
    });
    
    catCbs.forEach(cb => {
        cb.addEventListener('change', function() {
            if (this.checked) {
                allCb.checked = false;
            }
        });
    });
}

// ========================================
// SEARCH FUNCTIONALITY
// ========================================

function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        filters.searchTerm = this.value.toLowerCase();
        filterItems();
    });
}

// ========================================
// APPLY FILTERS
// ========================================

function applyFilters() {
    // Get selected urgency levels
    const urgencyCbs = document.querySelectorAll('.urgency-cb:checked');
    filters.urgency = Array.from(urgencyCbs).map(cb => cb.value);
    
    // Get selected categories
    const catCbs = document.querySelectorAll('.category-cb:checked');
    filters.categories = Array.from(catCbs).map(cb => cb.value);
    
    // Get sort order
    const sortRadio = document.querySelector('input[name="sortBy"]:checked');
    filters.sortBy = sortRadio ? sortRadio.value : 'newest';
    
    // Filter and sort
    filterItems();
    
    // Update badge
    updateFilterBadge();
    
    // Close dropdown
    const dropdown = bootstrap.Dropdown.getInstance(document.getElementById('tdFilterBtn'));
    if (dropdown) dropdown.hide();
    
    showToast('Filters applied successfully', 'success');
}

// ========================================
// FILTER ITEMS
// ========================================

function filterItems() {
    const grid = document.getElementById('trainingGrid');
    const items = Array.from(document.querySelectorAll('.training-item'));
    let visibleCount = 0;
    
    // Sort items
    items.sort((a, b) => {
        const dateA = new Date(a.dataset.date || 0);
        const dateB = new Date(b.dataset.date || 0);
        return filters.sortBy === 'newest' ? dateB - dateA : dateA - dateB;
    });
    
    // Clear grid
    grid.innerHTML = '';
    
    // Filter and re-append items
    items.forEach(item => {
        const urgency = item.dataset.urgency;
        const category = item.dataset.category;
        const incident = item.dataset.incident;
        
        const matchesUrgency = filters.urgency.length === 0 || filters.urgency.includes(urgency);
        const matchesCategory = filters.categories.length === 0 || filters.categories.includes(category);
        const matchesSearch = filters.searchTerm === '' || incident.includes(filters.searchTerm);
        
        if (matchesUrgency && matchesCategory && matchesSearch) {
            item.style.display = '';
            visibleCount++;
        } else {
            item.style.display = 'none';
        }
        
        grid.appendChild(item);
    });
    
    // Update visible count
    document.getElementById('visibleCount').textContent = visibleCount;
    
    // Show/hide no results message
    const noResults = document.getElementById('noResults');
    if (visibleCount === 0) {
        noResults.style.display = 'block';
        grid.style.display = 'none';
    } else {
        noResults.style.display = 'none';
        grid.style.display = '';
    }
}

// ========================================
// CLEAR FILTERS
// ========================================

function clearAllFilters() {
    // Reset urgency
    document.getElementById('urgAll').checked = true;
    document.querySelectorAll('.urgency-cb').forEach(cb => cb.checked = false);
    
    // Reset categories
    document.getElementById('catAll').checked = true;
    document.querySelectorAll('.category-cb').forEach(cb => cb.checked = false);
    
    // Reset sort
    document.getElementById('sortNewest').checked = true;
    
    // Reset search
    const searchInput = document.getElementById('searchInput');
    if (searchInput) searchInput.value = '';
    
    // Reset filter state
    filters = {
        urgency: [],
        categories: [],
        sortBy: 'newest',
        searchTerm: ''
    };
    
    // Show all items
    const items = document.querySelectorAll('.training-item');
    items.forEach(item => item.style.display = '');
    
    // Update counts
    document.getElementById('visibleCount').textContent = items.length;
    
    // Hide no results
    document.getElementById('noResults').style.display = 'none';
    document.getElementById('trainingGrid').style.display = '';
    
    // Update badge
    updateFilterBadge();
    
    showToast('Filters cleared', 'info');
}

// ========================================
// UPDATE FILTER BADGE
// ========================================

function updateFilterBadge() {
    let count = filters.urgency.length + filters.categories.length;
    if (filters.sortBy !== 'newest') count++;
    if (filters.searchTerm !== '') count++;
    
    const badge = document.querySelector('.filter-count');
    if (count > 0) {
        badge.textContent = count;
        badge.style.display = 'inline';
    } else {
        badge.style.display = 'none';
    }
}

// ========================================
// CALCULATE STATISTICS
// ========================================

function calculateStats() {
    const items = document.querySelectorAll('.training-item');
    const categories = new Set();
    let criticalCount = 0;
    
    items.forEach(item => {
        const cat = item.dataset.category;
        if (cat && cat !== 'none') {
            categories.add(cat);
        }
        
        const urgency = item.dataset.urgency;
        if (urgency === 'Critical') {
            criticalCount++;
        }
    });
    
    document.getElementById('categoryCount').textContent = categories.size;
    document.getElementById('criticalCount').textContent = criticalCount;
}

// ========================================
// DELETE TRAINING DATA
// ========================================

function deleteTraining(id, name) {
    deleteTrainingId = id;
    document.getElementById('deleteItemName').textContent = name;
    new bootstrap.Modal(document.getElementById('deleteModal')).show();
}

document.getElementById('confirmDeleteBtn')?.addEventListener('click', function() {
    if (deleteTrainingId) {
        this.disabled = true;
        this.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Deleting...';
        
        fetch(`/api/training/${deleteTrainingId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (response.ok) {
                showToast('Training data deleted successfully', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                showToast('Error deleting training data', 'danger');
                this.disabled = false;
                this.innerHTML = '<i class="fas fa-trash me-1"></i>Delete';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error deleting training data', 'danger');
            this.disabled = false;
            this.innerHTML = '<i class="fas fa-trash me-1"></i>Delete';
        });
    }
});

// ========================================
// TOAST NOTIFICATION
// ========================================

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3 shadow-lg`;
    toast.style.zIndex = '9999';
    toast.style.minWidth = '300px';
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
        ${message}
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.5s ease';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

console.log('Training Data JS loaded');
