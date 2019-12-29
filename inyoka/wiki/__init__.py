# -*- coding: utf-8 -*-
"""
    inyoka.wiki
    ~~~~~~~~~~~

    The wiki application.  The wiki is inspired by the MoinMoin wiki engine
    but uses a database rather than the plain filesystem.  This has the big
    advantage that it doesn't cause IO load on the server.  The database
    layout is inspired by MediaWiki.

    The Wiki Syntax is implemented and described in `inyoka.markup` and
    also used by other applications in the `inyoka` package.  Most important
    is that contrary to MoinMoin the parser produces `nodes` of the input
    text which that know how to render their contents into multiple output
    formats such as HTML and probably others in the future.

    The `views` are pretty nonexistent, in fact there is only one view which
    dispatches the `actions` and a second view to redirect from the url index
    to the main page.  A third view is always rendered if an action does not
    exist or an action wants to display something like a missing page but
    without giving users the possiblity to render a missing page.  (See also
    the `urls` module which just defines two url rules).

    The data `models` are encapsulated that most of them are available from
    the `Page` model when queried from the special query methods on the
    `PageManager`.  For more details have a look at the `inyoka.wiki.models`
    documentation.


    Entrypoints
    ===========

    `acl`
        Uses the `storage` module to manage wiki privileges and provides
        functions and decorators to test for them.

    `actions`
        The wiki actions (show, edit, ...) the wiki provides.  Actions change
        the way a page object is rendered or manipulated.  This approach is
        derived from the MoinMoin system.

    `forms`
        Holds django forms used in the wiki system.  (For example the
        page edit form)

    `macros`
        The abstract macro types and concrete implementations thereof.  Used
        directly by the parser.

    `models`
        The database models the wiki users.  This part of the documentation
        is especially useful for the template designers because it covers the
        objects mainly passed to the template rendering context.

    `parser`
        The parsing system used in the wiki and other components.

    `parsers`
        The parsers for the parser blocks.  Do not confuse this with the
        `parser` package which implements the wiki parser as such.

    `storage`
        The wiki storage system allows one to flag pages as behaving in a
        special way.  For example a page can act as inter wiki link mapping
        which the wiki will then automatically parse and add to the wiki
        configuration.  In fact most of the stuff that is configurable in the
        wiki is specified as wiki storage.

    `urls`
        The url definitions for the wiki.  Not so interesting because we just
        map urls directly to pagenames.

    `utils`
        Various utility functions and classes the wiki uses.  This for example
        holds the methods that validate page names, render udiffs etc.

    `views`
        Rather simple view functions that dispatch to the appropriate `actions`.


    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
