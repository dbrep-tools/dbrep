import pytest

import dbrep.utils


def test_test_output_type():
    with pytest.raises(TypeError):
        dbrep.utils.test_output_type({})
    with pytest.raises(TypeError):
        dbrep.utils.test_output_type((None,))
    with pytest.raises(TypeError):
        dbrep.utils.test_output_type([(None,)])
    with pytest.raises(TypeError):
        dbrep.utils.test_output_type('test')
    with pytest.raises(TypeError):
        dbrep.utils.test_output_type(['test'])
    with pytest.raises(TypeError):
        dbrep.utils.test_output_type([('test', )])
    assert dbrep.utils.test_output_type([]) is None
    assert dbrep.utils.test_output_type([[]]) is None
    assert dbrep.utils.test_output_type([['test']]) is None
    assert dbrep.utils.test_output_type([['test'], [1], [3]]) is None

def test_test_unique_key():
    with pytest.raises(ValueError):
        dbrep.utils.test_unique_key([[0], [0]])
    with pytest.raises(ValueError):
        dbrep.utils.test_unique_key([[0], [1], [None]])
    with pytest.raises(ValueError):
        dbrep.utils.test_unique_key([[0], [0, '0']])
    assert dbrep.utils.test_unique_key([[0], ['0']]) is None
    assert dbrep.utils.test_unique_key([[0], [1, '0']]) is None

def test_merge_outputs():
    assert dbrep.utils.merge_outputs([], []) == []
    assert dbrep.utils.merge_outputs([[0]], []) == [[(0, None)]]
    assert dbrep.utils.merge_outputs([[0]], [[1]]) == [[(0, None)], [(None, 1)]]

    assert dbrep.utils.merge_outputs([[0, 'a']], [[0, 'b']]) == [[(0, 0), ('a', 'b')]]
    assert dbrep.utils.merge_outputs([[0, 'a'], [2, 'c']], [[0, 'b']]) == [[(0, 0), ('a', 'b')], [(2, None), ('c', None)]]
    
    assert dbrep.utils.merge_outputs([[0]], [[1, 'a']]) == [[(0, None)], [(None, 1), (None, 'a')]]

def test_gather_exceptions_const():
    def fn_raise(arg): raise ValueError(42)
    assert dbrep.utils.gather_exceptions([[('a', 'a')]], fn_raise) == [[(ValueError, (42,))]]
    assert dbrep.utils.gather_exceptions([[('a', 'a'), ('a', 'a')]], fn_raise) == [[(ValueError, (42,)), (ValueError, (42,))]]
    assert dbrep.utils.gather_exceptions([[('a', 'a')], [('a', 'a')]], fn_raise) == [[(ValueError, (42,))], [(ValueError, (42,))]]


def test_gather_exceptions_conditional():
    def fn_raise(arg):
        if arg[0] > 10:
            raise ValueError(42)
    assert dbrep.utils.gather_exceptions([[(9, 0)]], fn_raise) == [[None]]
    assert dbrep.utils.gather_exceptions([[(11, 0)]], fn_raise) == [[(ValueError, (42,))]]
    
    assert dbrep.utils.gather_exceptions([[(11, 0), (9, 0)]], fn_raise) == [[(ValueError, (42,)), None]]
    assert dbrep.utils.gather_exceptions([[(9, 0), (11, 0)]], fn_raise) == [[None, (ValueError, (42,))]]
    assert dbrep.utils.gather_exceptions([[(11, 0)], [(9, 0)]], fn_raise) == [[(ValueError, (42,))], [None]]

def test_agg_row_stats():
    assert dbrep.utils.agg_row_stats([]) == []
    assert dbrep.utils.agg_row_stats([[None]]) == [set()]
    assert dbrep.utils.agg_row_stats([[1, None]]) == [set([1])]
    assert dbrep.utils.agg_row_stats([[1, 1]]) == [set([1])]
    assert dbrep.utils.agg_row_stats([[1, 2]]) == [set([1, 2])]
    assert dbrep.utils.agg_row_stats([[1, 1], [None, None]]) == [set([1]), set()]
    assert dbrep.utils.agg_row_stats([[None, 1], [None, None]]) == [set([1]), set()]
    assert dbrep.utils.agg_row_stats([[1, 1], [2, None]]) == [set([1]), set([2])]
    

def test_agg_col_stats():
    assert dbrep.utils.agg_col_stats([]) == []
    assert dbrep.utils.agg_col_stats([[None]]) == [set()]
    assert dbrep.utils.agg_col_stats([[1, None]]) == [set([1]), set()]
    assert dbrep.utils.agg_col_stats([[1, 1]]) == [set([1]), set([1])]
    assert dbrep.utils.agg_col_stats([[1, 2]]) == [set([1]), set([2])]
    assert dbrep.utils.agg_col_stats([[1, 1], [None, None]]) == [set([1]), set([1])]
    assert dbrep.utils.agg_col_stats([[None, 1], [None, None]]) == [set(), set([1])]
    assert dbrep.utils.agg_col_stats([[1, 1], [2, None]]) == [set([1, 2]), set([1])]


def test_agg_all_stats():
    assert dbrep.utils.agg_all_stats([]) == set()
    assert dbrep.utils.agg_all_stats([[None]]) == set()
    assert dbrep.utils.agg_all_stats([[1, None]]) == set([1])
    assert dbrep.utils.agg_all_stats([[1, 1]]) == set([1])
    assert dbrep.utils.agg_all_stats([[1, 2]]) == set([1,2])
    assert dbrep.utils.agg_all_stats([[1, 1], [None, None]]) == set([1])
    assert dbrep.utils.agg_all_stats([[None, 1], [None, None]]) == set([1])
    assert dbrep.utils.agg_all_stats([[1, 1], [2, None]]) == set([1,2])

