// ========== SETTINGS FUNCTIONS ==========

let isFullscreen = false;
let isTabView = false;
let currentTransparency = 0;
let currentBgImage = null;

function toggleFullscreen() {
    const t = translations[currentLang];
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
        isFullscreen = true;
        document.getElementById('fullscreen-status').textContent = t.current_on;
    } else {
        document.exitFullscreen();
        isFullscreen = false;
        document.getElementById('fullscreen-status').textContent = t.current_off;
    }
}

function toggleTabView() {
    isTabView = !isTabView;
    const pages = document.querySelectorAll('.page');
    const t = translations[currentLang];
    
    if (isTabView) {
        pages.forEach(p => p.style.display = 'block');
        document.getElementById('tabview-status').textContent = t.current_tabbed;
    } else {
        pages.forEach(p => {
            if (!p.classList.contains('active')) {
                p.style.display = 'none';
            }
        });
        document.getElementById('tabview-status').textContent = t.current_classic;
    }
}

function applyFontSettings() {
    const font = document.getElementById('font-select').value;
    const size = document.getElementById('font-size-slider').value;
    
    document.body.style.fontFamily = font;
    document.body.style.fontSize = size + 'px';
    document.getElementById('font-size-label').textContent = size + 'px';
    
    localStorage.setItem('ecoshop_font', font);
    localStorage.setItem('ecoshop_fontsize', size);
    
    alert('✅ Font settings applied!');
}

function applyBackgroundSettings() {
    const fileInput = document.getElementById('bg-image-upload');
    const transparency = parseInt(document.getElementById('bg-transparency').value);
    
    currentTransparency = transparency;
    document.getElementById('bg-transparency-label').textContent = transparency + '%';
    
    if (fileInput.files && fileInput.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            currentBgImage = e.target.result;
            applyBackground();
        };
        reader.readAsDataURL(fileInput.files[0]);
    } else if (currentBgImage) {
        applyBackground();
    } else {
        alert('⚠️ Please select an image first!');
    }
}

function applyBackground() {
    if (currentBgImage) {
        const transparency = currentTransparency / 100;
        document.body.style.backgroundImage = `url('${currentBgImage}')`;
        document.body.style.backgroundSize = 'cover';
        document.body.style.backgroundPosition = 'center';
        document.body.style.backgroundAttachment = 'fixed';
        
        const overlay = document.getElementById('bg-overlay');
        if (!overlay) {
            const div = document.createElement('div');
            div.id = 'bg-overlay';
            div.style.position = 'fixed';
            div.style.top = '0';
            div.style.left = '0';
            div.style.width = '100%';
            div.style.height = '100%';
            div.style.zIndex = '-1';
            div.style.pointerEvents = 'none';
            document.body.prepend(div);
        }
        document.getElementById('bg-overlay').style.background = `rgba(255, 255, 255, ${transparency})`;
        
        document.getElementById('bg-status').textContent = 'Current: Custom Image (' + currentTransparency + '% transparency)';
        
        localStorage.setItem('ecoshop_bg', currentBgImage);
        localStorage.setItem('ecoshop_transparency', currentTransparency);
        
        alert('✅ Background applied with ' + currentTransparency + '% transparency!');
    }
}

function resetBackgroundImage() {
    const t = translations[currentLang];
    currentBgImage = null;
    currentTransparency = 0;
    
    document.body.style.backgroundImage = '';
    document.body.style.backgroundSize = '';
    document.body.style.backgroundPosition = '';
    document.body.style.backgroundAttachment = '';
    
    const overlay = document.getElementById('bg-overlay');
    if (overlay) overlay.remove();
    
    document.getElementById('bg-status').textContent = t.current_default;
    document.getElementById('bg-image-upload').value = '';
    document.getElementById('bg-transparency').value = 0;
    document.getElementById('bg-transparency-label').textContent = '0%';
    
    localStorage.removeItem('ecoshop_bg');
    localStorage.removeItem('ecoshop_transparency');
    
    alert('✅ Background reset to default!');
}

function loadSettings() {
    const savedFont = localStorage.getItem('ecoshop_font');
    const savedSize = localStorage.getItem('ecoshop_fontsize');
    if (savedFont) {
        document.body.style.fontFamily = savedFont;
        document.getElementById('font-select').value = savedFont;
    }
    if (savedSize) {
        document.body.style.fontSize = savedSize + 'px';
        document.getElementById('font-size-slider').value = savedSize;
        document.getElementById('font-size-label').textContent = savedSize + 'px';
    }
    
    const savedBg = localStorage.getItem('ecoshop_bg');
    const savedTrans = localStorage.getItem('ecoshop_transparency');
    if (savedBg) {
        currentBgImage = savedBg;
        currentTransparency = parseInt(savedTrans) || 0;
        document.getElementById('bg-transparency').value = currentTransparency;
        document.getElementById('bg-transparency-label').textContent = currentTransparency + '%';
        applyBackground();
    }
}