/* ==============================================
   DOCUMATICA V12.0 - MAIN JAVASCRIPT
   ============================================== */

// Preloader
window.addEventListener('load', () => {
  setTimeout(() => {
    const preloader = document.getElementById('preloader');
    if (preloader) {
      preloader.classList.add('hidden');
    }
  }, 2500);
});

// Restart preloader (for demo)
function restartPreloader() {
  const preloader = document.getElementById('preloader');
  if (!preloader) return;
  
  preloader.classList.remove('hidden');
  
  // Recreate SVG to restart animation
  const logo = preloader.querySelector('.preloader-logo svg');
  if (logo) {
    const newLogo = logo.cloneNode(true);
    logo.parentNode.replaceChild(newLogo, logo);
  }
  
  setTimeout(() => {
    preloader.classList.add('hidden');
  }, 3000);
}

// Smooth scroll for navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  });
});

// Page Transitions (smooth page transitions)
function setupPageTransitions() {
  // Check View Transitions API support
  const supportsViewTransitions = 'startViewTransition' in document;
  
  // Intercept clicks on internal links
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a');
    
    // Ignore clicks on buttons or inside buttons
    if (e.target.closest('button')) return;
    
    // Check that it's an internal link (not anchor, not external)
    if (!link || !link.href || link.href.startsWith('#') || link.target === '_blank') return;
    if (link.origin !== location.origin) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey) return; // Ignore with modifiers
    
    e.preventDefault();
    const targetUrl = link.href;
    
    if (supportsViewTransitions) {
      // Use View Transitions API
      document.startViewTransition(() => {
        window.location.href = targetUrl;
      });
    } else {
      // Fallback: simple fade animation
      document.body.style.opacity = '0';
      setTimeout(() => {
        window.location.href = targetUrl;
      }, 150);
    }
  });
  
  // Fade-in animation on page load
  if (!supportsViewTransitions) {
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.3s ease';
    
    window.addEventListener('load', () => {
      setTimeout(() => {
        document.body.style.opacity = '1';
      }, 50);
    });
  }
}

// Export for global use
if (typeof window !== 'undefined') {
  window.restartPreloader = restartPreloader;
}

// ============================================
// PRICING TOGGLE (Monthly/Annual)
// ============================================
function initPricingToggle() {
  const billingToggle = document.getElementById('billingToggle');
  if (!billingToggle) return; // Exit if not on pricing page
  
  const monthlyLabel = document.getElementById('monthlyLabel');
  const annualLabel = document.getElementById('annualLabel');
  const priceValues = document.querySelectorAll('.pricing-value[data-monthly]');
  
  let isAnnual = false;
  
  function animatePriceChange(element, newValue) {
    // Scale down and fade out
    element.style.transform = 'scale(0.8)';
    element.style.opacity = '0';
    
    setTimeout(() => {
      element.textContent = newValue;
      // Scale up and fade in
      element.style.transform = 'scale(1)';
      element.style.opacity = '1';
    }, 200);
  }
  
  function togglePricing() {
    isAnnual = !isAnnual;
    
    // Toggle switch
    billingToggle.classList.toggle('active');
    
    // Toggle labels
    monthlyLabel.classList.toggle('active');
    annualLabel.classList.toggle('active');
    
    // Animate price changes
    priceValues.forEach(element => {
      const monthly = element.getAttribute('data-monthly');
      const annual = element.getAttribute('data-annual');
      const newPrice = isAnnual ? annual : monthly;
      
      animatePriceChange(element, newPrice);
    });
  }
  
  // Event listeners
  billingToggle.addEventListener('click', togglePricing);
  monthlyLabel.addEventListener('click', () => {
    if (isAnnual) togglePricing();
  });
  annualLabel.addEventListener('click', () => {
    if (!isAnnual) togglePricing();
  });
}

// Initialize pricing toggle when DOM is ready
document.addEventListener('DOMContentLoaded', initPricingToggle);

// ============================================
// MOBILE NAVIGATION TOGGLE
// ============================================
function initMobileNav() {
  const navbarToggle = document.getElementById('navbarToggle');
  const navbarMobileMenu = document.getElementById('navbarMobileMenu');

  if (navbarToggle && navbarMobileMenu) {
    navbarToggle.addEventListener('click', () => {
      navbarToggle.classList.toggle('active');
      navbarMobileMenu.classList.toggle('active');
    });

    const mobileLinks = navbarMobileMenu.querySelectorAll('.navbar-mobile-nav-link');
    mobileLinks.forEach(link => {
      link.addEventListener('click', () => {
        navbarToggle.classList.remove('active');
        navbarMobileMenu.classList.remove('active');
      });
    });
  }
}