def test_run_tests_const():
    def fn_raise(arg): raise ValueError(42)
    with pytest.raises(Exception):
        dbrep.utils.run_tests([[('a', 'a')]], fn_raise, report_cols=True)
    with pytest.raises(Exception):
        dbrep.utils.run_tests([[('a', 'a')]], fn_raise, report_cols=False)
    with pytest.raises(Exception):
        dbrep.utils.run_tests([[('a', 'a'), ('b', 'b')], [('c', 'c')]], fn_raise, report_cols=True)
    with pytest.raises(Exception):
        dbrep.utils.run_tests([[('a', 'a'), ('b', 'b')], [('c', 'c')]], fn_raise, report_cols=False)


def test_run_tests_conditional():
    def fn_raise(arg):
        if arg[0] > 10:
            raise ValueError(42)
    with pytest.raises(Exception):
        dbrep.utils.run_tests([[(12, 0)]], fn_raise, report_cols=True)
    with pytest.raises(Exception):
        dbrep.utils.run_tests([[(12, 0)]], fn_raise, report_cols=True)
    assert dbrep.utils.run_tests([[(8, 0)]], fn_raise, report_cols=True) is None
    assert dbrep.utils.run_tests([[(8, 0)]], fn_raise, report_cols=False) is None

    with pytest.raises(Exception):
        dbrep.utils.run_tests([[(8, 0), (8, 0)], [(12, 0)]], fn_raise, report_cols=True)
    with pytest.raises(Exception):
        dbrep.utils.run_tests([[(8, 0), (8, 0)], [(12, 0)]], fn_raise, report_cols=False)
    with pytest.raises(Exception):
        dbrep.utils.run_tests([[(8, 0), (12, 0)], [(6, 0)]], fn_raise, report_cols=True)
    with pytest.raises(Exception):
        dbrep.utils.run_tests([[(8, 0), (12, 0)], [(6, 0)]], fn_raise, report_cols=False)
    assert dbrep.utils.run_tests([[(8, 0), (9, 0)], [(6, 0)]], fn_raise, report_cols=True) is None
    assert dbrep.utils.run_tests([[(8, 0), (9, 0)], [(6, 0)]], fn_raise, report_cols=False) is None

def test_test_elem_typing():
    with pytest.raises(TypeError):
        dbrep.utils.test_elem_typing(None)
    with pytest.raises(TypeError):
        dbrep.utils.test_elem_typing(['a'])
    with pytest.raises(TypeError):
        dbrep.utils.test_elem_typing([])
    with pytest.raises(TypeError):
        dbrep.utils.test_elem_typing({})
    with pytest.raises(TypeError):
        dbrep.utils.test_elem_typing((1,))
    assert dbrep.utils.test_elem_typing((1,2)) is None
    assert dbrep.utils.test_elem_typing((1,None)) is None
    assert dbrep.utils.test_elem_typing((None,None)) is None
    assert dbrep.utils.test_elem_typing((1,'b')) is None

    
def test_test_elem_none():
    with pytest.raises(ValueError):
        dbrep.utils.test_elem_none((None, 1))
    with pytest.raises(ValueError):
        dbrep.utils.test_elem_none((1, None))
    with pytest.raises(ValueError):
        dbrep.utils.test_elem_none((None, 'None'))
    assert dbrep.utils.test_elem_none((1,2)) is None
    assert dbrep.utils.test_elem_none((None,None)) is None
    assert dbrep.utils.test_elem_none((1,'b')) is None

def test_test_elem_type():
    with pytest.raises(TypeError):
        dbrep.utils.test_elem_type((None, 1))
    with pytest.raises(TypeError):
        dbrep.utils.test_elem_type((1, None))
    with pytest.raises(TypeError):
        dbrep.utils.test_elem_type((1, 1.0))
    with pytest.raises(TypeError):
        dbrep.utils.test_elem_type((1.0, 1))
    with pytest.raises(TypeError):
        dbrep.utils.test_elem_type((1.0, '1'))
    with pytest.raises(TypeError):
        dbrep.utils.test_elem_type((1, '1'))
    with pytest.raises(TypeError):
        dbrep.utils.test_elem_type(([], {}))
    assert dbrep.utils.test_elem_type((1, -1)) is None
    assert dbrep.utils.test_elem_type((1.0, -1.0)) is None
    assert dbrep.utils.test_elem_type(('qwe', 'asd')) is None
    assert dbrep.utils.test_elem_type(({}, {'a': 8})) is None
    assert dbrep.utils.test_elem_type(([], [1,2,3])) is None


def test_test_elem_value():
    with pytest.raises(ValueError):
        dbrep.utils.test_elem_value((None, 1))
    with pytest.raises(ValueError):
        dbrep.utils.test_elem_value((1.2, 1))
    with pytest.raises(ValueError):
        dbrep.utils.test_elem_value((3, 1))
    with pytest.raises(ValueError):        
        dbrep.utils.test_elem_value((1.0, '1.0'))
    with pytest.raises(ValueError):        
        dbrep.utils.test_elem_value((1, '1'))
    assert dbrep.utils.test_elem_value((1.0, 1)) is None
    assert dbrep.utils.test_elem_value((1, 1)) is None
    assert dbrep.utils.test_elem_value(('1', '1')) is None
    assert dbrep.utils.test_elem_value((None, None)) is None