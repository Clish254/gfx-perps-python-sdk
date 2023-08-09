# LOCK-BEGIN[imports]: DON'T MODIFY
from .fractional import Fractional
from podite import (
    U64,
    pod,
)

# LOCK-END


# LOCK-BEGIN[class(OpenOrdersMetadata)]: DON'T MODIFY
@pod
class OpenOrdersMetadata:
    ask_qty_in_book: "Fractional"
    bid_qty_in_book: "Fractional"
    head_index: U64
    num_open_orders: U64
    # LOCK-END

    @classmethod
    def to_bytes(cls, obj, **kwargs):
        return cls.pack(obj, converter="bytes", **kwargs)

    @classmethod
    def from_bytes(cls, raw, **kwargs):
        return cls.unpack(raw, converter="bytes", **kwargs)
