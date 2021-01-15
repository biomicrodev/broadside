import numpy as np
from napari.layers import Layer
from napari.utils.events import Event


class Bows(Layer):
    """Bows layer.

    Parameters
    ----------
    data : array (N, 2)
        Coordinates for N bows (only in 2 dims).
    """

    def __init__(
        self,
        data=None,
        *,
        properties=None,
        text=None,
        edge_width=1,
        edge_color="black",
        n_dimensional=False,
        name=None,
        metadata=None,
        scale=None,
        translate=None,
        rotate=None,
        shear=None,
        affine=None,
        opacity=1,
        blending="translucent",
        visible=True
    ):
        ndim = 2
        if data is None:
            data = np.empty((0, ndim))
        else:
            data = np.atleast_2d(data)
            data_ndim = data.shape[1]
            if data_ndim != 2:
                raise ValueError("Bows dimensions must be 2!")

        super().__init__(
            data,
            ndim,
            name=name,
            metadata=metadata,
            scale=scale,
            translate=translate,
            rotate=rotate,
            shear=shear,
            affine=affine,
            opacity=opacity,
            blending=blending,
            visible=visible,
        )

        self.events.add(edge_width=Event)
