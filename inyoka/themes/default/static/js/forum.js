$(function () {
    $('.category').on('show.bs.collapse', function () {
        var category_id = $(this).find('ul').attr('id').replace('category_', '');
        $.get('/', {
            __service__: 'forum.toggle_category',
            id: category_id,
            state: 'show'
        });
    });
    $('.category').on('hide.bs.collapse', function () {
        var category_id = $(this).find('ul').attr('id').replace('category_', '');
        $.get('/', {
            __service__: 'forum.toggle_category',
            id: category_id,
            state: 'hide'
        });
    });

    $('.topic').hover(function () {
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
});