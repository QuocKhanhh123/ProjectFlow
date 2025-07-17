function toggleMode() {
    const body = document.body;
    const icon = document.getElementById('mode-icon');
    const toggleButton = document.querySelector('.toggle-mode');
    
    // Add transition effect
    body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
    
    // Toggle mode
    body.classList.toggle('light-mode');
    
    // Update icon and save preference
    if (body.classList.contains('light-mode')) {
        icon.textContent = '☀️';
        localStorage.setItem('theme', 'light');
        toggleButton.setAttribute('title', 'Chuyển sang chế độ tối');
        showThemeNotification('Đã chuyển sang chế độ sáng', 'light');
    } else {
        icon.textContent = '🌙';
        localStorage.setItem('theme', 'dark');
        toggleButton.setAttribute('title', 'Chuyển sang chế độ sáng');
        showThemeNotification('Đã chuyển sang chế độ tối', 'dark');
    }
    
    // Remove transition after animation
    setTimeout(() => {
        body.style.transition = '';
    }, 300);
}

// Initialize theme on page load
function initializeTheme() {
    const theme = localStorage.getItem('theme');
    const body = document.body;
    const icon = document.getElementById('mode-icon');
    const toggleButton = document.querySelector('.toggle-mode');
    
    // Apply theme without transition on initial load
    if (theme === 'light') {
        body.classList.add('light-mode');
        icon.textContent = '☀️';
        toggleButton.setAttribute('title', 'Chuyển sang chế độ tối');
    } else {
        body.classList.remove('light-mode');
        icon.textContent = '🌙';
        toggleButton.setAttribute('title', 'Chuyển sang chế độ sáng');
    }
}

// Show theme change notification
function showThemeNotification(message, theme) {
    const notification = document.createElement('div');
    notification.className = 'theme-notification';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 500;
        z-index: 10000;
        animation: themeSlideDown 0.3s ease-out;
        ${theme === 'light' ? 
            'background: #ffffff; color: #1e293b; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);' : 
            'background: #1f2937; color: #ffffff; border: 1px solid #374151; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);'
        }
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'themeSlideUp 0.3s ease-out forwards';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 1500);
}

// Sidebar toggle functionality
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.querySelector('.sidebar-toggle');
    
    if (!toggleBtn) {
        console.error('Toggle button not found in toggleSidebar');
        return;
    }
    
    sidebar.classList.toggle('collapsed');
    
    // Update button icon and tooltip
    if (sidebar.classList.contains('collapsed')) {
        toggleBtn.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
        toggleBtn.setAttribute('title', 'Mở rộng sidebar');
        localStorage.setItem('sidebarCollapsed', 'true');
    } else {
        toggleBtn.innerHTML = '<i class="fa-solid fa-bars"></i>';
        toggleBtn.setAttribute('title', 'Thu gọn sidebar');
        localStorage.setItem('sidebarCollapsed', 'false');
    }
}

// Initialize sidebar state
function initializeSidebar() {
    const sidebarCollapsed = localStorage.getItem('sidebarCollapsed');
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.querySelector('.sidebar-toggle');
    
    if (!toggleBtn || !sidebar) {
        console.error('Sidebar elements not found');
        return;
    }
    
    // Check if already initialized to prevent re-initialization
    if (sidebar.classList.contains('initialized')) {
        return;
    }
    
    // Apply state without transition first
    sidebar.style.transition = 'none';
    
    if (sidebarCollapsed === 'true') {
        sidebar.classList.add('collapsed');
        toggleBtn.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
        toggleBtn.setAttribute('title', 'Mở rộng sidebar');
    } else {
        sidebar.classList.remove('collapsed');
        toggleBtn.innerHTML = '<i class="fa-solid fa-bars"></i>';
        toggleBtn.setAttribute('title', 'Thu gọn sidebar');
    }
    
    // Mark as initialized and restore transitions
    sidebar.classList.add('initialized');
    
    // Restore transitions after a brief delay
    setTimeout(() => {
        sidebar.style.transition = '';
    }, 50);
}

// Update window.onload to use new functions
window.onload = function() {
    initializeTheme();
    initializeSidebar();
}

// Handle DOMContentLoaded for faster initialization
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    initializeSidebar();
});

function toggleUserMenu() {
    const menu = document.getElementById('user-menu');
    menu.classList.toggle('show');
}

window.onclick = function(event) {
    const userBtn = event.target.closest('.user-btn');
    if (!userBtn) {
        var dropdowns = document.getElementsByClassName("user-menu");
        for (var i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (openDropdown.classList.contains('show')) {
                openDropdown.classList.remove('show');
            }
        }
    }
}

