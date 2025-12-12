// Main JavaScript file for ConnectPro

$(document).ready(function() {
    // ===== MOBILE MENU =====
    const mobileMenuToggle = $('#mobile-menu-toggle');
    const closeMobileMenu = $('#close-mobile-menu');
    const mobileMenu = $('#mobile-menu');
    
    mobileMenuToggle.click(function() {
        mobileMenu.addClass('show');
        $('body').css('overflow', 'hidden');
    });
    
    closeMobileMenu.click(function() {
        mobileMenu.removeClass('show');
        $('body').css('overflow', 'auto');
    });
    
    // Close mobile menu on outside click
    mobileMenu.click(function(e) {
        if ($(e.target).hasClass('mobile-menu-overlay')) {
            mobileMenu.removeClass('show');
            $('body').css('overflow', 'auto');
        }
    });
    
    // ===== DROPDOWNS =====
    $(document).click(function(e) {
        // Close all dropdowns when clicking outside
        if (!$(e.target).closest('.dropdown, .user-dropdown').length) {
            $('.dropdown-menu').removeClass('show');
        }
    });
    
    // Toggle dropdowns
    $('.dropdown-toggle').click(function(e) {
        e.stopPropagation();
        $(this).closest('.dropdown').find('.dropdown-menu').toggleClass('show');
    });
    
    // ===== MODALS =====
    $('.modal-close').click(function() {
        $(this).closest('.modal').removeClass('show');
    });
    
    $('.modal').click(function(e) {
        if ($(e.target).hasClass('modal')) {
            $(this).removeClass('show');
        }
    });
    
    // ===== FORM VALIDATION =====
    $('form').submit(function(e) {
        const form = $(this);
        const requiredFields = form.find('[required]');
        let isValid = true;
        
        requiredFields.each(function() {
            const field = $(this);
            const value = field.val().trim();
            
            if (!value) {
                field.addClass('error');
                isValid = false;
                
                // Create error message if it doesn't exist
                if (!field.next('.error-message').length) {
                    field.after('<span class="error-message">This field is required</span>');
                }
            } else {
                field.removeClass('error');
                field.next('.error-message').remove();
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            
            // Scroll to first error
            const firstError = form.find('.error').first();
            if (firstError.length) {
                $('html, body').animate({
                    scrollTop: firstError.offset().top - 100
                }, 500);
            }
        }
    });
    
    // Remove error on input
    $('input, textarea, select').on('input change', function() {
        $(this).removeClass('error');
        $(this).next('.error-message').remove();
    });
    
    // ===== IMAGE LAZY LOADING =====
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    const src = img.dataset.src;
                    
                    if (src) {
                        img.src = src;
                        img.removeAttribute('data-src');
                    }
                    
                    observer.unobserve(img);
                }
            });
        });
        
        $('img[data-src]').each(function() {
            imageObserver.observe(this);
        });
    }
    
    // ===== INIFINITE SCROLL =====
    let isLoading = false;
    let currentPage = 1;
    let hasMorePages = true;
    
    $(window).scroll(function() {
        if ($(window).scrollTop() + $(window).height() >= $(document).height() - 100) {
            loadMoreContent();
        }
    });
    
    function loadMoreContent() {
        if (isLoading || !hasMorePages) return;
        
        isLoading = true;
        currentPage++;
        
        // Show loading indicator
        $('.content-container').append('<div class="loading-indicator"></div>');
        
        // Simulate API call - replace with actual endpoint
        $.get(window.location.pathname, { page: currentPage }, function(data) {
            if (data.html) {
                $('.content-container').append(data.html);
                hasMorePages = data.has_more;
            } else {
                hasMorePages = false;
            }
        }).always(function() {
            isLoading = false;
            $('.loading-indicator').remove();
        });
    }
    
    // ===== REAL-TIME UPDATES =====
    if (typeof WebSocket !== 'undefined') {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = protocol + '//' + window.location.host + '/ws/';
        
        try {
            const socket = new WebSocket(wsUrl);
            
            socket.onopen = function() {
                console.log('WebSocket connection established');
            };
            
            socket.onmessage = function(e) {
                const data = JSON.parse(e.data);
                handleWebSocketMessage(data);
            };
            
            socket.onclose = function() {
                console.log('WebSocket connection closed');
                // Attempt to reconnect after 5 seconds
                setTimeout(function() {
                    window.location.reload();
                }, 5000);
            };
        } catch (error) {
            console.log('WebSocket not available, using polling');
            startPolling();
        }
    } else {
        startPolling();
    }
    
    function startPolling() {
        setInterval(function() {
            $.get('/api/updates/', function(data) {
                handleUpdates(data);
            });
        }, 30000); // Poll every 30 seconds
    }
    
    function handleWebSocketMessage(data) {
        switch (data.type) {
            case 'new_message':
                showNotification('New message from ' + data.sender, '/inbox/');
                updateUnreadCount(data.unread_count);
                break;
                
            case 'new_booking':
                showNotification('New booking request', '/bookings/');
                break;
                
            case 'payment_received':
                showNotification('Payment received: KES ' + data.amount, '/wallet/');
                break;
                
            case 'profile_view':
                // Update profile views counter
                if ($('#profile-views').length) {
                    $('#profile-views').text(data.views);
                }
                break;
        }
    }
    
    function handleUpdates(data) {
        if (data.unread_messages > 0) {
            updateUnreadCount(data.unread_messages);
        }
    }
    
    // ===== NOTIFICATIONS =====
    function showNotification(message, url) {
        // Check if browser supports notifications
        if ("Notification" in window && Notification.permission === "granted") {
            const notification = new Notification('ConnectPro', {
                body: message,
                icon: '/static/images/logo.png'
            });
            
            notification.onclick = function() {
                window.focus();
                if (url) window.location.href = url;
                notification.close();
            };
        } else {
            // Fallback to in-app notification
            const notificationHtml = `
                <div class="notification toast">
                    <div class="toast-content">
                        <i class="fas fa-bell"></i>
                        <div class="message">${message}</div>
                    </div>
                    ${url ? `<a href="${url}" class="toast-action">View</a>` : ''}
                    <button class="toast-close"><i class="fas fa-times"></i></button>
                </div>
            `;
            
            $('.notifications-container').append(notificationHtml);
            
            // Auto-remove after 5 seconds
            setTimeout(function() {
                $('.toast').first().fadeOut(function() {
                    $(this).remove();
                });
            }, 5000);
        }
    }
    
    // Request notification permission
    if ("Notification" in window && Notification.permission === "default") {
        Notification.requestPermission();
    }
    
    // Close toast notifications
    $(document).on('click', '.toast-close', function() {
        $(this).closest('.toast').fadeOut(function() {
            $(this).remove();
        });
    });
    
    // ===== UNREAD COUNT UPDATES =====
    function updateUnreadCount(count) {
        $('.notification-badge').text(count);
        
        if (count > 0) {
            $('.notification-badge').addClass('has-unread');
            document.title = `(${count}) ConnectPro`;
        } else {
            $('.notification-badge').removeClass('has-unread');
            document.title = 'ConnectPro';
        }
    }
    
    // ===== IMAGE UPLOAD PREVIEW =====
    $('input[type="file"][accept*="image"]').change(function() {
        const input = $(this);
        const preview = input.siblings('.image-preview');
        
        if (this.files && this.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                if (preview.length) {
                    preview.html(`<img src="${e.target.result}" alt="Preview">`);
                } else {
                    input.after(`<div class="image-preview"><img src="${e.target.result}" alt="Preview"></div>`);
                }
            };
            
            reader.readAsDataURL(this.files[0]);
        }
    });
    
    // ===== RATING STARS =====
    $('.rating-stars .star').hover(function() {
        const rating = $(this).data('rating');
        $(this).parent().find('.star').each(function(i) {
            if (i < rating) {
                $(this).addClass('hover');
            } else {
                $(this).removeClass('hover');
            }
        });
    }).click(function() {
        const rating = $(this).data('rating');
        $(this).parent().find('.star').each(function(i) {
            if (i < rating) {
                $(this).addClass('selected');
            } else {
                $(this).removeClass('selected');
            }
        });
        
        // Submit rating via AJAX
        const itemId = $(this).closest('[data-id]').data('id');
        $.post('/api/rate/', {
            id: itemId,
            rating: rating,
            csrfmiddlewaretoken: getCookie('csrftoken')
        });
    });
    
    $('.rating-stars').mouseleave(function() {
        $(this).find('.star').removeClass('hover');
    });
    
    // ===== GEO LOCATION =====
    if (navigator.geolocation && $('#location-input').length) {
        $('#get-location-btn').click(function() {
            navigator.geolocation.getCurrentPosition(function(position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                
                // Reverse geocode using Nominatim
                $.get(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`, function(data) {
                    if (data.address) {
                        const location = data.display_name;
                        $('#location-input').val(location);
                    }
                });
            }, function(error) {
                console.log('Error getting location:', error);
                alert('Unable to get your location. Please enter it manually.');
            });
        });
    }
    
    // ===== PASSWORD VISIBILITY TOGGLE =====
    $('.toggle-password').click(function() {
        const input = $(this).siblings('input');
        const type = input.attr('type') === 'password' ? 'text' : 'password';
        input.attr('type', type);
        $(this).toggleClass('fa-eye fa-eye-slash');
    });
    
    // ===== COPY TO CLIPBOARD =====
    $('.copy-to-clipboard').click(function() {
        const text = $(this).data('text');
        const tempInput = $('<input>');
        $('body').append(tempInput);
        tempInput.val(text).select();
        document.execCommand('copy');
        tempInput.remove();
        
        // Show copied feedback
        const originalText = $(this).html();
        $(this).html('<i class="fas fa-check"></i> Copied');
        
        setTimeout(() => {
            $(this).html(originalText);
        }, 2000);
    });
    
    // ===== AJAX CSRF TOKEN =====
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Set up AJAX to send CSRF token
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type)) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });
    
    // ===== OFFLINE DETECTION =====
    window.addEventListener('online', function() {
        $('.connection-status').removeClass('offline').addClass('online').html('<i class="fas fa-wifi"></i> Online');
        syncOfflineData();
    });
    
    window.addEventListener('offline', function() {
        $('.connection-status').removeClass('online').addClass('offline').html('<i class="fas fa-wifi-slash"></i> Offline');
    });
    
    function syncOfflineData() {
        // Sync any data that was saved while offline
        if (localStorage.getItem('offline_data')) {
            const offlineData = JSON.parse(localStorage.getItem('offline_data'));
            
            offlineData.forEach(function(data) {
                $.ajax({
                    url: data.url,
                    method: data.method,
                    data: data.data,
                    success: function() {
                        console.log('Synced offline data');
                    }
                });
            });
            
            localStorage.removeItem('offline_data');
        }
    }
    
    // ===== INITIALIZE TOOLTIPS =====
    $('[title]').tooltip({
        placement: 'top',
        trigger: 'hover',
        container: 'body'
    });
    
    // ===== INITIALIZE POPOVERS =====
    $('[data-bs-toggle="popover"]').popover();
    
    // ===== SMOOTH SCROLL =====
    $('a[href^="#"]').click(function(e) {
        const target = $(this.getAttribute('href'));
        if (target.length) {
            e.preventDefault();
            $('html, body').stop().animate({
                scrollTop: target.offset().top - 100
            }, 1000);
        }
    });
    
    // ===== BACK TO TOP =====
    $(window).scroll(function() {
        if ($(this).scrollTop() > 300) {
            $('#back-to-top').fadeIn();
        } else {
            $('#back-to-top').fadeOut();
        }
    });
    
    $('#back-to-top').click(function() {
        $('html, body').animate({ scrollTop: 0 }, 1000);
        return false;
    });
    
    // ===== INITIALIZE DATE PICKERS =====
    $('.datepicker').datepicker({
        format: 'yyyy-mm-dd',
        autoclose: true,
        todayHighlight: true
    });
    
    $('.datetimepicker').datetimepicker({
        format: 'yyyy-mm-dd hh:ii',
        autoclose: true
    });
    
    // ===== CHARACTER COUNTER =====
    $('[maxlength]').each(function() {
        const maxLength = $(this).attr('maxlength');
        const counter = $(`<small class="char-counter">${maxLength} characters remaining</small>`);
        $(this).after(counter);
        
        $(this).on('input', function() {
            const length = $(this).val().length;
            const remaining = maxLength - length;
            counter.text(`${remaining} characters remaining`);
            
            if (remaining < 0) {
                counter.addClass('text-danger');
            } else {
                counter.removeClass('text-danger');
            }
        });
    });
    
    // ===== AUTO-SAVE FORMS =====
    let autoSaveTimer;
    $('.auto-save').on('input', function() {
        clearTimeout(autoSaveTimer);
        autoSaveTimer = setTimeout(function() {
            $('.auto-save-form').submit();
        }, 2000);
    });
    
    // ===== LAZY LOAD EMBEDS =====
    $('.lazy-embed').each(function() {
        const embed = $(this);
        const url = embed.data('url');
        
        if (isElementInViewport(embed[0])) {
            loadEmbed(embed, url);
        } else {
            $(window).on('scroll', function() {
                if (isElementInViewport(embed[0])) {
                    loadEmbed(embed, url);
                    $(window).off('scroll');
                }
            });
        }
    });
    
    function loadEmbed(embed, url) {
        $.get(url, function(data) {
            embed.html(data);
        });
    }
    
    function isElementInViewport(el) {
        const rect = el.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    // ===== INITIAL PAGE LOAD COMPLETE =====
    console.log('ConnectPro initialized');
});

// ===== SERVICE WORKER FOR PWA =====
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js').then(function(registration) {
            console.log('ServiceWorker registration successful with scope: ', registration.scope);
        }, function(err) {
            console.log('ServiceWorker registration failed: ', err);
        });
    });
}

// ===== PWA INSTALL PROMPT =====
let deferredPrompt;
const installButton = $('#install-pwa-btn');

if (installButton.length) {
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        installButton.show();
        
        installButton.click(() => {
            installButton.hide();
            deferredPrompt.prompt();
            
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('User accepted the install prompt');
                } else {
                    console.log('User dismissed the install prompt');
                }
                deferredPrompt = null;
            });
        });
    });
    
    window.addEventListener('appinstalled', () => {
        console.log('PWA was installed');
        installButton.hide();
        deferredPrompt = null;
    });
}