from cid.utils import IsolatedParameters, get_parameters, set_parameters

def test_isolated_parameter_context():
    """ make sure the isolated_parameter works
    """
    set_parameters({'param': 'a'})

    with IsolatedParameters():
        set_parameters({'param': 'b'})
        assert get_parameters().get('param') == 'b', 'parameters within context must be B'

    assert get_parameters().get('param') == 'a', 'parameters within context must be A'
