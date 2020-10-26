from ..sequence import SequenceModel

labels = ["Step 1", "Step 2", "Step 3", "Step 4"]


def test_sequence_model():
    """Test instantiating sequence model."""
    model = SequenceModel(labels)

    expected_state = {"index": 0, "label": "Step 1", "first": True, "last": False}
    assert model.state == expected_state


def test_sequence_model_step_next():
    """Test sequence model stepping next"""
    model = SequenceModel(labels)
    model.move_next()

    expected_state = {"index": 1, "label": "Step 2", "first": False, "last": False}
    assert model.state == expected_state


def test_sequence_model_step_back():
    """Test sequence model stepping back"""
    model = SequenceModel(labels)
    model.index = 1
    model.move_back()

    expected_state = {"index": 0, "label": "Step 1", "first": True, "last": False}
    assert model.state == expected_state


def test_sequence_model_steps_forward_multiple():
    """Test sequence model until the end"""
    model = SequenceModel(labels)
    for _ in range(10):
        model.move_next()

    expected_state = {"index": 3, "label": "Step 4", "first": False, "last": True}
    assert model.state == expected_state


def test_sequence_model_steps_backward_multiple():
    """Test sequence model from end until the beginning"""
    model = SequenceModel(labels)
    model.index = 3
    for _ in range(10):
        model.move_back()

    expected_state = {"index": 0, "label": "Step 1", "first": True, "last": False}
    assert model.state == expected_state
