from solana.publickey import PublicKey
from solana.keypair import Keypair
from solana.transaction import Transaction
from solana.system_program import (SYS_PROGRAM_ID, create_account, CreateAccountParams)
from typing import Union
from .perp import Perp
from .product import Product
from .types import (TraderRiskGroup, Fractional, Solana_pubkey, base, OrderType)
import utils
from dataclasses import dataclass, field
import base64
from solana.rpc import types
from .instructions.initialize_trader_risk_group import initialize_trader_risk_group
from .instructions.deposit_funds import (deposit_funds, DepositFundsParams)
from .instructions.withdraw_funds import (withdraw_funds, WithdrawFundsParams)
from .instructions.new_order import (new_order, NewOrderParams)
from .instructions.cancel_order import (cancel_order, CancelOrderParams)

class TraderPosition:
    quantity: str
    averagePrice: str
    index: str

class Trader(Perp):
    traderRiskGroup: TraderRiskGroup
    trgBytes: bytes
    trgKey: PublicKey
    userTokenAccount: PublicKey
    marketProductGroupVault: PublicKey
    totalDeposited: str
    totalWithdrawn: str
    marginAvailable: str
    traderPositions: any
    totalTradedVolume: str

    def __init__(self, perp: Perp):
        super(Trader,self).__init__(
            perp.connection,
            perp.networkType,
            perp.wallet,
            perp.marketProductGroup,
            perp.mpgBytes
        )

    def create_trader_account_ixs(self):
        trgAddress = utils.getTraderRiskGroup(self.wallet.public_key, self.connection, self.ADDRESSES["DEX_ID"], self.ADDRESSES["MPG_ID"])
        if trgAddress != None:
            raise KeyError("Trader Risk Group already exists for this wallet")

        trg = Keypair.generate()
        trader_risk_state_acct=Keypair.generate()
        ix1 = utils.initialize_trader_fee_acct(
            self.wallet.public_key, 
            self.ADDRESSES["MPG_ID"],
            self.ADDRESSES["FEES_ID"],
            trg.public_key,
            SYS_PROGRAM_ID,
            None
        )
        crParams = CreateAccountParams(from_pubkey=self.wallet.public_key, 
                                       new_account_pubkey=trg.public_key,
                                       lamports=96600000, space=13744,
                                        program_id=self.ADDRESSES["DEX_ID"] )
        ix2 = create_account(crParams)
        ix3 = initialize_trader_risk_group(
            owner=self.wallet.public_key,
            trader_risk_group=trg.public_key,
            market_product_group=self.ADDRESSES["MPG_ID"],
            risk_signer=utils.getRiskSigner(self.ADDRESSES["MPG_ID"], self.ADDRESSES["DEX_ID"]),
            trader_risk_state_acct=trader_risk_state_acct.public_key,
            trader_fee_state_acct=utils.get_trader_fee_state_acct(trg.public_key,self.ADDRESSES["MPG_ID"],self.ADDRESSES["FEES_ID"]),
            risk_engine_program=self.ADDRESSES["RISK_ID"],
            referral_key=PublicKey("11111111111111111111111111111111"),
            system_program=SYS_PROGRAM_ID,
            program_id=self.ADDRESSES["DEX_ID"]
        )
        # signers = list(trader_risk_state_acct )
        # signers.append(trg)
        # signers.append(self.wallet)
        blockhash = self.connection.get_recent_blockhash(commitment="finalized")
        transaction = Transaction(recent_blockhash=blockhash['result']['value']['blockhash'], 
                                  fee_payer=self.wallet.public_key).add(ix1)
        transaction.add(ix2)
        transaction.add(ix3)
        transaction.add_signer(trader_risk_state_acct)
        transaction.add_signer(trg)
        transaction.add_signer(self.wallet)
        try:
            #result = self.connection.simulate_transaction(transaction)
            result = self.connection.send_transaction(transaction, self.wallet, trg, trader_risk_state_acct, opts=types.TxOpts(skip_preflight=True))
            print("Transaction response: ", result)
        except:
            print("Error in sending transaction!")
            return None
            
    def get_open_orders(self, product: Product):
        l3ob = product.get_orderbook_L3()
        return utils.filterOpenOrders(l3ob, self.trgKey)
    
    def init(self):
        trgAddress = utils.getTraderRiskGroup(self.wallet.public_key, self.connection, self.ADDRESSES["DEX_ID"], self.ADDRESSES["MPG_ID"])
        if trgAddress == None:
            raise KeyError("No Trader Risk Group account for this wallet. Please create a new one first.")
        self.trgKey = PublicKey(trgAddress)
        response = self.connection.get_account_info(self.trgKey)
        try:
            r = response['result']['value']['data'][0]
            decoded = base64.b64decode(r)[8:]
            trg = TraderRiskGroup.from_bytes(decoded)
            self.traderRiskGroup = trg
            self.trgBytes = decoded
            
            self.userTokenAccount = utils.getUserAta(self.wallet.public_key, self.ADDRESSES['VAULT_MINT'])
            self.marketProductGroupVault = utils.getMpgVault(self.ADDRESSES['VAULT_SEED'], self.ADDRESSES['MPG_ID'], self.ADDRESSES['DEX_ID'])
        except:
            raise KeyError("No Trader Risk Group account for this wallet. Please create a new one first.") 
        
    def deposit_funds_ix(self, amount: Fractional):
        param = DepositFundsParams(amount)
        ix1 = deposit_funds(self.wallet.public_key, 
                self.userTokenAccount,
                self.trgKey,
                self.ADDRESSES["MPG_ID"],
                self.marketProductGroupVault,
                param,
                self.ADDRESSES["DEX_ID"]
                )
        blockhash = self.connection.get_recent_blockhash(commitment="finalized")
        transaction = Transaction(recent_blockhash=blockhash['result']['value']['blockhash'], 
                                  fee_payer=self.wallet.public_key).add(ix1)
        transaction.add_signer(self.wallet)
        #try:
        #result = self.connection.simulate_transaction(transaction)
        result = self.connection.send_transaction(transaction, self.wallet, opts=types.TxOpts(skip_preflight=True))
        print("Transaction response: ", result)
        #except:
        #    print("Error in sending transaction!")
        #    return None
        
    def withdraw_funds_ix(self, amount: Fractional):
        param = WithdrawFundsParams(amount)
        ix1 = withdraw_funds(self.wallet.public_key, 
                self.ADDRESSES["BUDDY_LINK_PROGRAM"],
                self.userTokenAccount,
                self.trgKey,
                self.ADDRESSES["MPG_ID"],
                self.marketProductGroupVault,
                self.ADDRESSES["RISK_ID"],
                PublicKey(Solana_pubkey.to_bytes(self.marketProductGroup.risk_model_configuration_acct)),
                PublicKey(Solana_pubkey.to_bytes(self.marketProductGroup.risk_output_register)),
                PublicKey(Solana_pubkey.to_bytes(self.traderRiskGroup.risk_state_account)),
                utils.getRiskSigner(self.ADDRESSES["MPG_ID"], self.ADDRESSES["DEX_ID"]),
                param,
                self.ADDRESSES["DEX_ID"],
                [SYS_PROGRAM_ID, SYS_PROGRAM_ID, SYS_PROGRAM_ID, SYS_PROGRAM_ID, SYS_PROGRAM_ID,
                 self.ADDRESSES["BUDDY_LINK_PROGRAM"], self.ADDRESSES["BUDDY_LINK_PROGRAM"], self.ADDRESSES["BUDDY_LINK_PROGRAM"] ]
                )
        blockhash = self.connection.get_recent_blockhash(commitment="finalized")
        transaction = Transaction(recent_blockhash=blockhash['result']['value']['blockhash'], 
                                  fee_payer=self.wallet.public_key).add(ix1)
        transaction.add_signer(self.wallet)
        #try:
        #result = self.connection.simulate_transaction(transaction)
        result = self.connection.send_transaction(transaction, self.wallet, opts=types.TxOpts(skip_preflight=True))
        print("Transaction response: ", result)
        #except:
        #    print("Error in sending transaction!")
        #    return None

    def new_order_ix(self, product: Product, size: Fractional,
         price: Fractional, side: str, order_type: str):
        if side == 'bid':
            sideParam = base.Side.BID
        elif side == 'ask':
            sideParam = base.Side.ASK
        else:
            raise KeyError("Side can only be bid or ask")
        
        self_trade_behaviour = base.SelfTradeBehavior.DECREMENT_TAKE
        match_limit = 1000
        if order_type == "limit":
          order_type_param = OrderType.LIMIT
        elif order_type == "market":
          order_type_param = OrderType.MARKET
        elif order_type == "fill_or_kill":
          order_type_param = OrderType.FILL_OR_KILL
        elif order_type == "immediate_or_cancel":
          order_type_param = OrderType.IMMEDIATE_OR_CANCEL
        elif order_type == "post_only":
          order_type_param = OrderType.POST_ONLY
        else:
            raise KeyError("Order type can onle be limit, market, fill_or_kill, immediate_or_cancel or post_only")
        
        newParams = NewOrderParams(sideParam,
                                   size,
                                   order_type_param,
                                   self_trade_behaviour,
                                   match_limit,
                                   price
                      )
        ix1 = new_order(
            self.wallet.public_key,
            self.trgKey,
            self.ADDRESSES["MPG_ID"],
            product.PRODUCT_ID,
            self.ADDRESSES["ORDERBOOK_P_ID"],
            product.ORDERBOOK_ID,
            utils.get_market_signer(product.PRODUCT_ID, self.ADDRESSES["DEX_ID"]),
            product.EVENT_QUEUE,
            product.BIDS,
            product.ASKS,
            self.ADDRESSES["FEES_ID"],
            PublicKey(Solana_pubkey.to_bytes(self.marketProductGroup.fee_model_configuration_acct)),
            PublicKey(Solana_pubkey.to_bytes(self.traderRiskGroup.fee_state_account)),
            PublicKey(Solana_pubkey.to_bytes(self.marketProductGroup.fee_output_register)),
            self.ADDRESSES["RISK_ID"],
            PublicKey(Solana_pubkey.to_bytes(self.marketProductGroup.risk_model_configuration_acct)),
            PublicKey(Solana_pubkey.to_bytes(self.marketProductGroup.risk_output_register)),
            PublicKey(Solana_pubkey.to_bytes(self.traderRiskGroup.risk_state_account)),
            utils.getRiskSigner(self.ADDRESSES["MPG_ID"], self.ADDRESSES["DEX_ID"]),
            newParams,
            self.ADDRESSES["DEX_ID"],
            SYS_PROGRAM_ID)

        blockhash = self.connection.get_recent_blockhash(commitment="finalized")
        transaction = Transaction(recent_blockhash=blockhash['result']['value']['blockhash'], 
                                  fee_payer=self.wallet.public_key).add(ix1)
        transaction.add_signer(self.wallet)
        #try:
        #result = self.connection.simulate_transaction(transaction)
        result = self.connection.send_transaction(transaction, self.wallet, opts=types.TxOpts(skip_preflight=True))
        print("Transaction response: ", result)
        #except:
        #    print("Error in sending transaction!")
        #    return None

    def cancel_order_ix(self,product:Product, orderId):
        param = CancelOrderParams(orderId)
        ix1 = cancel_order(
            self.wallet.public_key,
            self.trgKey,
            self.ADDRESSES["MPG_ID"],
            product.PRODUCT_ID,
            self.ADDRESSES["ORDERBOOK_P_ID"],
            product.ORDERBOOK_ID,
            utils.get_market_signer(product.PRODUCT_ID, self.ADDRESSES["DEX_ID"]),
            product.EVENT_QUEUE,
            product.BIDS,
            product.ASKS,
            self.ADDRESSES["RISK_ID"],
            PublicKey(Solana_pubkey.to_bytes(self.marketProductGroup.risk_model_configuration_acct)),
            PublicKey(Solana_pubkey.to_bytes(self.marketProductGroup.risk_output_register)),
            PublicKey(Solana_pubkey.to_bytes(self.traderRiskGroup.risk_state_account)),
            utils.getRiskSigner(self.ADDRESSES["MPG_ID"], self.ADDRESSES["DEX_ID"]),
            param,
            self.ADDRESSES["DEX_ID"],
            SYS_PROGRAM_ID)
        blockhash = self.connection.get_recent_blockhash(commitment="finalized")
        transaction = Transaction(recent_blockhash=blockhash['result']['value']['blockhash'], 
                                  fee_payer=self.wallet.public_key).add(ix1)
        transaction.add_signer(self.wallet)
        #try:
        #result = self.connection.simulate_transaction(transaction)
        result = self.connection.send_transaction(transaction, self.wallet, opts=types.TxOpts(skip_preflight=True))
        print("Transaction response: ", result)
        #except:
        #    print("Error in sending transaction!")
        #    return None

    def refresh_data():
        print('refresh_data')