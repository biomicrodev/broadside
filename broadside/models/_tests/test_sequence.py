from ..sequence import SequenceModel

labels = ["Step 1", "Step 2", "Step 3", "Step 4"]


def test_sequence_model():
    """Test instantiating sequence model."""
    model = SequenceModel(labels)

    assert model.index == 0
    assert model.first is True
    assert model.last is False


def test_sequence_model_step_next():
    """Test sequence model stepping next"""
    model = SequenceModel(labels)
    model.move_next()

    assert model.index == 1
    assert model.first is False
    assert model.last is False
    assert model.label == "Step 2"


def test_sequence_model_step_back():
    """Test sequence model stepping back"""
    model = SequenceModel(labels)
    model.index = 1
    model.move_back()

    assert model.index == 0
    assert model.first is True
    assert model.last is False
    assert model.label == "Step 1"


def test_sequence_model_steps_forward_multiple():
    """Test sequence model until the end"""
    model = SequenceModel(labels)
    for _ in range(10):
        model.move_next()

    assert model.index == 3
    assert model.first is False
    assert model.last is True
    assert model.label == "Step 4"


def test_sequence_model_steps_backward_multiple():
    """Test sequence model from end until the beginning"""
    model = SequenceModel(labels)
    model.index = 3
    for _ in range(10):
        model.move_back()

    assert model.index == 0
    assert model.first is True
    assert model.last is False
    assert model.label == "Step 1"
