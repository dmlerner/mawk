def parse(raw_records, ri_start=0):
    p('parse', repr(raw_records), ri_start)
    records = dict_vmap(index_dict)(
        dict_kmap(add(ri_start))(
            index_dict(map(map(field_type))(
                map(split(args.f, args.fx, args.fc))(
                    filter(identity)(
                        split(raw_records.strip(), args.r, args.rx, args.rc)
                    ))))))
    kept = filter_records(records, fps, rps)  # TODO: move to mawk
    return kept


def field_type(x):
    return eval(args.t)(x) if x is not None else None


def record_iterator(x, delim):  # TODO is this actually correct; probalby yes
    cache = []
    for line in x:
        # line += '\n'
        records = line.split(delim)
        cache.append(records[0])
        for record in records[1:]:
            if cache:
                to_yield = ''.join(cache)
                cache = [record]
                yield to_yield


def format_output(reduced):
    if args.p:
        return repr(reduced)
    try:
        if out_rank == 2:
            if not args.fx:
                reduced = map(vmap(replace(args.f, '')))(reduced)
            reduced = vmap(join(args.F))(reduced)
            if not args.rx:
                reduced = vmap(replace(args.r, ''))(reduced)
            return join(args.R)(reduced)
        if out_rank == 1:
            if not args.rx:
                reduced = '?'
            return vmap(join(args.R))(reduced)
        return str(reduced)
    except BaseException:
        p('format_output error')
        return str(reduced)


def write_out(x):
    x = str(x).strip()
    if x:
        print(x)


def out_rank(args):
    out_rank = 2
    if args.r20:
        assert not args.r21 and not args.r10
        out_rank = 0
    opts = (args.r21, *args.r10)
    out_rank -= sum(map(bool)(opts))
    assert out_rank >= 0
    return out_rank


class Formatter:
    def __init__(self, args):
        self.args = args
        self.use_stdin_raw = args.c and args.c[0] == '-'
        self.use_stdin_py = args.c and args.c[0] == '.'
        self.out_rank = out_rank(args)
