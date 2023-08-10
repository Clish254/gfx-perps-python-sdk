#from solana.publickey import PublicKey
from solana.rpc.api import Client
from typing import List, TypedDict
from dataclasses import dataclass, field
from .constants import perps_constants
from .types import (MarketProductGroup, Solana_pubkey)
from enum import Enum
from solana.publickey import PublicKey
from solana.keypair import Keypair
import base64

class NETWORK_TYPE(Enum):
    devnet = "devnet"
    mainnet = "mainnet"

class TradeSide(Enum):
    buy = "buy"
    sell = "sell"

class OrderType(Enum):
    limit = "limit"
    market = "market"
    immediateOrCancel = "immediateOrCancel"
    postOnly = "postOnly"

class Product_Type(TypedDict):
    name: str
    PRODUCT_ID: PublicKey
    ORDERBOOK_ID: PublicKey
    BIDS: PublicKey
    ASKS: PublicKey
    EVENT_QUEUE: PublicKey
    tick_size: int
    decimals: int
@dataclass
class ConstantIDs:
    MPG_ID: PublicKey
    DEX_ID: PublicKey
    INSTRUMENTS_ID: PublicKey
    FEES_ID: PublicKey
    RISK_ID: PublicKey
    ORDERBOOK_P_ID: PublicKey
    PYTH_MAINNET: PublicKey
    PYTH_DEVNET: PublicKey
    VAULT_MINT: PublicKey
    VAULT_SEED: str
    FEES_SEED: str
    TRADER_FEE_ACCT_SEED: str
    BUDDY_LINK_PROGRAM: PublicKey
    PRODUCTS: List[Product_Type] = field(default_factory=list)
class Perp:
    marketProductGroup: MarketProductGroup
    mpgBytes: bytes
    connection: Client
    program: str #TODO: Change
    wallet: Keypair 
    networkType: NETWORK_TYPE
    ADDRESSES: ConstantIDs

    def __init__(self, connection: Client, 
      network_type: NETWORK_TYPE, 
      wallet: Keypair, 
      mpg: MarketProductGroup = None, 
      mpgBytes: bytes = None):
      self.wallet = wallet
      self.connection = connection
      self.networkType = network_type
      if self.networkType == "mainnet":
          self.ADDRESSES = perps_constants.ADDRESSES['MAINNET']
      elif self.networkType == "devnet":
          self.ADDRESSES = perps_constants.ADDRESSES['DEVNET']
      if mpg:
          self.marketProductGroup = mpg
      if mpgBytes:
          self.mpgBytes = mpgBytes

    async def init(self):
        mpgId = self.ADDRESSES["MPG_ID"]
        response = self.connection.get_account_info(PublicKey(mpgId))
        try:
          r = response['result']['value']['data'][0]
          decoded = base64.b64decode(r)[8:]
          mpg = MarketProductGroup.from_bytes(decoded)
          self.marketProductGroup = mpg
          self.mpgBytes = decoded
        except:
          raise KeyError("Wrong Market Product Group PublicKey")