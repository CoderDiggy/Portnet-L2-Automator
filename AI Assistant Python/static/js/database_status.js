/**
 * Database Status Page JavaScript
 */

// Filter state
let kbFilters = { categories: [], sort: 'newest' };
let tdFilters = { urgency: [], sort: 'newest' };

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeFilters();
    populateKBCategories();
    setupUrgencyCheckboxes();
});

// ========================================
// INITIALIZATION
// ========================================

function initializeFilters() {
    // Prevent dropdowns from closing when clicking inside
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
}

// ========================================
// KNOWLEDGE BASE FILTERS
// ========================================

function populateKBCategories() {
    const rows = document.querySelectorAll('#kbTable tbody tr');
    const categories = new Set();
    
    rows.forEach(row => {
        const cat = row.dataset.category;
        if (cat && cat !== 'none') {
            categories.add(cat);
        }
    });
    
    const container = document.getElementById('kbCategoryFilters');
    if (!container) return;
    
    // Add "All" checkbox
    container.innerHTML = `
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="kbCatAll" value="all" checked>
            <label class="form-check-label" for="kbCatAll">All Categories</label>
        </div>
    `;
    
    // Add individual categories
    categories.forEach((cat, index) => {
        const div = document.createElement('div');
        div.className = 'form-check';
        div.innerHTML = `
            <input class="form-check-input kb-cat-cb" type="checkbox" id="kbCat${index}" value="${cat}">
            <label class="form-check-label" for="kbCat${index}">${cat}</label>
        `;
        container.appendChild(div);
    });
    
    // Setup "All" checkbox logic
    const allCheckbox = document.getElementById('kbCatAll');
    const catCheckboxes = document.querySelectorAll('.kb-cat-cb');
    
    allCheckbox.addEventListener('change', function() {
        if (this.checked) {
            catCheckboxes.forEach(cb => cb.checked = false);
        }
    });
    
    catCheckboxes.forEach(cb => {
        cb.addEventListener('change', function() {
            if (this.checked) {
                allCheckbox.checked = false;
            }
        });
    });
}

function applyKBFilters() {
    // Get selected categories
    const catCheckboxes = document.querySelectorAll('.kb-cat-cb:checked');
    kbFilters.categories = Array.from(catCheckboxes).map(cb => cb.value);
    
    // Get sort order
    const sortRadio = document.querySelector('input[name="kbSort"]:checked');
    kbFilters.sort = sortRadio ? sortRadio.value : 'newest';
    
    // Filter and sort table
    filterKBTable();
    
    // Update badge
    updateKBBadge();
    
    // Close dropdown
    const dropdown = bootstrap.Dropdown.getInstance(document.getElementById('kbFilterBtn'));
    if (dropdown) dropdown.hide();
    
    showToast('Filters applied successfully', 'success');
}