// ============================================
// TABS SYSTEM
// ============================================
function initTabs(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const triggers = container.querySelectorAll('.tab');
  const panels = container.querySelectorAll('.tab-panel');

  triggers.forEach(trigger => {
    trigger.addEventListener('click', () => {
      const targetId = trigger.getAttribute('data-tab');

      // Remove active from all
      triggers.forEach(t => t.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));

      // Add active to clicked
      trigger.classList.add('active');
      const targetPanel = container.querySelector(`#${targetId}`);
      if (targetPanel) targetPanel.classList.add('active');
    });
  });
}

// Auto-initialize all tabs on page
function initAllTabs() {
  document.querySelectorAll('.tabs').forEach(container => {
    if (container.id) {
      initTabs(container.id);
    }
  });
}

// ============================================
// ACCORDION SYSTEM
// ============================================
function initAccordion(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  // Get only direct children accordion items (not nested ones)
  const items = Array.from(container.children).filter(el => el.classList.contains('accordion-item'));

  items.forEach(item => {
    const header = item.querySelector(':scope > .accordion-header');
    const content = item.querySelector(':scope > .accordion-content');
    
    // Set initial height for active items
    if (item.classList.contains('active')) {
      content.style.maxHeight = content.scrollHeight + 'px';
    } else {
      content.style.maxHeight = '0';
    }
    
    // Store observer for nested content changes
    let observerTimeout;
    item._observer = new MutationObserver(() => {
      if (item.classList.contains('active') && !item._closing && !item._opening) {
        clearTimeout(observerTimeout);
        observerTimeout = setTimeout(() => {
          content.style.maxHeight = content.scrollHeight + 'px';
          updateParentHeights(item);
        }, 50);
      }
    });
    
    item._observer.observe(content, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['class']
    });
    
    header.addEventListener('click', (e) => {
      e.stopPropagation();
      
      const isActive = item.classList.contains('active');
      
      if (isActive) {
        // Close
        item._closing = true;
        item.classList.remove('active');
        content.style.maxHeight = '0';
        
        setTimeout(() => {
          item._closing = false;
          updateParentHeights(item);
        }, 400);
      } else {
        // Close others
        items.forEach(i => {
          if (i !== item && i.classList.contains('active')) {
            i._closing = true;
            i.classList.remove('active');
            const iContent = i.querySelector(':scope > .accordion-content');
            iContent.style.maxHeight = '0';
            setTimeout(() => { i._closing = false; }, 400);
          }
        });
        
        // Open this
        item._opening = true;
        item.classList.add('active');
        content.style.maxHeight = content.scrollHeight + 'px';
        
        setTimeout(() => {
          item._opening = false;
          updateParentHeights(item);
        }, 450);
      }
    });
  });
}

// Update parent accordion heights (bottom-up)
function updateParentHeights(element) {
  let parent = element.parentElement;
  const parentsToUpdate = [];
  
  // Collect all parent accordion contents
  while (parent) {
    if (parent.classList.contains('accordion-content') && parent.parentElement.classList.contains('active')) {
      parentsToUpdate.push(parent);
    }
    parent = parent.parentElement;
  }
  
  // Update from bottom to top
  parentsToUpdate.forEach(parentContent => {
    parentContent.style.maxHeight = parentContent.scrollHeight + 'px';
  });
}

// Auto-initialize all accordions on page
function initAllAccordions() {
  // Initialize nested accordions first (bottom-up)
  initAccordion('nestedUtilities');
  initAccordion('nestedComponents');
  initAccordion('nestedAccordion');
  initAccordion('darkAccordion');
  initAccordion('iconAccordion');
  initAccordion('separatedAccordion');
  initAccordion('borderedAccordion');
  initAccordion('basicAccordion');
  
  // Update all heights after initialization
  setTimeout(() => {
    const activeItems = document.querySelectorAll('.accordion-item.active');
    activeItems.forEach(item => {
      const content = item.querySelector(':scope > .accordion-content');
      if (content) {
        content.style.maxHeight = 'none';
        const height = content.scrollHeight;
        content.style.maxHeight = height + 'px';
      }
    });
    
    // Update parent heights from bottom to top (multiple passes for deep nesting)
    setTimeout(() => {
      activeItems.forEach(item => updateParentHeights(item));
    }, 50);
    
    setTimeout(() => {
      activeItems.forEach(item => updateParentHeights(item));
    }, 150);
  }, 100);
}

