
// Main JavaScript file for MjengoLink

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll to sections
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if(targetId === '#') return;
            const targetElement = document.querySelector(targetId);
            if(targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Navbar scroll effect
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            if (window.scrollY > 50) {
                navbar.classList.add('navbar-scrolled');
            } else {
                navbar.classList.remove('navbar-scrolled');
            }
        }
    });

    // Animation on scroll
    function animateOnScroll() {
        const elements = document.querySelectorAll('.animate-fadeInUp');

        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const screenPosition = window.innerHeight / 1.2;

            if (elementPosition < screenPosition) {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }
        });
    }

    // Set initial state for animated elements
    document.querySelectorAll('.animate-fadeInUp').forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        element.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
    });

    // Trigger animation on load and scroll
    window.addEventListener('load', animateOnScroll);
    window.addEventListener('scroll', animateOnScroll);

    // Trade item hover effects
    document.querySelectorAll('.trade-item').forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px)';
        });

        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Project filter functionality
    const projectFilters = document.querySelectorAll('.project-filter');
    projectFilters.forEach(filter => {
        filter.addEventListener('change', function() {
            // This would be implemented based on your project filtering logic
            console.log('Filter changed:', this.value);
        });
    });

    // Payment form validation
    const paymentForms = document.querySelectorAll('.payment-form');
    paymentForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const amountInput = this.querySelector('input[name="amount"]');
            if (amountInput && parseFloat(amountInput.value) <= 0) {
                e.preventDefault();
                alert('Please enter a valid amount');
                amountInput.focus();
            }
        });
    });

    // Dashboard menu toggle for mobile
    const dashboardMenuToggle = document.getElementById('dashboardMenuToggle');
    if (dashboardMenuToggle) {
        dashboardMenuToggle.addEventListener('click', function() {
            const dashboardMenu = document.getElementById('dashboardMenu');
            if (dashboardMenu) {
                dashboardMenu.classList.toggle('show');
            }
        });
    }
});
