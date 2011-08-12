#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
    Build Cache-Key Map
    ~~~~~~~~~~~~~~~~~~~

    This module builds a nicely map that documents
    all our used cache-keys

    :copyright: 2008 by Christopher Grebs.
"""
import os
try:
    import _ast
except ImportError:
    raise RuntimeError('This requires at least python2.5')
import linecache
import inyoka

#TODO: if the cache_key is an BinOp or ast.Name try to lookup the correct value
#      – well I have no idea how to do that... – entequak


INYOKA_ROOT = os.path.realpath(os.path.dirname(inyoka.__file__))


def build_map():
    """
    Build the cache-key-map.

    Walk through all the files and look for `cache.set` or `cache.set_many`
    calls. This is just for documentation :-)
    """
    searchpath = [(INYOKA_ROOT, 'inyoka')]
    #XXX: I have no idea if I need to check for namespaces...
    assign_mapper = {}


    def walk_ast(ast):
        ii = isinstance
        if ii(ast, _ast.Assign):
            # concern of assigns
            targets = filter(
                lambda x: not ii(x, (_ast.Attribute, _ast.Subscript)),
                ast.targets
            )

            if ii(ast.value, _ast.Str):
                assign_mapper.update(dict((x.id,ast.value.s) for x in \
                                     targets))
            elif ii(ast.value, _ast.BinOp):
                check = False
                if ii(ast.value.left, _ast.Name) and \
                   not ii(ast.value.right, _ast.Attribute) and \
                   not ii(ast.value.left, _ast.Name):
                    s = ast.value.right.s
                    check = True
                elif ii(ast.value.right, _ast.Name) and \
                     not ii(ast.value.left, _ast.List) and \
                     not ii(ast.value.right, _ast.Name):
                    s = ast.value.left.s
                    check = True
                elif ii(ast.value.right, _ast.Subscript):
                    # obj = 'string%s' % obj.call()
                    # I have no idea how many combinations exists, so I
                    # leave that...
                    check = False
                if check:
                    assign_mapper.update(dict((x.id,s) for x in \
                                         targets))

        if ii(ast, _ast.Call) and ii(ast.func, _ast.Attribute) and \
           ii(ast.func.value, _ast.Name) and ast.func.value.id == 'cache' and \
           ast.func.attr in ('get', 'get_many') and ast.args:
            if ii(ast.args[0], _ast.Str):
                yield 'key "%s"' % ast.args[0].s, ast.func.lineno
            elif ii(ast.args[0], _ast.BinOp):
                op = ast.args[0]
                if ii(op.left, _ast.Name):
                    id, value = op.left.id, op.right.s
                else:
                    id, value = op.right.id, op.left.s
                yield 'key "%s" %s %s' % (value, '%', id), ast.func.lineno
            else:
                id = ast.args[0].id
                if id in assign_mapper:
                    yield 'object `%s` ("%s")' % (id, assign_mapper[id]), ast.func.lineno
                else:
                    yield 'object `%s`' % ast.args[0].id, ast.func.lineno

        for field in ast._fields or ():
            value = getattr(ast, field)
            if ii(value, (tuple, list)):
                for node in value:
                    if ii(node, _ast.AST):
                        for item in walk_ast(node):
                            yield item
            elif ii(value, _ast.AST):
                for item in walk_ast(value):
                    yield item

    def find_desc(filename, lineno):
        lines = []
        lineno -= 1
        while lineno > 0:
            line = linecache.getline(filename, lineno).strip()
            if line.startswith('#!'):
                line = line[2:]
                if line and line[0] == ' ':
                    line = line[1:]
                lines.append(line)
            elif line:
                break
            lineno -= 1

        return '\n'.join(reversed(lines)).decode('utf-8')


    result = {}

    for folder, prefix in searchpath:
        offset = len(folder)
        for dirpath, dirnames, filenames in os.walk(folder):
            for filename in filenames:
                if not filename.endswith('.py'):
                    continue
                filename = os.path.join(dirpath, filename)
                shortname = filename[offset:]
                ast = compile(''.join(linecache.getlines(filename)),
                              filename, 'exec', 0x400)

                for call, lineno in walk_ast(ast):
                    description = find_desc(filename, lineno)
                    result.setdefault(call, []).append((prefix, shortname,
                                                        lineno, description))
    return result


if __name__ == '__main__':
    map = build_map()
    for call, occur in map.iteritems():
        print '%s  ::' % call
        for x in occur:
            prefix, shortname, lineno, desc = x
            print '    Prefix: %s' % prefix
            print '    Module: %s' % shortname
            print '    Linenumber: %d' % lineno
            print '    Description: %s' % desc
            print '-----------------------------'
        print '***************************************'
