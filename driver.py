import arguments
from logger import p
import sys
import mawk
from mawk import process
import formatter
import functionmaker
import test

# Fix for broken pipe error I don't quite eunderstand
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE, SIG_DFL)


def init(x=None):
    global args, use_stdin_raw, use_stdin_py, get_input, write_out, format_output, cmds
    arguments.init(x)
    from arguments import args
    p(args)
    formatter.init()
    from formatter import use_stdin_raw, use_stdin_py, get_input, write_out, format_output
    # TODO: need to reimport the functions?
    functionmaker.init()
    from functionmaker import cmds
    mawk.init()
    test.init()


def main(x=None):
    init(x)
    stdin = sys.stdin if not args.test else test.mock_stdin
    if use_stdin_raw or use_stdin_py:  # TODO clean this up
        if args.s:
            for ri, raw in enumerate(get_input(stdin)):
                if use_stdin_raw:
                    kept, transformed, reduced, formatted = process(raw, ri)
                    write_out(formatted)
                    return kept, transformed, reduced, formatted
                else:  # use_stdin_py
                    out = cmds((ri, eval(raw)))
                    p('out', out)
                    formatted = format_output(out)
                    write_out(formatted)
                    return None, None, None, formatted
        else:
            raw = get_input(stdin)
            if use_stdin_raw:
                kept, transformed, reduced, formatted = process(raw)
                write_out(formatted)
                return kept, transformed, reduced, formatted
            else:  # use_stdin_py
                out = cmds((None, eval(raw)))
                p('out', out)
                formatted = format_output(out)
                write_out(formatted)
                return None, None, None, formatted
    else:
        out = cmds(None)
        write_out(out)  # TODO is it going to be a problem that I'm passing a dummy arugment?
        return None, None, None, out


if __name__ == '__main__':
    kept, transformed, reduced, formatted = main()