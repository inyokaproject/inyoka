$(function () {

    function sidebar_resize() {
        var width = $('.col-sm-3').width();
        $('#sidebar').width(width);
    };

    $(window).scroll(function () {
        var y = $(window).scrollTop();
        if (y > 0) {
            $("#main-navbar").addClass('shadowed');
        } else {
            $("#main-navbar").removeClass('shadowed');
        }
    });

    $(window).resize(function () {
        sidebar_resize();
    });

    var navbar_height = parseFloat($('#main-navbar').css('height'), 10) * 1.38;
    $('#sidebar').affix({
        offset: { top: $('#sidebar').offset().top - navbar_height }
    });

    sidebar_resize();
    if (window.location.hash) {
        var pos = $(window.location.hash).offset().top - navbar_height;
        window.setTimeout(function() {
        $('html, body').animate({ scrollTop: pos }, 100);
        }, 50);
    }
});