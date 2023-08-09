from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.types import MemcmpOpts
from solana.transaction import Transaction
from gfx_perps_sdk.constant_instructions.instructions import initialize_trader_acct_ix
def get_market_signer(product: PublicKey, DEX_ID: PublicKey) -> PublicKey:
    addr = PublicKey.find_program_address([product._key], DEX_ID)
    return addr[0]

def processOrderbook(bidsParam, asksParams, tickSize, decimals):
    result = {}
    result["bids"] = []
    for bids in bidsParam:
        result["bids"].append(
            {
                'size': bids['size'] / (10 ** (decimals + 5)),
                'price': (bids['price'] >> 32) / tickSize
            }
        )
    result["asks"] = []
    for asks in asksParams:
        result["asks"].append(
            {
                'size': asks['size'] / (10 ** (decimals + 5)),
                'price': (asks['price'] >> 32) / tickSize
            }
        )
    return result

def processL3Ob(bidsParam, asksParams, tickSize, decimals):
    result = {}
    result["bids"] = []
    for bids in bidsParam:
        result["bids"].append(
            {
                'size': bids['size'] / (10 ** (decimals + 5)),
                'price': (bids['price'] >> 32) / tickSize,
                "user": bids['user'],
                "orderId": bids['orderId']
            }
        )
    result["asks"] = []
    for asks in asksParams:
        result["asks"].append(
            {
                'size': asks['size'] / (10 ** (decimals + 5)),
                'price': (asks['price'] >> 32) / tickSize,
                "user": asks['user'],
                "orderId": asks['orderId']               
            }
        )
    return result  

def getTraderRiskGroup(wallet: PublicKey, connection: Client,DEX_ID: PublicKey, MPG_ID: PublicKey):
    try:  
        print("wallet: ", wallet)
        m1 = [MemcmpOpts(48, wallet.to_base58().decode("utf-8"))]
        m1.append(MemcmpOpts(16, MPG_ID.to_base58().decode("utf-8")))
        res = connection.get_program_accounts(DEX_ID,"confirmed", "jsonParsed",memcmp_opts=m1
        )
        result = res['result']
        if len(result) == 0:
            return None
        return result[0]['pubkey']
    except:
        print("error in getting trg")
        return None
    
def getUserAta(wallet: PublicKey, vault_mint: PublicKey):
    return PublicKey.find_program_address([wallet._key, bytes("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",encoding="utf-8"), vault_mint._key]
                                          ,PublicKey("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"))

def getMpgVault(  
        VAULT_SEED: str,
        MPG_ID: PublicKey,
        DEX_ID: PublicKey):
    return PublicKey.find_program_address([bytes(VAULT_SEED,encoding="utf-8"), MPG_ID._key]
            , DEX_ID)

def get_fee_model_configuration_addr(
        market_product_group_key: PublicKey,
        program_id: PublicKey,
) -> PublicKey:
    key, _ = PublicKey.find_program_address(
        seeds=[
            b"fee_model_config_acct",
            bytes(market_product_group_key),
        ],
        program_id=program_id,
    )
    return key

def get_trader_fee_state_acct(
        trader_risk_group: PublicKey,
        market_product_group: PublicKey,
        program_id: PublicKey,
) -> PublicKey:
    key, _ = PublicKey.find_program_address(
        seeds=[
            b"trader_fee_acct",
            bytes(trader_risk_group),
            bytes(market_product_group),
        ],
        program_id=program_id,
    )
    return key

SYSTEM_PROGRAM = PublicKey("11111111111111111111111111111111")

def initialize_trader_fee_acct(
    payer: PublicKey,
    market_product_group: PublicKey,
    program_id: PublicKey,
    trader_risk_group: PublicKey,
    system_program: PublicKey,
    fee_model_config_acct: PublicKey,
):

    if fee_model_config_acct is None:
        fee_model_config_acct = get_fee_model_configuration_addr(
            market_product_group,
            program_id,
        )

    trader_fee_acct = get_trader_fee_state_acct(
        trader_risk_group,
        market_product_group,
        program_id,
    )

    #return Transaction(fee_payer=payer).add(

    return initialize_trader_acct_ix(
            payer=payer,
            fee_model_config_acct=fee_model_config_acct,
            trader_fee_acct=trader_fee_acct,
            market_product_group=market_product_group,
            trader_risk_group=trader_risk_group,
            system_program=system_program,
            program_id=program_id,
        )

def getRiskSigner(MPG_ID: PublicKey, DEX_ID: PublicKey):
    res = PublicKey.find_program_address([MPG_ID._key], DEX_ID)
    return res[0]

def get_trader_fee_state_acct(
        trader_risk_group: PublicKey,
        market_product_group: PublicKey,
        program_id: PublicKey,
) -> PublicKey:
    key, _ = PublicKey.find_program_address(
        seeds=[
            b"trader_fee_acct",
            bytes(trader_risk_group),
            bytes(market_product_group),
        ],
        program_id=program_id,
    )
    return key
