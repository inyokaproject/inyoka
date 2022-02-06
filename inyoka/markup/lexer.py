# -*- coding: utf-8 -*-
"""
    inyoka.markup.lexer
    ~~~~~~~~~~~~~~~~~~~

    Tokenizes our wiki markup.  The lexer is implemented as some sort of
    scanner with an internal stack.  Inspired by pygments.


    :copyright: (c) 2007-2022 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re


from django.utils.encoding import smart_text

from inyoka.markup.parsertools import TokenStream


def bygroups(*args):
    """
    Callback creator for bygroup yielding.
    """
    return lambda m: zip(args, m.groups())


def astuple(token):
    """
    Yield the groups together as one tuple.
    """
    def wrapped(match):
        yield token, match.groups()
    return wrapped


def fallback():
    """
    Just pop and do nothing.
    """
    return rule('', leave=1)


def switch(state):
    """
    Go to another state when reached.
    """
    return rule('', switch=state)


class ruleset(tuple):
    """
    Rulesets keep some rules.  If at the end of parsing a ruleset is left
    on the stack a `name_end` token is emitted without a value.  If you don't
    want this behavior use the `helperset`.
    """
    __slots__ = ()

    def __new__(cls, *args):
        return tuple.__new__(cls, args)


class include(str):
    """
    Tells the lexer to include tokens from another set.
    """
    __slots__ = ()


class rule(object):
    """
    This represents a parsing rule.
    """
    __slots__ = ('match', 'token', 'enter', 'silententer', 'switch', 'leave')

    def __init__(self, regexp, token=None, enter=None, silententer=None,
                 switch=None, leave=0):
        self.match = re.compile(regexp, re.U).match
        self.token = token
        self.enter = enter
        self.silententer = silententer
        self.switch = switch
        self.leave = leave


# what the lexer understands as url.  This list is far from complete
# but this is intention.  These are the most often used URLs and the
# smaller the list, the less the clashes with the interwiki names.
# and yes: this list includes nonstandard urls too because they are
# in use (like git or irc)
_url_pattern = (
    # urls with netloc
    r'(?:(?:https?|ftps?|file|ssh|mms|svn(?:\+ssh)?|git|dict|nntp|ircs?|'
    r'rsync|smb|apt)://|'
    # urls without netloc
    r'(?:mailto|telnet|s?news|sips?|skype|apt):)'
)

rules = {
    'everything': ruleset(
        include('block'),
        include('inline'),
        include('links')
    ),
    'inline_with_links': ruleset(
        include('inline'),
        include('links')
    ),
    'block': ruleset(
        rule('^##.*?(\n|$)(?m)', None),
        rule('^#\s*(.*?)\s*:\s*(?m)', bygroups('metadata_key'),
             enter='metadata'),
        rule(r'^={1,5}\s*(?m)', enter='headline'),
        rule(r'^[ \t]+((?!::).*?)::\s+(?m)', bygroups('definition_term'),
             enter='definition'),
        rule(r'^\|\|(?m)', enter='table_row'),
        rule(r'^[ \t]+(?:[*-]|[01aAiI]\.)\s*(?m)', enter='list_item'),
        rule(r'\{\{\|', enter='box'),
        rule(r'\{\{\{', enter='pre'),
        rule(r'^<{40}\s*$(?m)', enter='conflict'),
        rule(r'^----+\s*(\n|$)(?m)', 'ruler')
    ),
    'inline': ruleset(
        rule('<!--.*?-->(?s)', None),
        rule("'''", enter='strong'),
        rule("''", enter='emphasized'),
        rule('``', enter='escaped_code'),
        rule('`', enter='code'),
        rule('__', enter='underline'),
        rule(r'--\(', enter='stroke'),
        rule('~-\(', enter='small'),
        rule(r'~\+\(', enter='big'),
        rule(r',,\(', enter='sub'),
        rule(r'\^\^\(', enter='sup'),
        rule(r'\(\(', enter='footnote'),
        rule(r'\[\[([\w_]+)', bygroups('macro_name'),
             enter='macro'),
        rule(r'\[@(.+?)\s*\(', bygroups('template_name'),
             enter='template'),
        rule(r'\[color\s*=\s*(.*?)\s*\]', bygroups('color_value'),
             enter='color'),
        rule(r'\[size\s*=\s*(.*?)\s*\]', bygroups('font_size'),
             enter='size'),
        rule(r'\[font\s*=\s*(.*?)\s*\]', bygroups('font_face'),
             enter='font'),
        rule(r'\[mod\s*=\s*(.*?)\s*\]', bygroups('username'),
             enter='mod'),
        rule(r'\[edit\s*=\s*(.*?)\s*\]', bygroups('username'),
             enter='edit'),
        rule(r'\[raw\](.*?)\[/raw\]', bygroups('raw')),
        rule(r'\\\\[^\S\n]*(\n|$)(?m)', 'nl'),
        include('highlightable_with_inlines')
    ),
    'links': ruleset(
        rule(r'\[\s*(\d+)\s*\]', bygroups('sourcelink')),
        rule(r'(\[\s*)((?:%s|\?|#)\S+?)(\s*\])' % _url_pattern, bygroups(
             'external_link_begin', 'link_target', 'external_link_end')),
        rule(r'\[((?:%s|\?|#).*?)\s+' % _url_pattern, bygroups('link_target'),
             enter='external_link'),
        rule(r'\[\s*([^:\]]+?)?\s*:\s*((?:::|\\:|[^:\]])*)\s*:\s*',
             astuple('link_target'), enter='wiki_link'),
        rule(_url_pattern + r'[^\[\s/\]]+(/[^\s\].,:;?]*([.,:;?][^\s\].,:;?]+)*)?[^\]\)\\\s]',
             'free_link')
    ),
    'highlightable_with_inlines': ruleset(
        rule(r'\[mark\]', enter='highlighted_wi')
    ),
    'highlightable': ruleset(
        rule(r'\[mark\]', enter='highlighted')
    ),
    # highlighted code; the first allows other inlines as content
    # and is used for normal text, the other is used in pre_data
    'highlighted_wi': ruleset(
        rule(r'\[/mark\]', leave=1),
        include('inline_with_links')
    ),
    'highlighted': ruleset(
        rule(r'\[/mark\]', leave=1)
    ),
    # metadata defs
    'metadata': ruleset(
        rule(r'\s*(\n|$)(?m)', leave=1),
        rule(r'\s*,\s*', 'func_argument_delimiter'),
        rule(r"('([^'\\]*(?:\\.[^'\\]*)*)'|"
             r'"([^"\\]*(?:\\.[^"\\]*)*)")(?s)', 'func_string_arg'),
    ),
    # conflict blocks
    'conflict': ruleset(
        rule(r'^={40}\s*$(?m)', 'conflict_switch'),
        rule(r'^>{40}\s*$(?m)', leave=1),
        include('everything')
    ),
    # In difference to moin we allow arbitrary markup in headlines.
    'headline': ruleset(
        rule(r'\s*=+\s*$(?m)', leave=1),
        include('inline_with_links')
    ),
    'definition': ruleset(
        rule(r'(\n|$)(?m)', leave=1),
        include('inline_with_links')
    ),
    'strong': ruleset(
        rule("'''", leave=1),
        include('inline_with_links')
    ),
    'emphasized': ruleset(
        rule("'''([^'])", bygroups('text'), enter='strong'),
        rule("''", leave=1),
        include('inline_with_links')
    ),
    'escaped_code': ruleset(
        rule('``', leave=1),
    ),
    'code': ruleset(
        rule('`', leave=1),
    ),
    'underline': ruleset(
        rule('__', leave=1),
        include('inline_with_links')
    ),
    'stroke': ruleset(
        rule('\)--', leave=1),
        include('inline_with_links')
    ),
    'small': ruleset(
        rule('\)-~', leave=1),
        include('inline_with_links')
    ),
    'big': ruleset(
        rule(r'\)\+~', leave=1),
        include('inline_with_links')
    ),
    'sub': ruleset(
        rule(r'\),,', leave=1),
        include('inline_with_links')
    ),
    'sup': ruleset(
        rule(r'\)\^\^', leave=1),
        include('inline_with_links')
    ),
    'footnote': ruleset(
        rule(r'\)\)', leave=1),
        include('everything')
    ),
    'list_item': ruleset(
        rule(r'(\n|$)(?m)', leave=1),
        include('everything')
    ),
    'color': ruleset(
        rule(r'\[/color\]', leave=1),
        include('inline_with_links')
    ),
    'size': ruleset(
        rule(r'\[/size\]', leave=1),
        include('inline_with_links')
    ),
    'font': ruleset(
        rule(r'\[/font\]', leave=1),
        include('inline_with_links')
    ),
    'mod': ruleset(
        rule(r'\[/mod\]', leave=1),
        include('everything')
    ),
    'edit': ruleset(
        rule(r'\[/edit\]', leave=1),
        include('everything')
    ),
    # links
    'wiki_link': ruleset(
        rule(r'\s*\]', leave=1),
        include('inline')
    ),
    'external_link': ruleset(
        rule(r'\s*\]', leave=1),
        include('inline')
    ),
    # a pre block, could have arguments and a parser
    'pre': ruleset(
        rule(r'\n?#!([\w_]+)', bygroups('parser_begin'),
             switch='parser_arguments'),
        switch('pre_data')
    ),
    'parser_arguments': ruleset(
        rule(r'(?=\n|$)(?m)', 'parser_end', switch='parser_data'),
        rule(r'[^\S\n]+', None),
        include('function_call')
    ),
    'parser_data': ruleset(
        rule(r'\}\}\}', leave=1)
    ),
    'pre_data': ruleset(
        include('parser_data'),
        include('highlightable')
    ),
    # a table row. with spans and all that stuff
    'table_row': ruleset(
        rule(r'\s*<', 'table_def_begin', switch='table_def'),
        switch('table_contents')
    ),
    'table_def': ruleset(
        rule(r'>', 'table_def_end', switch='table_contents'),
        include('function_call')
    ),
    'table_contents': ruleset(
        rule(r'\|\|\s*?(\n|$)(?m)', leave=1),
        rule(r'\|\|', 'table_col_switch', switch='table_row'),
        include('everything')
    ),
    # a box, works like a single table cell but generates a div
    'box': ruleset(
        rule(r'\s*<', 'box_def_begin', switch='box_def'),
        switch('box_contents')
    ),
    'box_def': ruleset(
        rule(r'>', 'box_def_end', switch='box_contents'),
        include('function_call')
    ),
    'box_contents': ruleset(
        rule(r'\|\}\}(?m)', leave=1),
        include('everything')
    ),
    # the macro base is that part where the lexer waits for an upcoming
    # argument list start parenthesis. It will skip whitespace but fall
    # back and close the macro if there is something that is not handled.
    'macro': ruleset(
        rule(r'\s+', None),
        rule(r'\]\]', leave=1),
        rule(r'\(', None, silententer='macro_arguments'),
        fallback()
    ),
    # inside the argument section of a macro the normal rules for function
    # calls (shared with parsers). we do not close on the closing
    # parenthesis only, just if followed by whitespace and the closing
    # brackets. Note that we leave the `macro` state too. This ruleset
    # can only be entered by the `macro` ruleset.
    'macro_arguments': ruleset(
        rule(r'\)\s*\]\]', leave=2),
        include('function_call')
    ),
    # the template alias works pretty much like a macro
    'template': ruleset(
        rule(r'\s*\)\s*@?\]', leave=1),
        include('function_call')
    ),
    # function calls (parse string arguments and implicit strings)
    'function_call': ruleset(
        rule(',', 'func_argument_delimiter'),
        rule('\s+', None),
        rule(r"('([^'\\]*(?:\\.[^'\\]*)*)'|"
             r'"([^"\\]*(?:\\.[^"\\]*)*)")(?s)', 'func_string_arg'),
        rule(r'([\w_]+)\s*=', bygroups('func_kwarg'))
    )
}

_quote_re = re.compile(r'^(>+) ?(?m)')
_block_start_re = re.compile(r'(?<!\\)\{\{\{')
_block_end_re = re.compile(r'(?<!\\)\}\}\}')


def iter_rules(x):
    for rule in rules[x]:
        if rule.__class__ is include:
            for item in iter_rules(rule):
                yield item
        else:
            yield rule


def tokenize_block(string, _escape_hint=None):
    """
    This tokenizes a block.  It's used by the normal tokenize function to
    lex quotes and normal markup isolated, so that breakage in one block
    does not affect outer areas.
    """
    escaped = False
    pos = 0
    end = len(string)
    stack = [(None, 'everything')]
    rule_cache = {}
    text_buffer = []
    add_text = text_buffer.append
    push = stack.append
    flatten = ''.join

    while pos < end:
        state = stack[-1][1]
        if state not in rule_cache:
            rule_cache[state] = list(iter_rules(state))
        for rule in rule_cache[state]:
            m = rule.match(string, pos)
            if m is not None:
                # if the token is escaped we push the lexed
                # value to the text buffer and ignore
                if escaped or _escape_hint is not None:
                    add_text(m.group())
                    pos = m.end()
                    if _escape_hint is not None:
                        _escape_hint.append(m.start())
                    escaped = False
                    break

                # first flush text that is left in the buffer
                if text_buffer:
                    text = flatten(text_buffer)
                    if text:
                        yield 'text', text
                    del text_buffer[:]

                # now enter the new scopes if entered in a
                # non silent way
                if rule.enter is not None:
                    push((rule.enter + '_end', rule.enter))
                    yield rule.enter + '_begin', m.group()
                elif rule.silententer is not None:
                    push((None, rule.silententer))

                # now process the data
                if callable(rule.token):
                    for item in rule.token(m):
                        yield item
                elif rule.token is not None:
                    yield rule.token, m.group()

                # now check if we leave something. if the state was
                # entered non silent, send a close token.
                pos = m.end()
                for x in range(rule.leave):
                    announce, item = stack.pop()
                    if announce is not None:
                        yield announce, m.group()

                # switch to another state, postponing the nonsilent token
                if rule.switch:
                    announce, item = stack.pop()
                    if announce is not None:
                        push((announce, rule.switch))
                break
        else:
            char = string[pos]
            if char == '\\':
                if escaped:
                    # this is a fix for the problem that two backslashes
                    # inside are displayed as one, even in code blocks
                    if string[pos - 1] == '\\':
                        char = '\\\\'
                    else:
                        char = ''
                    escaped = False
                else:
                    escaped = True
                    char = ''
            else:
                if escaped:
                    char = '\\' + char
                escaped = False
            add_text(char)
            pos += 1

    # if there is a bogus escaped push a backslash
    if escaped:
        add_text('\\')

    # if the text buffer is left filled, we flush it
    if text_buffer:
        text = flatten(text_buffer)
        if text:
            yield 'text', text

    # if there are things in the stack left we should
    # emit the end tokens
    for announce, item in reversed(stack):
        if announce is not None:
            yield announce, ''


def escape(text):
    """Escape a text."""
    escapes = []
    gen = tokenize_block('\n'.join(text.splitlines()), escapes)
    text = ''.join(x[1] for x in gen)
    offset = 0
    for pos in escapes:
        pos = pos + offset
        text = text[:pos] + '\\' + text[pos:]
        offset += 1
    return text


class Lexer(object):

    def tokenize(self, string):
        """
        Resolve quotes and parse quote for quote in an isolated environment.
        """
        buffer = []
        stack = [0]
        open_blocks = [False]

        def tokenize_buffer():
            for item in tokenize_block('\n'.join(smart_text(obj) for obj in buffer)):
                yield item
            del buffer[:]

        def changes_block_state(line, reverse):
            primary = _block_start_re.search
            secondary = _block_end_re.search
            if reverse:
                primary, secondary = secondary, primary
            match = primary(line)
            if match is None:
                return False
            while True:
                match = secondary(line, match.end())
                if match is None:
                    return True
                match = primary(line, match.end())
                if match is None:
                    return False

        def tokenize_blocks():
            for line in string.splitlines():
                block_open = open_blocks[-1]
                if not block_open:
                    m = _quote_re.match(line)
                    if m is None:
                        level = 0
                    else:
                        level = len(m.group(1))
                        line = line[m.end():]
                    if level > stack[-1]:
                        for item in tokenize_buffer():
                            yield item
                        for new_level in range(stack[-1] + 1, level + 1):
                            stack.append(new_level)
                            open_blocks.append(False)
                            yield 'quote_begin', None
                    elif level < stack[-1]:
                        for item in tokenize_buffer():
                            yield item
                        for x in range(stack[-1] - level):
                            stack.pop()
                            open_blocks.pop()
                            yield 'quote_end', None
                else:
                    line = re.sub('^' + '> ?' * (len(open_blocks) - 1), '', line)
                if not block_open and changes_block_state(line, False):
                    open_blocks[-1] = True
                elif block_open and changes_block_state(line, True):
                    open_blocks[-1] = False
                buffer.append(line)

            for item in tokenize_buffer():
                yield item
            while stack:
                if stack.pop():
                    yield 'quote_end', None
                open_blocks.pop()

        return TokenStream.from_tuple_iter(tokenize_blocks())
