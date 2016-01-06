# TODO!

## Features
* Moving messages to trash in bulk. Currently there is no (functioning) way to
  select multiple messages and move them to trash. This needs some backend
  method on the model/manager, as well as a view and a form.
* Tasks: Messages should be deleted from trash automatically. There is a
  queryset for it `to_expunge()` but no task that takes advantage of it.

## Migrations
This is a pretty big point. Since the model changes, we will need migrations!

## Tests
A metric buttload of tests. Specifically the views are currently untested.
I think fixtures might be a good idea to provide a default database to test
against. I really need to learn mocking. :/

* The forms seem reasonably well tested.
* The model is partially tested. Specifically the queryset should be tested.
  (Fixtures!)
* The views are currently untested.
* I introduced a few helpers (mixins) that should get tested separately.

## Spam protection
Ideally we get a simple mixin we can use for all kinds of forms. For starters a
blacklist of bad words might like we had before might be reasonable.

## Other little bits and bobs
I think some code could be relocated.
* `CSVField` should go to `inyoka.utils.forms`, since I think it is generally
  useful to have a comma separated value field.
* `MultiUserField` and `MultiGroupField` could have other applications as well,
  so they should also get a more general place (probably also
  `inyoka.utils.forms`)
* `FormPreviewMixin` seems really useful in a lot of places where we have
  preview functionality on edit views. My biggest issue with it is how the
  `render_preview()` method looks and how it may interfere with `TestCase`,
  because `InyokaMarkupField` relies on `session`. I think it can be cleaned up
  a bit and then could have a place in `inyoka.utils.generic`.
* Replying to “tickets” (e.g reported topics and suggested articles) should
  probably be relocated to the respective views – or even better, if we do
  [Unify Ticket Systems](https://github.com/inyokaproject/inyoka/issues/354)
  that would be the the right place for it.
