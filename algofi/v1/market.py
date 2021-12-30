import json
import base64
from algosdk import encoding, logic
from algosdk.v2client.algod import AlgodClient
from ..utils import read_local_state, get_global_state, SCALE_FACTOR
from ..contract_strings import algofi_manager_strings as manager_strings
from ..contract_strings import algofi_market_strings as market_strings
from .asset import Asset

class Market:

    def __init__(self, algod_client: AlgodClient, market_info):
        """Constructor method for the market object.

        :param algod_client: a :class:`AlgodClient` for interacting with the network
        :type algod_client: :class:`AlgodClient`
        :param market_info: dictionary of market information
        :type market_info: dict
        """

        self.algod = algod_client

        self.market_app_id = market_info.get("marketAppId")
        self.market_address = logic.get_application_address(self.market_app_id)

        self.underlying_asset_id = market_info.get("underlyingAssetId", None)
        self.bank_asset_id = market_info.get("bankAssetId", None)

        # read market global state
        self.update_global_state()
    
    def update_global_state(self):
        """Method to fetch most recent market global state.
        """
        market_state = get_global_state(self.algod, self.market_app_id)
        # market parameters
        self.oracle_app_id = market_state.get(market_strings.oracle_app_id, None)
        self.oracle_price_field = market_state.get(market_strings.oracle_price_field, None)
        self.oracle_price_scale_factor = market_state.get(market_strings.oracle_price_scale_factor, None)
        self.collateral_factor = market_state.get(market_strings.collateral_factor, None)
        self.liquidation_incentive = market_state.get(market_strings.liquidation_incentive, None)
        self.reserve_factor = market_state.get(market_strings.reserve_factor, None)
        self.base_interest_rate = market_state.get(market_strings.base_interest_rate, None)
        self.slope_1 = market_state.get(market_strings.slope_1, None)
        self.slope_2 = market_state.get(market_strings.slope_2, None)
        self.utilization_optimal = market_state.get(market_strings.utilization_optimal, None)
        self.market_supply_cap_in_dollars = market_state.get(market_strings.market_supply_cap_in_dollars, None)
        self.market_borrow_cap_in_dollars = market_state.get(market_strings.market_borrow_cap_in_dollars, None)
        
        # balance info
        self.active_collateral = market_state.get(market_strings.active_collateral, 0)
        self.bank_circulation = market_state.get(market_strings.bank_circulation, 0)
        self.bank_to_underlying_exchange = market_state.get(market_strings.bank_to_underlying_exchange, 0)
        self.underlying_borrowed = market_state.get(market_strings.underlying_borrowed, 0)
        self.outstanding_borrow_shares = market_state.get(market_strings.outstanding_borrow_shares, 0)
        self.underlying_cash = market_state.get(market_strings.underlying_cash, 0)
        self.underlying_reserves = market_state.get(market_strings.underlying_reserves, 0)
        self.total_borrow_interest_rate = market_state.get(market_strings.total_borrow_interest_rate, 0)
    
        self.asset = Asset(self.algod,
                           self.underlying_asset_id,
                           self.bank_asset_id,
                           self.oracle_app_id,
                           self.oracle_price_field,
                           self.oracle_price_scale_factor) if self.underlying_asset_id else None
    # GETTERS
    
    def get_market_app_id(self):
        """Returns the app id for this market

        :return: market app id
        :rtype: int
        """
        return self.market_app_id
    
    def get_market_address(self):
        """Returns the address for this market
        
        :return: market address
        :rtype: string
        """
        return self.market_address
    
    def get_asset_info(self):
        """Returns asset object for this market

        :return: asset
        :rtype: :class:`Asset`
        """
        return self.asset
    
    def get_active_collateral(self):
        """Returns active_collateral for this market

        :return: active_collateral
        :rtype: int
        """
        return self.active_collateral

    def get_bank_circulation(self):
        """Returns bank_circulation for this market

        :return: bank_circulation
        :rtype: int
        """
        return self.bank_circulation

    def get_bank_to_underlying_exchange(self):
        """Returns bank_to_underlying_exchange for this market

        :return: bank_to_underlying_exchange
        :rtype: int
        """
        return self.bank_to_underlying_exchange

    def get_underlying_borrowed(self):
        """Returns underlying_borrowed for this market

        :return: underlying_borrowed
        :rtype: int
        """
        return self.underlying_borrowed

    def get_outstanding_borrow_shares(self):
        """Returns outstanding_borrow_shares for this market

        :return: outstanding_borrow_shares
        :rtype: int
        """
        return self.outstanding_borrow_shares

    def get_underlying_cash(self):
        """Returns underlying_cash for this market

        :return: underlying_cash
        :rtype: int
        """
        return self.underlying_cash

    def get_underlying_reserves(self):
        """Returns underlying_reserves for this market

        :return: underlying_reserves
        :rtype: int
        """
        return self.underlying_reserves

    def get_total_borrow_interest_rate(self):
        """Returns total_borrow_interest_rate for this market

        :return: total_borrow_interest_rate
        :rtype: int
        """
        return self.total_borrow_interest_rate
    
    # USER FUNCTIONS
    
    def get_storage_state(self, storage_address):
        """Returns the market local state for address.

        :param storage_address: storage_address to get info for
        :type storage_address: string
        :return: market local state for address
        :rtype: dict
        """
        result = {}
        user_state = read_local_state(self.algod, storage_address, self.market_app_id)
        result["active_collateral_bank"] = user_state.get(market_strings.user_active_collateral, 0)
        result["active_collateral_underlying"] = int(result["active_collateral_bank"] * self.bank_to_underlying_exchange / SCALE_FACTOR)
        result["borrow_shares"] = user_state.get(market_strings.user_borrow_shares, 0)
        result["borrow_underlying"] = int(self.underlying_borrowed * result["borrow_shares"] / self.outstanding_borrow_shares)
        
        return result