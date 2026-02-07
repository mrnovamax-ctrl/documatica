/**
 * Accordion v12 – init .js-accordion (FAQ blocks)
 * One item open at a time; toggles .active and maxHeight on .accordion-content
 */
(function() {
  function initAccordions() {
    var containers = document.querySelectorAll('.js-accordion');
    Array.prototype.forEach.call(containers, function(container) {
      var items = Array.prototype.filter.call(container.children, function(el) {
        return el.classList.contains('accordion-item');
      });
      items.forEach(function(item) {
        var header = item.querySelector(':scope > .accordion-header');
        var content = item.querySelector(':scope > .accordion-content');
        if (!header || !content) return;
        if (item.classList.contains('active')) {
          content.style.maxHeight = content.scrollHeight + 'px';
        } else {
          content.style.maxHeight = '0';
        }
        header.addEventListener('click', function(e) {
          e.preventDefault();
          var isActive = item.classList.contains('active');
          if (isActive) {
            item.classList.remove('active');
            content.style.maxHeight = '0';
          } else {
            items.forEach(function(i) {
              if (i !== item && i.classList.contains('active')) {
                i.classList.remove('active');
                var c = i.querySelector(':scope > .accordion-content');
                if (c) c.style.maxHeight = '0';
              }
            });
            item.classList.add('active');
            content.style.maxHeight = content.scrollHeight + 'px';
            setTimeout(function() {
              content.style.maxHeight = content.scrollHeight + 'px';
            }, 50);
          }
        });
      });
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAccordions);
  } else {
    initAccordions();
  }
})();
