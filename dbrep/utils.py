

from typing import Any, Callable, List, Set, Tuple


def test_output_type(out) -> None:
    if out is None:
        raise TypeError('Output should be of type List[List[Any]], but got None')
    if not isinstance(out, list):
        raise TypeError('Output should be of type List[List[Any]], but got {}'.format(type(out)))
    if not all([isinstance(x, list) for x in out]):
        raise TypeError('Output should be of type List[List[Any]], but got {}'.format(set([type(x) for x in out if not isinstance(x, list)])))
    return   

def test_unique_key(out: List[List[Any]]) -> None:
    v0 = [x[0] for x in out] #Should raise if in some case length is 0
    if any([x is None for x in v0]):
        raise ValueError('Key in output should not be None!')
    if len(v0) != len(set(v0)):
        raise ValueError('Key should be unique, but got duplicates!')
    return

def merge_outputs(out1: List[List[Any]], out2: List[List[Any]]) -> List[List[Tuple[Any, Any]]]:
    def merge_row(r1, r2):
        if r1 is None and r2 is None:
            raise ValueError('Both rows can not be None!')
        if r1 is None or r2 is None:
            if r1 is None:
                return [(None, x) for x in r2]
            else:
                return [(x, None) for x in r1]
        if len(r1) != len(r2):
            raise ValueError('Both rows should have the same length!')
        return list(zip(r1, r2))

    all_keys = set.union(set(x[0] for x in out1), set(x[0] for x in out2))
    d1 = {x[0]: x for x in out1}
    d2 = {x[0]: x for x in out2}
    return [merge_row(d1.get(k), d2.get(k)) for k in all_keys]


def gather_exceptions(input: List[List[Tuple[Any, Any]]], test: Callable[[Tuple[Any, Any]], None]) -> List[List[Any]]:
    def gather_exc_(x: Tuple[Any, Any]) -> Any:
        try:
            test(x)
            return None
        except Exception as e:
            return type(e), e.args #if return just e it would not compare to itself and won't produce set
    return [[gather_exc_(x) for x in row] for row in input]

def agg_row_stats(input: List[List[Any]]) -> List[Set[Any]]:
    return [set(x for x in row if x is not None) for row in input]

def agg_col_stats(input: List[List[Any]]) -> List[Set[Any]]:
    if len(input) == 0:
        return []
    num_cols = len(input[0])
    return [set(r[i] for r in input if r[i] is not None) for i in range(num_cols)]

def agg_all_stats(input: List[List[Any]]) -> Set[Any]:
    return set(x for row in input for x in row if x is not None)

def run_tests(input: List[List[Tuple[Any, Any]]], test: Callable[[Tuple[Any, Any]], None], report_cols : bool = False):
    def format_exc_(exc):
        exc_type, exc_args = exc
        return '{}({})'.format(exc_type, '.'.join(exc_args))
    def format_exc_set_(excs):
        if len(excs) == 0:
            return '[]'
        return '[{}]'.format(', '.join(format_exc_(x) for x in excs))
    res = gather_exceptions(input, test)
    total = agg_all_stats(res)
    if len(total) == 0:
        return
    report = 'Triggered exceptions: {}'.format(format_exc_set_(total))
    if report_cols:
        cols = agg_col_stats(res)
        report += '\nExceptions by cols:\n{}'.format('\n'.join(format_exc_set_(x) for x in cols))
    raise Exception(report)

def test_elem_typing(input: Tuple[Any, Any]):
    if not isinstance(input, tuple):
        raise TypeError('Element should be tuple of length=2, but got type={}'.format(type(input)))
    if len(input) != 2:
        raise TypeError('Element should be tuple of length=2, but got length={}'.format(len(input)))
    return

def test_elem_none(input: Tuple[Any, Any]):
    a, b = input
    if a is None and b is None:
        return
    if a is None or b is None:
        raise ValueError('One elem is None, while other is not')
    return

def test_elem_type(input: Tuple[Any, Any]):
    a, b = input
    if type(a) != type(b):
        raise TypeError('Types differ: {} vs {}'.format(type(a), type(b)))
    return

def test_elem_value(input: Tuple[Any, Any]):
    a, b = input
    if a != b:
        raise ValueError('Values differ: {} vs {}'.format(a, b))
    return