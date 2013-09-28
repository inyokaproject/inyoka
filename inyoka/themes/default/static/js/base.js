$(function () {
/*
    function sidebar_resize() {
        var width = $('.col-sm-3').width();
        var padding_left = parseFloat($('#sidebar').css('padding-left').replace('px', ''));
        var padding_right = parseFloat($('#sidebar').css('padding-right').replace('px', ''));
        width -=  padding_left + padding_right;
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
*/
    if (window.location.hash) {
        var pos = $(window.location.hash).offset().top - navbar_height;
        window.setTimeout(function () {
            $('html, body').animate({ scrollTop: pos }, 100);
        }, 50);
    }

    // initialize fancy tooltips
    $('[data-toggle="tooltip"]').tooltip();

    // resizer for large codeblocks
    $('div.code').add('pre.notranslate').each(function () {
        if (this.clientHeight < this.scrollHeight) {
            $(this).after('<button class="codeblock_resizer btn btn-default btn-sm">Expand</button>')
                .css('height', '300px').css('max-height', 'none')
                .data('original_height', this.clientHeight);
        }
    });

    $('[data-trigger="manual"]').hover(function () {
        var placement;
        if ($('body').width() < 753) {
            placement = 'bottom';
        } else {
            placement = 'left';
        }
        $(this).data('bs.tooltip').options.placement = placement;
        $(this).tooltip('show');
    }, function() {
        $(this).tooltip('hide');
    });

    if (navigator.appName.toLowerCase() == 'konqueror') return;
    $('.codeblock_resizer').click(function () {
        $codeblock = $(this).prev();
        if (!$codeblock.hasClass('codeblock_expanded')) {
            $codeblock.addClass('codeblock_expanded');
            $codeblock.animate({
                'height': $codeblock[0].scrollHeight
            }, 500);
            $(this).text('Collapse');
        } else {
            $codeblock.removeClass('codeblock_expanded');
            $codeblock.animate({
                'height': $codeblock.data('original_height')
            }, 500);
            $(this).text('Expand');
        }
    });
});
