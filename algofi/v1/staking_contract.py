import json
import base64
from algosdk import encoding, logic
from algosdk.v2client.algod import AlgodClient
from ..utils import read_local_state, get_global_state, SCALE_FACTOR
from ..contract_strings import algofi_manager_strings as manager_strings
from ..contract_strings import algofi_market_strings as market_strings
from .asset import Asset

COEFFICIENT_KEY = int(1).to_bytes(8, byteorder='big').decode('utf-8')+manager_strings.counter_indexed_rewards_coefficient
USER_COEFFICIENT_KEY = int(1).to_bytes(8, byteorder='big').decode('utf-8')+manager_strings.counter_to_user_rewards_coefficient_initial

class StakingContract:
    def __init__(self, algod_client: AlgodClient, staking_contract_info):
        """Constructor method for the generic client.

        :param algod_client: a :class:`AlgodClient` for interacting with the network
        :type algod_client: :class:`AlgodClient`
        :param staking_contract_info: dictionary of staking contract information
        :type staking_contract_info: dict
        """

        self.algod = algod_client
        
        self.manager_app_id = staking_contract_info.get("managerAppId")
        self.manager_address = logic.get_application_address(self.manager_app_id)
        self.market_app_id = staking_contract_info.get("marketAppId")
        self.market_address = logic.get_application_address(self.market_app_id)

        self.underlying_asset_id = staking_contract_info.get("underlyingAssetId", None)
        self.bank_asset_id = staking_contract_info.get("bankAssetId", None)
        
        # read market global state
        self.update_global_state()
    
    def update_global_state(self):
        """Method to fetch most recent staking contract global state
        """
        
        manager_state = get_global_state(self.algod, self.manager_app_id)
        self.rewards_program_number = manager_state.get(manager_strings.n_rewards_programs, 0)
        self.rewards_amount = manager_state.get(manager_strings.rewards_amount, 0)
        self.rewards_per_second = manager_state.get(manager_strings.rewards_per_second, 0)
        self.rewards_asset_id = manager_state.get(manager_strings.rewards_asset_id, 0)
        self.rewards_secondary_ratio = manager_state.get(manager_strings.rewards_secondary_ratio, 0)
        self.rewards_secondary_asset_id = manager_state.get(manager_strings.rewards_secondary_asset_id, 0)
        self.rewards_coefficient = manager_state.get(COEFFICIENT_KEY, 0)
        
        market_state = get_global_state(self.algod, self.market_app_id)
        # market parameters
        self.oracle_app_id = market_state.get(market_strings.oracle_app_id, None)
        self.oracle_price_field = market_state.get(market_strings.oracle_price_field, None)
        self.oracle_price_scale_factor = market_state.get(market_strings.oracle_price_scale_factor, None)
        self.market_staking_cap = market_state.get(market_strings.market_supply_cap_in_dollars, None)
        self.staked = market_state.get(market_strings.active_collateral, 0)
        self.bank_to_underlying_exchange = market_state.get(market_strings.bank_to_underlying_exchange, 0)

        self.asset = Asset(self.algod, self.underlying_asset_id, self.bank_asset_id)

    # GETTERS

    def get_asset_info(self):
        """Returns asset object for this market

        :return: asset
        :rtype: :class:`Asset`
        """
        return self.asset
    
    def get_manager_app_id(self):
        """Return manager app id
        
        :return: manager app id
        :rtype: int
        """
        return self.manager_app_id
    
    def get_manager_address(self):
        """Return manager address
        
        :return: manager address
        :rtype: string
        """
        return self.manager_address
    
    def get_market_app_id(self):
        """Returns the market app id

        :return: market app id
        :rtype: int
        """
        return self.market_app_id
    
    def get_market_address(self):
        """Returns the market address
        
        :return: market address
        :rtype: string
        """
        return self.market_address

    def get_oracle_app_id(self):
        """Returns the oracle app id
        
        :return: oracle app id
        :rtype: int
        """
        return self.oracle_app_id

    def get_staked(self):
        """Return staked amount
        
        :return: staked
        :rtype: int
        """
        return self.staked

    def get_rewards_asset_ids(self):
        """Return a list of current rewards assets
        
        :return: rewards asset list
        :rtype: list
        """
        result = []
        if self.rewards_asset_id > 1:
            result.append(self.rewards_asset_id)
        if self.rewards_secondary_asset_id > 1:
            result.append(self.rewards_secondary_asset_id)
        return result

    # USER FUNCTIONS

    def get_storage_address(self, address):
        """Returns the staking contract storage address for the given address or None if it does not exist.

        :param address: address to get info for
        :type address: string
        :return: storage account address for user
        :rtype: string
        """
        
        user_manager_state = read_local_state(self.algod, address, self.manager_app_id)
        raw_storage_address = user_manager_state.get(manager_strings.user_storage_address, None)
        if not raw_storage_address:
            return None
        return encoding.encode_address(base64.b64decode(raw_storage_address.strip()))

    
    def get_user_state(self, address):
        """Returns the staking contract local state for address.

        :param address: address to get info for
        :type address: string
        :return: staking contract local state for address
        :rtype: dict
        """
        
        storage_address = self.get_storage_address(address)
        if not storage_address:
            raise Exception("no storage address found")
        
        result = {}
        user_manager_state = read_local_state(self.algod, storage_address, self.manager_app_id)
        user_rewards_program_number = user_manager_state.get(manager_strings.user_rewards_program_number, -1)
        IS_CURRENT_REWARDS_PROGRAM = user_rewards_program_number == self.rewards_program_number
        result["pending_rewards"] = user_manager_state.get(manager_strings.user_pending_rewards, 0) if IS_CURRENT_REWARDS_PROGRAM else 0
        result["pending_secondary_rewards"] = user_manager_state.get(manager_strings.user_secondary_pending_rewards, 0) if IS_CURRENT_REWARDS_PROGRAM else 0
        result["rewards_coefficient"] = user_manager_state.get(USER_COEFFICIENT_KEY, 0) if IS_CURRENT_REWARDS_PROGRAM else 0
        
        user_market_state = read_local_state(self.algod, storage_address, self.market_app_id)
        result["staked_bank"] = user_market_state.get(market_strings.user_active_collateral, 0)
        result["staked"] = int(result["staked_bank"] * self.bank_to_underlying_exchange / SCALE_FACTOR)
        
        return result