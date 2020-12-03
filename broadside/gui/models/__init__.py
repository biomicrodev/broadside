from typing import Dict, Any


class Serializable:
    def as_dict(self) -> Dict[str, Any]:
        """
        Convert object to dict. The value can be of Any type; it is up to the final
        serializer to make sure that everything is processed properly in one go, unless
        it is particularly unusual.
        """
        raise NotImplementedError

    @classmethod
    def from_dict(cls, dct: Dict[str, str]):
        """
        Convert dict to object. This is where conversion to the proper types is
        important, and that is up to the individual class, which is why this is a
        classmethod.
        """
        raise NotImplementedError