function filterKBTable() {
    const tbody = document.querySelector('#kbTable tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    let visibleCount = 0;
    
    // Sort rows
    rows.sort((a, b) => {
        const dateA = new Date(a.dataset.date || 0);
        const dateB = new Date(b.dataset.date || 0);
        return kbFilters.sort === 'newest' ? dateB - dateA : dateA - dateB;
    });
    
    // Clear and re-append
    tbody.innerHTML = '';
    
    rows.forEach(row => {
        const cat = row.dataset.category;
        const showByCategory = kbFilters.categories.length === 0 || kbFilters.categories.includes(cat);
        
        if (showByCategory) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
        
        tbody.appendChild(row);
    });
    
    // Update visible count
    document.getElementById('kb-visible').textContent = visibleCount;
}

function clearKBFilters() {
    // Reset checkboxes
    document.getElementById('kbCatAll').checked = true;
    document.querySelectorAll('.kb-cat-cb').forEach(cb => cb.checked = false);
    
    // Reset sort
    document.getElementById('kbNewest').checked = true;
    
    // Reset filter state
    kbFilters = { categories: [], sort: 'newest' };
    
    // Show all rows
    const rows = document.querySelectorAll('#kbTable tbody tr');
    rows.forEach(row => row.style.display = '');
    
    // Update count
    document.getElementById('kb-visible').textContent = rows.length;
    
    // Update badge
    updateKBBadge();
    
    showToast('Filters cleared', 'info');
}

function updateKBBadge() {
    let count = kbFilters.categories.length;
    if (kbFilters.sort !== 'newest') count++;
    
    const badge = document.querySelector('.kb-filter-count');
    const btn = document.getElementById('kbFilterBtn');
    
    if (count > 0) {
        badge.textContent = count;
        badge.style.display = 'inline';
    } else {
        badge.style.display = 'none';
    }
}

// ========================================
// TRAINING DATA FILTERS
// ========================================

function setupUrgencyCheckboxes() {
    const allCheckbox = document.getElementById('tdUrgAll');
    const urgencyCheckboxes = document.querySelectorAll('.td-urgency-cb');
    
    if (!allCheckbox) return;
    
    allCheckbox.addEventListener('change', function() {
        if (this.checked) {
            urgencyCheckboxes.forEach(cb => cb.checked = false);
        }
    });
    
    urgencyCheckboxes.forEach(cb => {
        cb.addEventListener('change', function() {
            if (this.checked) {
                allCheckbox.checked = false;
            }
        });
    });
}

function applyTDFilters() {
    // Get selected urgency levels
    const urgencyCheckboxes = document.querySelectorAll('.td-urgency-cb:checked');
    tdFilters.urgency = Array.from(urgencyCheckboxes).map(cb => cb.value);
    
    // Get sort order
    const sortRadio = document.querySelector('input[name="tdSort"]:checked');
    tdFilters.sort = sortRadio ? sortRadio.value : 'newest';
    
    // Filter and sort table
    filterTDTable();
    
    // Update badge
    updateTDBadge();
    
    // Close dropdown
    const dropdown = bootstrap.Dropdown.getInstance(document.getElementById('tdFilterBtn'));
    if (dropdown) dropdown.hide();
    
    showToast('Filters applied successfully', 'success');
}

function filterTDTable() {
    const tbody = document.querySelector('#tdTable tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    let visibleCount = 0;
    
    // Sort rows
    rows.sort((a, b) => {
        const dateA = new Date(a.dataset.date || 0);
        const dateB = new Date(b.dataset.date || 0);
        return tdFilters.sort === 'newest' ? dateB - dateA : dateA - dateB;
    });
    
    // Clear and re-append
    tbody.innerHTML = '';
    
    rows.forEach(row => {
        const urgency = row.dataset.urgency;
        const showByUrgency = tdFilters.urgency.length === 0 || tdFilters.urgency.includes(urgency);
        
        if (showByUrgency) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
        
        tbody.appendChild(row);
    });
    
    // Update visible count
    document.getElementById('td-visible').textContent = visibleCount;
}

function clearTDFilters() {
    // Reset checkboxes
    document.getElementById('tdUrgAll').checked = true;
    document.querySelectorAll('.td-urgency-cb').forEach(cb => cb.checked = false);
    
    // Reset sort
    document.getElementById('tdNewest').checked = true;
    
    // Reset filter state
    tdFilters = { urgency: [], sort: 'newest' };
    
    // Show all rows
    const rows = document.querySelectorAll('#tdTable tbody tr');
    rows.forEach(row => row.style.display = '');
    
    // Update count
    document.getElementById('td-visible').textContent = rows.length;
    
    // Update badge
    updateTDBadge();
    
    showToast('Filters cleared', 'info');
}

function updateTDBadge() {
    let count = tdFilters.urgency.length;
    if (tdFilters.sort !== 'newest') count++;
    
    const badge = document.querySelector('.td-filter-count');
    const btn = document.getElementById('tdFilterBtn');
    
    if (count > 0) {
        badge.textContent = count;
        badge.style.display = 'inline';
    } else {
        badge.style.display = 'none';
    }
}

// ========================================
// UTILITIES
// ========================================

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3 shadow-lg`;
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
        ${message}
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.5s ease';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

// Add to the initialization section
document.addEventListener('DOMContentLoaded', function() {
    initializeFilters();
    populateKBCategories();
    setupUrgencyCheckboxes();
    setupDropdownArrows(); // Add this line
});

// Add this new function
function setupDropdownArrows() {
    // Track dropdown state for both filters
    const kbDropdown = document.getElementById('kbFilterBtn');
    const tdDropdown = document.getElementById('tdFilterBtn');
    
    if (kbDropdown) {
        kbDropdown.addEventListener('shown.bs.dropdown', function() {
            this.closest('.dropdown').classList.add('show');
        });
        
        kbDropdown.addEventListener('hidden.bs.dropdown', function() {
            this.closest('.dropdown').classList.remove('show');
        });
    }
    
    if (tdDropdown) {
        tdDropdown.addEventListener('shown.bs.dropdown', function() {
            this.closest('.dropdown').classList.add('show');
        });
        
        tdDropdown.addEventListener('hidden.bs.dropdown', function() {
            this.closest('.dropdown').classList.remove('show');
        });
    }
}




console.log('Database Status JS loaded');