// ============================================
// MODAL SYSTEM
// ============================================
function initModals() {
  // Open modal
  document.querySelectorAll('[data-modal]').forEach(trigger => {
    trigger.addEventListener('click', () => {
      const modalId = trigger.getAttribute('data-modal');
      const modal = document.getElementById(modalId);
      if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
      }
    });
  });

  // Close modal
  document.querySelectorAll('[data-modal-close]').forEach(closeBtn => {
    closeBtn.addEventListener('click', () => {
      const modalId = closeBtn.getAttribute('data-modal-close');
      const modal = document.getElementById(modalId);
      if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  });

  // Close on backdrop click
  document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        backdrop.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  });

  // Close on ESC key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-backdrop.active').forEach(modal => {
        modal.classList.remove('active');
        document.body.style.overflow = '';
      });
    }
  });
}

// ============================================
// RANGE SLIDERS (Dual Handle)
// ============================================
function initRangeSliders() {
  document.querySelectorAll('[data-range-slider]').forEach(slider => {
    const minInput = slider.querySelector('[data-range-min]');
    const maxInput = slider.querySelector('[data-range-max]');
    const fill = slider.querySelector('.range-slider__fill');
    const valueMin = slider.parentElement.querySelector('[data-value-min]');
    const valueMax = slider.parentElement.querySelector('[data-value-max]');
    
    if (!minInput || !maxInput || !fill) return;
    
    const min = parseFloat(minInput.min);
    const max = parseFloat(maxInput.max);
    
    function updateSlider() {
      let minVal = parseFloat(minInput.value);
      let maxVal = parseFloat(maxInput.value);
      
      // Prevent crossing
      if (maxVal - minVal < 0) {
        if (this === minInput) {
          minInput.value = maxVal;
          minVal = maxVal;
        } else {
          maxInput.value = minVal;
          maxVal = minVal;
        }
      }
      
      // Calculate percentages
      const minPercent = ((minVal - min) / (max - min)) * 100;
      const maxPercent = ((maxVal - min) / (max - min)) * 100;
      
      // Update fill position
      fill.style.left = minPercent + '%';
      fill.style.width = (maxPercent - minPercent) + '%';
      
      // Update values display
      if (valueMin) {
        valueMin.textContent = formatValue(minVal, minInput);
      }
      if (valueMax) {
        valueMax.textContent = formatValue(maxVal, maxInput);
      }
    }
    
    function formatValue(val, input) {
      const step = parseFloat(input.step) || 1;
      const maxVal = parseFloat(input.max);
      
      // Format based on value range
      if (maxVal >= 100000) {
        return '$' + (val / 1000).toFixed(0) + 'K';
      } else if (maxVal >= 1000) {
        return '$' + val.toFixed(0);
      } else {
        return '$' + val.toFixed(0);
      }
    }
    
    minInput.addEventListener('input', updateSlider);
    maxInput.addEventListener('input', updateSlider);
    
    // Initialize
    updateSlider.call(minInput);
  });
}

// ============================================
// ICONS FLOATING ACTION BUTTON
// ============================================
function initFloatingActionButton() {
  const iconsDemoInput = document.getElementById('iconsDemoInput');
  const iconsDemoBtn = document.getElementById('iconsDemoBtn');

  if (iconsDemoInput && iconsDemoBtn) {
    iconsDemoInput.addEventListener('focus', () => {
      iconsDemoBtn.classList.add('show');
    });
    iconsDemoInput.addEventListener('blur', () => {
      setTimeout(() => {
        if (!iconsDemoBtn.matches(':hover')) {
          iconsDemoBtn.classList.remove('show');
        }
      }, 200);
    });
  }
}

