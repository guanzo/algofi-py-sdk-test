import json
import base64
from algosdk import encoding, logic
from algosdk.v2client.algod import AlgodClient
from ..utils import read_local_state, get_global_state, SCALE_FACTOR
from ..contract_strings import algofi_manager_strings as manager_strings
from ..contract_strings import algofi_market_strings as market_strings
from .rewards_program import RewardsProgram

class Manager:
    def __init__(self, algod_client: AlgodClient, manager_app_id):
        """Constructor method for manager object.

        :param algod_client: a :class:`AlgodClient` for interacting with the network
        :type algod_client: :class:`AlgodClient`
        :param manager_app_id: manager app id
        :type manager_app_id: int
        """

        self.algod = algod_client

        self.manager_app_id = manager_app_id
        self.manager_address = logic.get_application_address(self.manager_app_id)
        
        # read market global state
        self.update_global_state()
    
    def update_global_state(self):
        """Method to fetch most recent manager global state.
        """
        manager_state = get_global_state(self.algod, self.manager_app_id)
        self.rewards_program = RewardsProgram(self.algod, manager_state)
    
    # GETTERS
    
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

    def get_rewards_program(self):
        """Return a list of current rewards program
        
        :return: rewards program
        :rtype: :class:`RewardsProgram
        """
        return self.rewards_program

    # USER FUNCTIONS
    
    def get_storage_address(self, address):
        """Returns the storage address for the client user

        :param address: address to get info for
        :type address: string
        :return: storage account address for user
        :rtype: string
        """
        user_manager_state = read_local_state(self.algod, address, self.manager_app_id)
        raw_storage_address = user_manager_state.get(manager_strings.user_storage_address, None)
        if not raw_storage_address:
            raise Exception("No storage address found")
        return encoding.encode_address(base64.b64decode(raw_storage_address.strip()))
    
    def get_user_state(self, address):
        """Returns the market local state for address.

        :param address: address to get info for
        :type address: string
        :return: market local state for address
        :rtype: dict
        """
        storage_address = self.get_storage_address(address)
        return self.get_storage_state(storage_address)
    
    def get_storage_state(self, storage_address):
        """Returns the market local state for storage address.

        :param storage_address: storage_address to get info for
        :type storage_address: string
        :return: market local state for address
        :rtype: dict
        """
        result = {}
        user_state = read_local_state(self.algod, storage_address, self.manager_app_id)
        result["user_global_max_borrow_in_dollars"] = user_state.get(manager_strings.user_global_max_borrow_in_dollars, 0) 
        result["user_global_borrowed_in_dollars"] = user_state.get(manager_strings.user_global_borrowed_in_dollars, 0)
        return result
    
    def get_user_unrealized_rewards(self, address, markets):
        """Returns projected unrealzed rewards for a user address
        
        :return: tuple of primary and secondary unrealized rewards
        :rtype: (int, int)
        """
        storage_address = self.get_storage_address(address)
        return self.get_storage_unrealized_rewards(storage_address, markets)

    def get_storage_unrealized_rewards(self, storage_address, markets):
        """Returns preojected unrealized rewards for a storage address
        
        :return: tuple of primary and secondary unrealized rewards
        :rtype: (int, int)
        """
        return self.get_rewards_program().get_storage_unrealized_rewards(storage_address, self, markets)