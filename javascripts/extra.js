// Loups Documentation - Custom JavaScript

// Add smooth scrolling behavior
document.addEventListener('DOMContentLoaded', function() {
  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId !== '#') {
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
          e.preventDefault();
          targetElement.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      }
    });
  });

  // Add copy feedback for code blocks
  document.querySelectorAll('.md-clipboard').forEach(button => {
    button.addEventListener('click', function() {
      const icon = this.querySelector('.md-icon');
      if (icon) {
        icon.classList.add('icon-pulse');
        setTimeout(() => {
          icon.classList.remove('icon-pulse');
        }, 1000);
      }
    });
  });

  // Enhance external links
  document.querySelectorAll('a[href^="http"]').forEach(link => {
    if (!link.hostname.includes('jcspeegs.github.io') && !link.hostname.includes('localhost')) {
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
    }
  });
});