// ============================================
// DEMO NAVBARS MOBILE TOGGLE
// ============================================
function initDemoNavbars() {
  // Multi-navbar toggle support
  document.querySelectorAll('[data-navbar]').forEach(toggle => {
    const menuId = toggle.getAttribute('data-navbar');
    const menu = document.querySelector(`[data-navbar-menu="${menuId}"]`);
    
    if (menu) {
      toggle.addEventListener('click', () => {
        toggle.classList.toggle('active');
        menu.classList.toggle('active');
      });

      const links = menu.querySelectorAll('.navbar-mobile-nav-link:not(.navbar-mobile-nav-toggle), .navbar-mobile-submenu-link');
      links.forEach(link => {
        link.addEventListener('click', () => {
          toggle.classList.remove('active');
          menu.classList.remove('active');
        });
      });
    }
  });

  // Demo search toggle
  const navbarSearchDemo = document.getElementById('navbarSearchDemo');
  const navbarSearchBtnDemo = document.getElementById('navbarSearchBtnDemo');
  const navbarSearchInputDemo = document.getElementById('navbarSearchInputDemo');

  if (navbarSearchBtnDemo && navbarSearchInputDemo) {
    let isSearchExpanded = false;

    navbarSearchBtnDemo.addEventListener('click', () => {
      if (!isSearchExpanded) {
        navbarSearchDemo.classList.add('is-expanded');
        navbarSearchInputDemo.focus();
        isSearchExpanded = true;
      }
    });

    navbarSearchInputDemo.addEventListener('blur', () => {
      if (!navbarSearchInputDemo.value) {
        navbarSearchDemo.classList.remove('is-expanded');
        isSearchExpanded = false;
      }
    });
  }

  // Main navbar search (for navigation page)
  const navbarSearch = document.getElementById('navbarSearch');
  const navbarSearchBtn = document.getElementById('navbarSearchBtn');
  const navbarSearchInput = document.getElementById('navbarSearchInput');

  if (navbarSearchBtn && navbarSearchInput) {
    let isSearchExpanded = false;

    navbarSearchBtn.addEventListener('click', () => {
      if (!isSearchExpanded) {
        navbarSearch.classList.add('is-expanded');
        navbarSearchInput.focus();
        isSearchExpanded = true;
      }
    });

    navbarSearchInput.addEventListener('blur', () => {
      if (!navbarSearchInput.value) {
        navbarSearch.classList.remove('is-expanded');
        isSearchExpanded = false;
      }
    });
  }

  // Mobile submenu toggles
  document.querySelectorAll('.navbar-mobile-nav-toggle').forEach(toggle => {
    toggle.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const submenuId = toggle.getAttribute('data-submenu');
      const submenu = document.querySelector(`[data-submenu-content="${submenuId}"]`);
      
      if (submenu) {
        toggle.classList.toggle('active');
        submenu.classList.toggle('active');
      }
    });
  });
}

// ============================================
// INTERACTIVE RATING
// ============================================
function initInteractiveRating() {
  const interactiveRating = document.getElementById('interactiveRating');
  if (!interactiveRating) return;
  
  const stars = interactiveRating.querySelectorAll('.rating-star');
  let selectedRating = 0;

  stars.forEach((star, index) => {
    star.addEventListener('mouseenter', () => {
      stars.forEach((s, i) => {
        if (i <= index) {
          s.classList.add('rating-star--filled');
        } else {
          s.classList.remove('rating-star--filled');
        }
      });
    });

    star.addEventListener('click', () => {
      selectedRating = index + 1;
    });
  });

  interactiveRating.addEventListener('mouseleave', () => {
    stars.forEach((s, i) => {
      if (i < selectedRating) {
        s.classList.add('rating-star--filled');
      } else {
        s.classList.remove('rating-star--filled');
      }
    });
  });
}

