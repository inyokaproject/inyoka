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
});