// Search functionality
function performSearch() {
    const searchInput = document.getElementById('search-input');
    const query = searchInput.value.trim();
    
    if (query === '') {
        showSearchNotification('Vui lòng nhập từ khóa tìm kiếm', 'warning');
        return;
    }
    
    // Show loading state
    const searchBtn = document.querySelector('.search-btn');
    const originalContent = searchBtn.innerHTML;
    searchBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    searchBtn.disabled = true;
    
    // Perform search
    fetch(`/dashboard/search/?q=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displaySearchResults(data.results, query);
        } else {
            showSearchNotification('Có lỗi xảy ra khi tìm kiếm', 'error');
        }
    })
    .catch(error => {
        console.error('Search error:', error);
        showSearchNotification('Có lỗi xảy ra khi tìm kiếm', 'error');
    })
    .finally(() => {
        // Restore button state
        searchBtn.innerHTML = originalContent;
        searchBtn.disabled = false;
    });
}

// Handle Enter key in search input
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
});

// Display search results in modal
function displaySearchResults(results, query) {
    // Remove existing search modal if any
    const existingModal = document.getElementById('search-results-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create search results modal
    const modal = document.createElement('div');
    modal.id = 'search-results-modal';
    modal.className = 'search-modal-overlay';
    
    let projectsHtml = '';
    let tasksHtml = '';
    
    if (results.projects && results.projects.length > 0) {
        projectsHtml = `
            <div class="search-section">
                <h3><i class="fa-solid fa-folder"></i> Dự án (${results.projects.length})</h3>
                <div class="search-items">
                    ${results.projects.map(project => `
                        <div class="search-item" onclick="window.location.href='/dashboard/projects/${project.id}/'">
                            <div class="search-item-icon">
                                <i class="fa-solid fa-folder"></i>
                            </div>
                            <div class="search-item-content">
                                <div class="search-item-title">${project.name}</div>
                                <div class="search-item-desc">${project.description}</div>
                                <div class="search-item-meta">
                                    <span class="status status-${project.status.toLowerCase()}">${getStatusText(project.status)}</span>
                                    <span class="date">${formatDate(project.created_at)}</span>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    if (results.tasks && results.tasks.length > 0) {
        tasksHtml = `
            <div class="search-section">
                <h3><i class="fa-solid fa-tasks"></i> Công việc (${results.tasks.length})</h3>
                <div class="search-items">
                    ${results.tasks.map(task => `
                        <div class="search-item" onclick="window.location.href='/dashboard/projects/${task.project_id}/tasks/${task.id}/'">
                            <div class="search-item-icon">
                                <i class="fa-solid fa-tasks"></i>
                            </div>
                            <div class="search-item-content">
                                <div class="search-item-title">${task.title}</div>
                                <div class="search-item-desc">${task.description || 'Không có mô tả'}</div>
                                <div class="search-item-meta">
                                    <span class="project-name">${task.project_name}</span>
                                    <span class="status status-${task.status.toLowerCase()}">${getTaskStatusText(task.status)}</span>
                                    <span class="priority priority-${task.priority.toLowerCase()}">${getPriorityText(task.priority)}</span>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    const totalResults = (results.projects?.length || 0) + (results.tasks?.length || 0);
    
    modal.innerHTML = `
        <div class="search-modal-content">
            <div class="search-modal-header">
                <h2>Kết quả tìm kiếm cho "${query}"</h2>
                <span class="search-modal-close" onclick="closeSearchModal()">&times;</span>
            </div>
            <div class="search-modal-body">
                ${totalResults > 0 ? 
                    projectsHtml + tasksHtml : 
                    '<div class="no-search-results"><i class="fa-solid fa-search"></i><p>Không tìm thấy kết quả nào</p></div>'
                }
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';
    
    // Close modal when clicking outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeSearchModal();
        }
    });
}

// Close search modal
function closeSearchModal() {
    const modal = document.getElementById('search-results-modal');
    if (modal) {
        modal.remove();
        document.body.style.overflow = 'auto';
    }
}

// Helper functions
function getStatusText(status) {
    const statusMap = {
        'ACTIVE': 'Đang hoạt động',
        'COMPLETED': 'Hoàn thành',
        'ON_HOLD': 'Tạm dừng'
    };
    return statusMap[status] || status;
}

function getTaskStatusText(status) {
    const statusMap = {
        'TODO': 'Cần làm',
        'IN_PROGRESS': 'Đang thực hiện',
        'DONE': 'Hoàn thành'
    };
    return statusMap[status] || status;
}

function getPriorityText(priority) {
    const priorityMap = {
        'HIGH': 'Cao',
        'MEDIUM': 'Trung bình',
        'LOW': 'Thấp'
    };
    return priorityMap[priority] || priority;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN');
}

function showSearchNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `search-notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 6px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
        ${type === 'success' ? 'background: #059669;' : 
          type === 'warning' ? 'background: #d97706;' : 'background: #dc2626;'}
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

