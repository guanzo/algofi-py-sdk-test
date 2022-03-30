import json
import base64
from algosdk import encoding, logic
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from ..utils import read_local_state, get_global_state, SCALE_FACTOR, PARAMETER_SCALE_FACTOR, search_global_state
from ..contract_strings import algofi_manager_strings as manager_strings
from ..contract_strings import algofi_market_strings as market_strings
from .asset import Asset

class Market:

    def __init__(self, indexer_client: IndexerClient, historical_indexer_client: IndexerClient, market_app_id):
        """Constructor method for the market object.

        :param indexer_client: a :class:`IndexerClient` for interacting with the network
        :type indexer_client: :class:`IndexerClient`
        :param historical_indexer_client: a :class:`IndexerClient` for interacting with the network
        :type historical_indexer_client: :class:`IndexerClient`
        :param market_app_id: market app id
        :type market_app_id: int
        """

        self.indexer = indexer_client
        self.historical_indexer = historical_indexer_client

        self.market_app_id = market_app_id
        self.market_address = logic.get_application_address(self.market_app_id)

        # read market global state
        self.update_global_state()
    
    def update_global_state(self):
        """Method to fetch most recent market global state.
        """
        market_state = get_global_state(self.indexer, self.market_app_id)
        # market constants
        self.market_counter = market_state[market_strings.manager_market_counter_var]
        
        # market asset info
        self.underlying_asset_id = market_state.get(market_strings.asset_id, None)
        self.bank_asset_id = market_state.get(market_strings.bank_asset_id, None)
        
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
    
        self.asset = Asset(self.indexer,
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
    
    def get_market_counter(self):
        """Returns the market counter for this market
        
        :return: market counter
        :rtype: int
        """
        return self.market_counter
    
    def get_asset(self):
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

    def get_underlying_borrowed(self, block=None):
        """Returns underlying_borrowed for this market

        :return: underlying_borrowed
        :rtype: int
        """
        if block:
            try:
                data = self.historical_indexer.applications(application_id=self.market_app_id, round_num=block)
                data = data["application"]["params"]["global-state"]
                return search_global_state(data, market_strings.underlying_borrowed)
            except:
                raise Exception("Issue getting data")
            
        else:
            return self.underlying_borrowed

    def get_outstanding_borrow_shares(self):
        """Returns outstanding_borrow_shares for this market

        :return: outstanding_borrow_shares
        :rtype: int
        """
        return self.outstanding_borrow_shares

    def get_underlying_cash(self, block=None):
        """Returns underlying_cash for this market

        :return: underlying_cash
        :rtype: int
        """
        if block:
            try:
                data = self.historical_indexer.applications(application_id=self.market_app_id, round_num=block)
                data = data["application"]["params"]["global-state"]
                return search_global_state(data, market_strings.underlying_cash)
            except:
                raise Exception("Issue getting data")
            
        else:
            return self.underlying_cash

    def get_underlying_reserves(self, block=None):
        """Returns underlying_reserves for this market

        :return: underlying_reserves
        :rtype: int
        """
        if block:
            try:
                data = self.historical_indexer.applications(application_id=self.market_app_id, round_num=block)
                data = data["application"]["params"]["global-state"]
                return search_global_state(data, market_strings.underlying_reserves)
            except:
                raise Exception("Issue getting data")
            
        else:
            return self.underlying_reserves

    def get_total_borrow_interest_rate(self, block=None):
        """Returns total_borrow_interest_rate for this market

        :return: total_borrow_interest_rate
        :rtype: int
        """
        if block:
            try:
                data = self.historical_indexer.applications(application_id=self.market_app_id, round_num=block)
                data = data["application"]["params"]["global-state"]
                return search_global_state(data, market_strings.total_borrow_interest_rate)
            except:
                raise Exception("Issue getting data")
            
        else:
            return self.total_borrow_interest_rate
    
    def get_collateral_factor(self):
        """Returns collateral_factor for this market

        :return: collateral_factor
        :rtype: int
        """
        return self.collateral_factor

    def get_liquidation_incentive(self):
        """Returns liquidation_incentive for this market

        :return: liquidation_incentive
        :rtype: int
        """
        return self.liquidation_incentive

    # USER FUNCTIONS
    
    def get_storage_state(self, storage_address):
        """Returns the market local state for address.

        :param storage_address: storage_address to get info for
        :type storage_address: string
        :return: market local state for address
        :rtype: dict
        """
        result = {}
        user_state = read_local_state(self.indexer, storage_address, self.market_app_id)
        asset = self.get_asset()
        result["active_collateral_bank"] = user_state.get(market_strings.user_active_collateral, 0)
        result["active_collateral_underlying"] = int(result["active_collateral_bank"] * self.bank_to_underlying_exchange / SCALE_FACTOR)
        result["active_collateral_usd"] = asset.to_usd(result["active_collateral_underlying"])
        result["active_collateral_max_borrow_usd"] = result["active_collateral_usd"] * self.collateral_factor / PARAMETER_SCALE_FACTOR
        result["borrow_shares"] = user_state.get(market_strings.user_borrow_shares, 0)
        result["borrow_underlying"] = int(self.underlying_borrowed * result["borrow_shares"] / self.outstanding_borrow_shares) \
                                        if self.outstanding_borrow_shares > 0 else 0
        result["borrow_usd"] = asset.to_usd(result["borrow_underlying"])

        return result