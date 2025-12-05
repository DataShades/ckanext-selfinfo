(function($) {
  $(document).ready(function () {
    const selfinfoSidebar = $('.selfinfo-sidebar');
    const selfinfoContent = $('.selfinfo-content');
    selfinfoSidebar.find('.selfinfo-plugin-link').on('click', function () {
      const plugin = $(this).data('plugin');
      if (!plugin) {
        return;
      }
      selfinfoSidebar.find('.selfinfo-plugin-link').removeClass('active');
      $(this).addClass('active');

      selfinfoSidebar.find('.selfinfo-navigation').removeClass('active');
      selfinfoSidebar.find(`.selfinfo-navigation-${plugin}`).addClass('active');

      selfinfoContent.find('.selfinfo-content-wrapper').removeClass('active');
      selfinfoContent.find(`.selfinfo-content-${plugin}-wrapper`).addClass('active');
    });

    selfinfoSidebar.find('.selfinfo-navigation-link').on('click', function () {
      const category = $(this).data('category');
      const plugin = $(this).data('plugin');
      if (!plugin || !category) {
        return;
      }
      $(this).parent().find('.selfinfo-navigation-link').removeClass('active');
      $(this).addClass('active');

      selfinfoSidebar.find(`.selfinfo-navigation-${plugin} .selfinfo-category-navigation`).removeClass('active');
      selfinfoSidebar.find(`.selfinfo-navigation-${plugin} .selfinfo-category-${category}-navigation`).addClass('active');

      selfinfoContent.find(`.selfinfo-content-${plugin}-wrapper .selfinfo-category-content`).removeClass('active');
      selfinfoContent.find(`.selfinfo-content-${plugin}-wrapper .selfinfo-category-${category}-content`).addClass('active');
    });
  });

  $('.sidebar-mobile-open, .sidebar-mobile-close').on('click', function() {
    const selfinfoSidebar = $('.selfinfo-sidebar');
    selfinfoSidebar.toggleClass('active');
  });
})(jQuery);
