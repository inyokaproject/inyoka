$(function () {

    function sidebar_resize() {
        var width = $('.col-sm-3').width();
        $('#sidebar').width(width);
    };

    $(window).scroll(function () {
        var y = $(window).scrollTop();
        if (y > 0) {
            $(".navbar-fixed-top").addClass('shadowed');
        } else {
            $(".navbar-fixed-top").removeClass('shadowed');
        }
    });

    $(window).resize(function () {
        sidebar_resize();
    });

    $('#sidebar').affix({
        offset: { top: $('#sidebar').offset().top - 60 }
    });

    sidebar_resize();
    if (window.location.hash) {
        var pos = $(window.location.hash).offset().top - 60;
        window.setTimeout(function() {
        $("html, body").animate({ scrollTop: pos }, 100);
        }, 50);
    }
});