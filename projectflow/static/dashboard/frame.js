function toggleMode() {
    const body = document.body;
    const icon = document.getElementById('mode-icon');
    body.classList.toggle('light-mode');
    if (body.classList.contains('light-mode')) {
        icon.textContent = '☀️';
        localStorage.setItem('theme', 'light');
    } else {
        icon.textContent = '🌙';
        localStorage.setItem('theme', 'dark');
    }
}
// Tự động lưu trạng thái theme
window.onload = function() {
    const theme = localStorage.getItem('theme');
    const body = document.body;
    const icon = document.getElementById('mode-icon');
    if (theme === 'light') {
        body.classList.add('light-mode');
        icon.textContent = '☀️';
    } else {
        body.classList.remove('light-mode');
        icon.textContent = '🌙';
    }
}
function toggleUserMenu() {
    const menu = document.getElementById('user-menu');
    menu.classList.toggle('show');
}
window.onclick = function(event) {
    if (!event.target.matches('.user-btn')) {
        var dropdowns = document.getElementsByClassName("user-menu");
        for (var i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (openDropdown.classList.contains('show')) {
                openDropdown.classList.remove('show');
            }
        }
    }
}
function showContent(section) {
    const sections = ['overview', 'projects', 'members', 'settings'];
    sections.forEach(s => {
        document.getElementById(s + '-content').classList.remove('active');
        document.querySelector('.sidebar-menu li[onclick*="' + s + '"]').classList.remove('active');
    });
    document.getElementById(section + '-content').classList.add('active');
    document.querySelector('.sidebar-menu li[onclick*="' + section + '"]').classList.add('active');
}
showContent('projects');
