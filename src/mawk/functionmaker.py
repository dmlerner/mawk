from .utils import curry  # used in eval
from .utils import find # used in make_regex_match_function_string
from .utils import vector, replace, map, compose, filter, flatten, identity, apply, const, sub
from .logger import p
import re
from .formatter import use_stdin_raw, use_stdin_py
from . import arguments

def make_regex_match_function_string(x):
    '''
    'blah blah k&foo stuff asdf'
    ->
    blah blah find('foo', 'k') stuff asdf
    '''
    # TODO: allow not quoting the pattern?
    return sub(r'([^\s&]+)&([^&]+)&', 'find($2,$1)', x)

def make_regex_sub_function_string(x):
    return sub(r'([^\s&]+)&([^&]+)&([^&]*)&', 'sub($2,$3,$1)', x)

def make_conditional_string(x):
    ''' a?b:c '''
    p('cond', 'x', x, 'sub', sub(r'(.*)\?(.*):(.*);', '$2 if $1 else $3', x))
    return sub(r'\?([^:]+):([^:]+):([^:]*):', '$2 if $1 else $3', x)

def predicate_maker(mode, arg, vals):
    assert mode in 'wb'
    assert arg in (0, 1)
    if not vals:
        return None
    vals = set(vals)
    p(mode, arg, vals)
    return lambda k, v: ([k, v][arg] in vals) == (mode == 'w')

# TODO:; ability to add variable to scope


