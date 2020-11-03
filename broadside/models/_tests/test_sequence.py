from ..sequence import SequenceModel


def test_sequence_model():
    """Test instantiating sequence model."""
    model = SequenceModel(4)

    expected_state = {"index": 0, "first": True, "last": False}
    assert model.state == expected_state


def test_sequence_model_step_next():
    """Test sequence model stepping next"""
    model = SequenceModel(4)
    model.move_next()

    expected_state = {"index": 1, "first": False, "last": False}
    assert model.state == expected_state


def test_sequence_model_step_back():
    """Test sequence model stepping back"""
    model = SequenceModel(4)
    model.index = 1
    model.move_back()

    expected_state = {"index": 0, "first": True, "last": False}
    assert model.state == expected_state


def test_sequence_model_steps_forward_multiple():
    """Test sequence model until the end"""
    model = SequenceModel(4)
    for _ in range(10):
        model.move_next()

    expected_state = {"index": 3, "first": False, "last": True}
    assert model.state == expected_state


def test_sequence_model_steps_backward_multiple():
    """Test sequence model from end until the beginning"""
    model = SequenceModel(4)
    model.index = 3
    for _ in range(10):
        model.move_back()

    expected_state = {"index": 0, "first": True, "last": False}
    assert model.state == expected_state