// ============================================
// DRAG & DROP FILE UPLOAD
// ============================================
function initDropzones() {
  document.querySelectorAll('.dropzone').forEach(dropzone => {
    const input = dropzone.querySelector('.dropzone__input');
    const icon = dropzone.querySelector('.dropzone__icon');
    const title = dropzone.querySelector('.dropzone__title');
    const text = dropzone.querySelector('.dropzone__text');
    const link = dropzone.querySelector('.dropzone__link');
    
    if (!input) return;

    // Click on link to trigger file input
    if (link) {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        input.click();
      });
    }

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
      e.preventDefault();
      e.stopPropagation();
    }

    // Highlight dropzone when dragging over
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, () => {
        dropzone.classList.add('dropzone--hover');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, () => {
        dropzone.classList.remove('dropzone--hover');
      }, false);
    });

    // Handle dropped files
    dropzone.addEventListener('drop', (e) => {
      const files = e.dataTransfer.files;
      handleFiles(files, dropzone, icon, title, text);
    }, false);

    // Handle selected files
    input.addEventListener('change', (e) => {
      const files = e.target.files;
      handleFiles(files, dropzone, icon, title, text);
    });

    function handleFiles(files, dropzone, icon, title, text) {
      if (files.length === 0) return;

      // Show success state
      dropzone.classList.add('dropzone--success');

      // Update icon to checkmark
      if (icon) {
        icon.innerHTML = `
          <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round"></path>
          </svg>
        `;
      }

      // Update text
      const fileCount = files.length;
      const fileName = files[0].name;

      if (title) {
        title.textContent = fileCount > 1 ? `${fileCount} FILES UPLOADED` : 'FILE UPLOADED';
      }

      if (text) {
        text.textContent = fileCount > 1 ? 'Ready to upload' : fileName;
      }
    }
  });
}

// ============================================
// INPUT FLOATING ACTION BUTTONS
// ============================================
function initFloatingInputButtons() {
  // All input-button pairs
  const inputButtonPairs = [
    { inputId: 'orgInput', buttonId: 'orgBtn' },
    { inputId: 'aiInput', buttonId: 'aiBtn' },
    { inputId: 'projectInput', buttonId: 'projectBtn' },
    { inputId: 'taskInput', buttonId: 'taskBtn' },
    { inputId: 'issueInput', buttonId: 'issueBtn' },
    { inputId: 'reviewInput', buttonId: 'reviewBtn' },
    { inputId: 'noteInput', buttonId: 'noteBtn' }
  ];

  inputButtonPairs.forEach(({ inputId, buttonId }) => {
    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);

    if (input && button) {
      input.addEventListener('focus', () => {
        button.classList.add('show');
      });

      input.addEventListener('blur', () => {
        setTimeout(() => {
          if (!button.matches(':hover')) {
            button.classList.remove('show');
          }
        }, 200);
      });
    }
  });
}

// ============================================
// CTA COUNTDOWN TIMER
// ============================================
function initCountdownTimer() {
  const countdownElements = document.querySelectorAll('[data-countdown]');
  if (countdownElements.length === 0) return;

  const target = Date.now() + (15 * 24 * 60 * 60 * 1000);

  function updateCountdown() {
    const now = new Date().getTime();
    const distance = target - now;

    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((distance % (1000 * 60)) / 1000);

    countdownElements.forEach(element => {
      const type = element.getAttribute('data-countdown');
      switch(type) {
        case 'days':
          element.textContent = String(days).padStart(2, '0');
          break;
        case 'hours':
          element.textContent = String(hours).padStart(2, '0');
          break;
        case 'minutes':
          element.textContent = String(minutes).padStart(2, '0');
          break;
        case 'seconds':
          element.textContent = String(seconds).padStart(2, '0');
          break;
      }
    });
  }

  updateCountdown();
  setInterval(updateCountdown, 1000);
}

// FLOATING CTA
// ============================================
function initFloatingCTA() {
  const floatingCTA = document.querySelector('.cta-floating');
  if (!floatingCTA) return;

  const closeBtn = floatingCTA.querySelector('.cta-floating-close');
  
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      floatingCTA.classList.add('cta-floating--closing');
      setTimeout(() => {
        floatingCTA.style.display = 'none';
        floatingCTA.classList.remove('cta-floating--closing');
      }, 400);
    });
  }

  // Show floating CTA after scroll delay (optional)
  let hasShown = false;
  window.addEventListener('scroll', () => {
    if (!hasShown && window.scrollY > 500) {
      hasShown = true;
      floatingCTA.style.display = 'block';
    }
  });
}

// INITIALIZE ALL ON DOM READY
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  initMobileNav();
  initAllTabs();
  initAllAccordions();
  initModals();
  initRangeSliders();
  initFloatingActionButton();
  initDemoNavbars();
  initInteractiveRating();
  initDropzones();
  initFloatingInputButtons();
  initCountdownTimer();
  initFloatingCTA();
  
  // Initialize page transitions LAST so it doesn't interfere with component handlers
  setupPageTransitions();
});
