# LOCK-BEGIN[imports]: DON'T MODIFY
from .fractional import Fractional
from .price_ewma import PriceEwma
from .solana_pubkey import Solana_pubkey
from podite import (
    FixedLenArray,
    U64,
    U8,
    pod,
)

# LOCK-END


# LOCK-BEGIN[class(ProductMetadata)]: DON'T MODIFY
@pod
class ProductMetadata:
    bump: U64
    product_key: Solana_pubkey
    name: FixedLenArray[U8, 16]
    orderbook: Solana_pubkey
    tick_size: "Fractional"
    base_decimals: U64
    price_offset: "Fractional"
    contract_volume: "Fractional"
    prices: PriceEwma
    # LOCK-END

    @classmethod
    def to_bytes(cls, obj, **kwargs):
        return cls.pack(obj, converter="bytes", **kwargs)

    @classmethod
    def from_bytes(cls, raw, **kwargs):
        return cls.unpack(raw, converter="bytes", **kwargs)
