from cid.utils import IsolatedParameters, get_parameters, set_parameters

def test_isolated_parameter_context():
    """ make sure the merge works with depth
    """
    set_parameters({'a': 'a'})
    with IsolatedParameters():
        set_parameters({'a': 'b'})
        assert get_parameters().get('a') == 'b', 'parameters within context must be B'
    assert get_parameters().get('a') == 'a', 'parameters within context must be A'