$(function () {
  $(".mobile-bottom-navigation").appendTo("body")

  $(".mobile-search-button").on("click", function (e) {
    e.stopPropagation();
    e.preventDefault();
    $(".store-search-box").toggleClass("open");
    $("html").toggleClass("search-open");
  })
  $(document).on("click", ".filter-button" ,function (e) {
    e.stopPropagation();
    e.preventDefault();
    $(".side-2").toggleClass("open");
  })
  $(".store-search-box").on("click", function (e) {
    e.stopPropagation();
  })

  $(".side-2,.search-box,.header-menu").on("click", function (e) {
    e.stopPropagation();
  })

  $(".mobile-menu-close").on("click", function (e) {
    e.stopPropagation();
    $(".header-menu .sublist").removeClass("show");
    $(".header-menu").removeClass("open");

    $("html").removeClass("mobile-menu-added");

  })

  $(".go-back").on("click", function (e) {
    e.stopPropagation();
    var ParentHead = $(this).parent(".mobile-menu-head");
    ParentHead.parent(".sublist").removeClass("show");
  })

  $(".mm-nav-item.has-children .right-arrow").on("click", function (e) {
    e.stopPropagation();
    e.preventDefault();
    var ParentLink = $(this).parent("a");
    ParentLink.siblings(".sublist").addClass("show");
  })

    $("#mega-menu-toggle").on("click", function (e) {
      e.stopPropagation();
      e.preventDefault();

      if ($(window).width() < 992) {
        $(".header-menu").addClass("open");
        $("html").addClass("mobile-menu-added");
      }
    })
    $(".header-menu").on("click", function (e) {
      e.stopPropagation();
    })


  var headerHeight = 0;
  $(window).on("scroll", function () {
    headerHeight = $(".header").height();
     
    if ($(window).scrollTop() > headerHeight) {
      $("html").addClass("header-scrolled");
    } else {
      $("html").removeClass("header-scrolled");
    }

  })

  $(".not-loggedin > a").on("click", function (e) {
    e.stopPropagation();
    e.preventDefault();
    $(".login-form-popup").toggleClass("show");
  })
  $(".login-form-popup").on("click", function (e) {
    e.stopPropagation();
  })
  $("html,body").on("click", function (e) {
    $(".login-form-popup").removeClass("show");
  })

  $(".product-filter .collapse-filter").on("click", function (e) {
    e.stopPropagation();
    var findParentFilterBlock = $(this).parents(".product-filter");
    $(this).toggleClass("open");
    findParentFilterBlock.children(".filter-content").slideToggle();
  })
  $(".side-2 .block:not(.product-filters) .collapse-filter").on("click", function (e) {
    e.stopPropagation();
    var findParentBlock = $(this).parents(".side-2 .block");
    $(this).toggleClass("open");
    findParentBlock.children(".listbox").slideToggle();
  })

  $("#advance-cart-flyout-cart-wrapper").appendTo("body");

  $(".product-filter .filter-search-button").on("click", function (e) {
    e.stopPropagation();
    var filterParent = $(this).parents(".product-filter");
    filterParent.find(".filter-search").toggleClass("show");
    filterParent.find(".filter-search.show .filter-search-text-input").focus()
  })
  $(".block .filter-search-button").on("click", function (e) {
    e.stopPropagation();
    var filterParent = $(this).parents(".block");
    filterParent.find(".filter-search").toggleClass("show");
  })

  $(".customer-pupup-button").on("click", function (e) {
    e.stopPropagation();
    e.preventDefault();
    $(".customer-popup").toggleClass("show");
  })

  $(document).on("click", ".product-item .attribute-squares", function (e) {
    e.stopPropagation();
    var childListItem = $(this).siblings(".attribute-squares").children("li")
    childListItem.removeClass("selected-value");
    $(this).children("li").addClass("selected-value")
  })

  $(".side-2-close").on("click", function () {
    $(".side-2").removeClass("open");
  })

  $("html, body").on("click", function (e) {
    $(".header-menu").removeClass("open");

    $("html").removeClass("mobile-menu-added");
    $(".store-search-box").removeClass("open");
    $("html").removeClass("search-open");

    $(".customer-popup").removeClass("show");
    $(".side-2").removeClass("open");
  })

});