def make_predicates(i, ix, v, vx):
    return filter(bool)((predicate_maker('wb'[j % 2], j // 2, vals) for j, vals in enumerate((i, ix, v, vx))))


def shape(x):
    dims = []
    last = x
    while len(dims) < 10:
        try:
            dims.append(len(last))
            last = last[0][:]
        except BaseException:
            break
    return dims


def sub_all(source, *subs):
    alphanumeric = 'Q', '[a-zA-Z0-9_]'
    p('source, subs', source, subs, shape(subs))
    # replaced = False
    for sub in subs:
        for f, r in sub:
            f = f.replace(*alphanumeric)
            new = re.sub(f, r, source)
            if new != source:
                p(f, r, source, new)
                # replaced = True
            source = new
            # TODO: make default argument work with parameterized conditoin/return replaced
            # if not replaced and not set(source.lower()).intersection(set('idkv')):
            #     source = 'v ' + source
            #     p('--> ' + source)
    return source


@vector
def make_subs(prefix):
    p('make_subs', prefix)
    range = r'x\.(Q+),(Q+)', r'x[x.index("\1"): x.index("\2")+1]'  # x.account_name,amount
    numeric_range = r'x([\d]+),([\d]+)', r'x[int(\1):int(\2)+1]'  # x7,9
    numeric_range_start = r'x,([\d]+)', r'x[:int(\1)+1]'  # x,9
    numeric_range_end = r'x([\d]+),', r'x[int(\1):]'  # x7,
    numeric = r'x([\d]+)', r'x[\1]'  # x7
    templates = range, numeric_range, numeric_range_start, numeric_range_end, numeric
    # pdb.set_trace()
    return map(map(replace('x', prefix)))(templates)


def parse_command(cmd):
    '''
    no inputs
    for i in range(10):  if i > 3:    print(i);    print(i+1)
    -->
    for i in range(10):
        if i > 3:
            print(i)
            print(i+1)
    '''
    if not cmd:
        return identity

    # TODO: make indentation less annoying? curly braces?
    cmd = cmd.replace(':', ':;')
    cmd = '\n'.join(cmd.replace('  ', '\t').split(';'))
    cmd = make_regex_sub_function_string(cmd)
    cmd = make_regex_match_function_string(cmd)
    cmd = make_conditional_string(cmd)
    # dummy argument makes it work out better because signature matches the command2 case
    return lambda _: eval(cmd)


def parse_command0(cmd):
    if not cmd:
        return identity
    template = '''\
@curry
def f(k, v):
    p('parse_command0', k, v),
    K = str(k)
    V = str(v)
    ret = %s
    p('ret', ret)
    return ret'''
    return build(template, cmd)

def build(template, cmd):
    function_text = template % cmd
    assert 'def f(' in function_text
    function_text = make_regex_sub_function_string(function_text)
    function_text = make_regex_match_function_string(function_text)
    function_text = make_conditional_string(function_text)
    p('function_text', function_text)
    exec(compile(function_text, '<string>', 'exec'))
    ret = locals()['f']
    ret.code = function_text
    return ret


def parse_command1(cmd):
    if not cmd:
        return identity
    template = '''\
@curry
def f(i, d):
    p('parse_command1', i, d),
    if not type(d) is dict and type(i) is int:
        p(type(i), type(d))
        assert False
    k = list(d.keys())
    K = ''.join(map(str)(k)) # TODO use arguments.args.f or similar
    v = list(d.values())
    V = ''.join(map(str)(v)) # TODO use arguments.args.f or similar
    ret = %s
    p('k, v, ret', k, v, ret)
    return ret'''
    # TODO: if foo like bar, ie any(bar in f for f in foo)
    # TODO: handle case like xi.,foo by writing find(collection, symbol) ->
    # collection[collection.index(symbol) if symbol else 0 or -1 etc]
    made = make_subs(['k', 'K', 'v', 'V'])
    cmd = sub_all(cmd, flatten(made))
    return build(template, cmd)


def parse_command2(cmd):
    if not cmd:
        return lambda: None
    template = '''\
def f(d):
    p('parse_command2', d, type(d)),
    rk = list(d.keys())
    rK  = ''.join(map(str)(rk))
    rv = list(d.values())
    rV  = ''.join(map(str)(rv))
    ck = map(lambda d: list(d.keys()))(d.values())
    cK  = ''.join(map(str)(ck))
    cv = map(lambda d: list(d.values()))(d.values())
    cV  = ''.join(map(str)(cv))
    dv = sum(cv, [])
    dV  = ''.join(map(str)(dv))
    ret = %s
    p(rk, rv, ck, cv, dV)
    return ret'''
    # TODO: if foo like bar, ie any(bar in f for f in foo)
    # TODO: handle case like xi.,foo by writing find(collection, symbol) ->
    # collection[collection.index(symbol) if symbol else 0 or -1 etc]

    made = make_subs(('rk', 'rK', 'rv', 'rV', 'ck', 'cK', 'cv', 'cV', 'dv', 'dV'))
    cmd = sub_all(cmd, flatten(made))
    return build(template, cmd)



fps = map(parse_command0)(arguments.args.fp) + \
    make_predicates(arguments.args.fi, arguments.args.fix, arguments.args.fv, arguments.args.fvx)
ftps = map(parse_command0)(arguments.args.ftp) + \
    make_predicates(arguments.args.fti, arguments.args.ftix, arguments.args.ftv, arguments.args.ftvx)
fts = map(parse_command0)(arguments.args.ft)

rps = map(parse_command1)(arguments.args.rp) + \
    make_predicates(arguments.args.ri, arguments.args.rix, arguments.args.rv, arguments.args.rvx)
rtps = map(parse_command1)(arguments.args.rtp) + \
    make_predicates(arguments.args.rti, arguments.args.rtix, arguments.args.rtv, arguments.args.rtvx)
rts = map(parse_command1)(arguments.args.rt)

r20 = parse_command2(arguments.args.r20)
r21 = parse_command2(arguments.args.r21)
r10 = map(parse_command1)(arguments.args.r10)

if use_stdin_raw:
    cmds = compose(map(parse_command2)(arguments.args.c[1:]))  # command1 in streaming case?
elif use_stdin_py:
    cmds = compose(
            map(apply(None))(
                map(parse_command0)(
                    arguments.args.c[1:]
                    )
                )
            )
else:
    cmds = const(apply(None)(map(parse_command)(arguments.args.c))) # compose?
