import dbrep.config
import copy

def test_make_config_empty():
    assert dbrep.config.make_config(None) == {}
    assert dbrep.config.make_config([]) == {}


def test_make_config_single_level():
    assert dbrep.config.make_config([('a', 1), ('b', 2)]) == {'a': 1, 'b': 2}
    assert dbrep.config.make_config([['c', 1]]) == {'c': 1}

def test_make_config_multi_level():
    assert dbrep.config.make_config([('a.a', 1), ('a.b', 2), ('b', 3)]) == {'a': {'a':1, 'b': 2}, 'b': 3}
    assert dbrep.config.make_config([('a.b', 1), ('b.a', 2)]) == {'a': {'b':1}, 'b': {'a': 2}}

def test_merge_config_empty():
    assert dbrep.config.merge_config() == {}
    assert dbrep.config.merge_config({}) == {}
    assert dbrep.config.merge_config(None) == {}
    assert dbrep.config.merge_config({}, {}) == {}
    assert dbrep.config.merge_config(None, {}) == {}
    assert dbrep.config.merge_config({}, None) == {}
    assert dbrep.config.merge_config(None, None) == {}


def test_merge_config_simple():
    d1 = {'a': 1, 'b': 2, 'c': {'a':-1, 'b': -2}}
    d1c = copy.deepcopy(d1)
    
    d2 = {'a': 11, 'd': 3, 'c': {'a': {'q': 7}, 'd': -7}}
    d2c = copy.deepcopy(d2)

    d12 = {'a': 11, 'b':2, 'd': 3, 'c':{'a': {'q': 7}, 'd': -7, 'b': -2}}
    d21 = {'a': 1, 'b':2, 'd': 3, 'c':{'a': -1, 'd': -7, 'b': -2}}

    assert dbrep.config.merge_config(d1) == d1c
    assert dbrep.config.merge_config({}, d1) == d1c
    assert dbrep.config.merge_config(d1, {}) == d1c
    assert dbrep.config.merge_config(d1, d1) == d1c
    assert d1 == d1c

    assert dbrep.config.merge_config(d1, d2) == d12
    assert dbrep.config.merge_config(d2, d1) == d21
    assert d1 == d1c
    assert d2 == d2c
    
    assert dbrep.config.merge_config({}, d1, d2) == d12
    assert dbrep.config.merge_config(d1, {}, d2) == d12
    assert dbrep.config.merge_config(d1, d2, {}) == d12
    assert dbrep.config.merge_config(d1, d2, d1) == d21
    assert dbrep.config.merge_config(d1, d1, d2) == d12
    assert dbrep.config.merge_config(d2, d1, d1) == d21
    assert dbrep.config.merge_config(d2, d1, d2) == d12

def test_flatten_empty():
    assert dbrep.config.flatten_config(None) == {}
    assert dbrep.config.flatten_config({}) == {}

def test_flatten_single_level():
    assert dbrep.config.flatten_config({'a': 1, 'b': 2}) == {'a':1, 'b': 2}

def test_flatten_multi_level():
    assert dbrep.config.flatten_config({'a': 1, 'b': {'a': 2, 'b': 3}}) == {'a':1, 'b.a': 2, 'b.b': 3}

def test_template():
    assert dbrep.config.TemplateDotted('${ab}').safe_substitute({'ab': '0'}) == '0'
    assert dbrep.config.TemplateDotted('${a@b}').safe_substitute({'a@b': '0'}) == '0'
    assert dbrep.config.TemplateDotted('${a-b}').safe_substitute({'a-b': '0'}) == '0'
    assert dbrep.config.TemplateDotted('${a.b}').safe_substitute({'a.b': '0'}) == '0'
    assert dbrep.config.TemplateDotted('${a_b}').safe_substitute({'a_b': '0'}) == '0'
    assert dbrep.config.TemplateDotted('${a+b}').safe_substitute({'a+b': '0'}) == '${a+b}'
    assert dbrep.config.TemplateDotted('${a*b}').safe_substitute({'a*b': '0'}) == '${a*b}'
    assert dbrep.config.TemplateDotted('${a#b}').safe_substitute({'a#b': '0'}) == '${a#b}'
    assert dbrep.config.TemplateDotted('${a%b}').safe_substitute({'a%b': '0'}) == '${a%b}'

def test_substitute_config_empty():
    assert dbrep.config.substitute_config({}) == {}
    assert dbrep.config.substitute_config(None) == {}

def test_substitute_config_simple():
    assert dbrep.config.substitute_config({'a':1, 'b':2}) == {'a':1, 'b':2}
    assert dbrep.config.substitute_config({'a':1, 'b':{'a':2, 'b': 3}}) == {'a':1, 'b':{'a':2, 'b': 3}}


def test_substitute_config_complex():
    assert dbrep.config.substitute_config({'a':'${b}', 'b':2}) == {'a':'2', 'b':2}
    assert dbrep.config.substitute_config({'a':'${b.a}', 'b':{'a':2, 'b': 3}}) == {'a':'2', 'b':{'a':2, 'b': 3}}

def test_unflatten():
    assert dbrep.config.unflatten_config({'a.b': 3}) == {'a': {'b': 3}}
    assert dbrep.config.unflatten_config([{'a.b': 3}, {'a.b': 4}]) == [{'a': {'b': 3}}, {'a': {'b': 4}}]
    assert dbrep.config.unflatten_config({'q':{'a.b': 3}}) == {'q':{'a': {'b': 3}}}