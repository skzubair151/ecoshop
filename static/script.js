// ============================================================
//  NAVIGATION STYLE TOGGLE
// ============================================================

function changeNavStyle(style) {
    const t = translations[currentLang];
    document.getElementById('nav-style-status').textContent = 
        `Current: ${style === 'topbar' ? t.topbar : t.sidebar}`;
    localStorage.setItem('ecoshop_nav_style', style);
}

function applyNavStyle() {
    const style = document.getElementById('nav-style-select').value;
    const nav = document.getElementById('main-nav');
    const container = document.querySelector('.container');
    const body = document.body;
    const t = translations[currentLang];
    
    if (style === 'sidebar') {
        nav.classList.add('sidebar');
        body.classList.add('sidebar-active');
        localStorage.setItem('ecoshop_nav_style', 'sidebar');
        document.getElementById('nav-style-status').textContent = `Current: ${t.sidebar}`;
    } else {
        nav.classList.remove('sidebar');
        body.classList.remove('sidebar-active');
        localStorage.setItem('ecoshop_nav_style', 'topbar');
        document.getElementById('nav-style-status').textContent = `Current: ${t.topbar}`;
    }
    
    alert(`✅ Navigation style changed to ${style === 'topbar' ? t.topbar : t.sidebar}!`);
}

function loadNavStyle() {
    const saved = localStorage.getItem('ecoshop_nav_style');
    if (saved) {
        document.getElementById('nav-style-select').value = saved;
        applyNavStyle();
    }
}

// ============================================================
//  KEYBOARD SHORTCUTS
// ============================================================
document.addEventListener('keydown', function(e) {
    // F2 - Start new sale (focus on barcode input)
    if (e.key === 'F2') {
        e.preventDefault();
        showTab('sales');
        document.getElementById('scan-barcode').focus();
        document.getElementById('scan-barcode').select();
    }
    
    // F5 - Logout
    if (e.key === 'F5') {
        e.preventDefault();
        if (confirm('Are you sure you want to logout?')) {
            window.location.href = '/logout';
        }
    }
    
    // F1 - Help
    if (e.key === 'F1') {
        e.preventDefault();
        alert('📋 Keyboard Shortcuts:\n\n' +
              'F2 - Start New Sale\n' +
              'F5 - Logout\n' +
              'Enter - Add to Cart (when barcode field focused)\n' +
              'Esc - Clear Cart\n' +
              'Ctrl+Enter - Checkout');
    }
    
    // ESC - Clear Cart
    if (e.key === 'Escape' && document.getElementById('sales').classList.contains('active')) {
        if (cart.length > 0) {
            if (confirm('Clear cart?')) {
                cart = [];
                renderCart();
            }
        }
    }
    
    // Ctrl+Enter - Checkout
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        if (document.getElementById('sales').classList.contains('active') && cart.length > 0) {
            e.preventDefault();
            checkout();
        }
    }
});

// ============================================================
//  BACKUP FUNCTIONS
// ============================================================
function loadBackupStatus() {
    fetch('/api/backup/status')
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                document.getElementById('last-backup-time').textContent = data.last_backup || 'Never';
                document.getElementById('backup-products').textContent = data.stats.products || 0;
                document.getElementById('backup-sales').textContent = data.stats.sales || 0;
                document.getElementById('backup-customers').textContent = data.stats.customers || 0;
                
                const list = document.getElementById('backup-list');
                list.innerHTML = '';
                if (data.backups && data.backups.length > 0) {
                    data.backups.forEach(b => {
                        const li = document.createElement('li');
                        const sizeKB = (b.size / 1024).toFixed(1);
                        li.textContent = `${b.date} (${sizeKB} KB)`;
                        list.appendChild(li);
                    });
                } else {
                    list.innerHTML = '<li style="color:#888;">No backups yet</li>';
                }
            }
        })
        .catch(err => console.error('Backup status error:', err));
}

function createBackup() {
    const btn = document.getElementById('backup-btn');
    const msg = document.getElementById('backup-message');
    
    btn.innerHTML = '⏳ Creating backup...';
    btn.disabled = true;
    msg.innerHTML = '';
    msg.style.color = '#333';
    
    fetch('/api/backup/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            msg.innerHTML = `✅ ${data.message}`;
            msg.style.color = '#43a047';
            loadBackupStatus();
        } else {
            msg.innerHTML = `❌ ${data.message}`;
            msg.style.color = '#e53935';
        }
    })
    .catch(err => {
        msg.innerHTML = `❌ Error: ${err.message}`;
        msg.style.color = '#e53935';
    })
    .finally(() => {
        btn.innerHTML = '📤 Create Backup & Upload to Drive';
        btn.disabled = false;
    });
}

function downloadBackup() {
    window.location.href = '/api/backup/download';
}