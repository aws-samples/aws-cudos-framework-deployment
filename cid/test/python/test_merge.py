from cid.utils import merge_objects


def test_merge_objects():
    """ make sure the merge works with depth
    """

    obj1 = {'a': {'b': {'c1': 1}, 'c': 3}}
    obj2 = {'a': {'b': {'c2': 1}, 'd': {'e': 2}}}

    assert merge_objects(obj1, obj2, depth=0) == obj2
    assert merge_objects(obj1, obj2, depth=1) == {
        'a': {
            'b': { 'c2': 1},
            'c': 3,
            'd': {'e': 2}
        }
    }
    assert merge_objects(obj1, obj2, depth=2) == {
        'a': {
            'b': { 'c1': 1, 'c2': 1},
            'c': 3,
            'd': {'e': 2}
        }
    }