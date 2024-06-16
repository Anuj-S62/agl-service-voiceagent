import json
import threading
from kuksa_client import KuksaClientThread
import sys
from pathlib import Path
import asyncio
import concurrent.futures
from kuksa_client.grpc.aio import VSSClient
from kuksa_client.grpc import Datapoint
import time
from agl_service_voiceagent.utils.config import get_config_value, get_logger


class VSSInterface:
    """
    VSS Interface

    This class provides methods to initialize, authorize, connect, send values,
    check the status, and close the Kuksa client.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        Get the unique instance of the class.

        Returns:
            KuksaInterface: The instance of the class.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(VSSInterface, cls).__new__(cls)
                cls._instance.init_client()
        return cls._instance

    def init_client(self):
        """
        Initialize the Kuksa client.
        """
        # Defaults
        self.hostname = str(get_config_value("hostname", "VSS"))
        self.port = str(get_config_value("port", "VSS"))
        self.token_filename = str(get_config_value("token_filename", "VSS"))
        self.tls_server_name = str(get_config_value("tls_server_name", "VSS"))
        self.verbose = False
        self.insecure = bool(int(get_config_value("insecure", "VSS")))
        self.protocol = str(get_config_value("protocol", "VSS"))
        self.ca_cert_filename = str(get_config_value("ca_cert_filename", "VSS"))
        self.token = None
        self.is_connected = False
        self.logger = get_logger()

        self.set_token()

        # validate config
        if not self.validate_config():
            exit(1)

        # define class methods
        self.vss_client = None

    def validate_config(self):
        """
        Validate the Kuksa client configuration.

        Returns:
            bool: True if the configuration is valid, False otherwise.
        """
        if self.hostname is None:
            print("[-] Error: Kuksa IP address is not set.")
            self.logger.error("Kuksa IP address is not set.")
            return False

        if self.port is None:
            print("[-] Error: Kuksa port is not set.")
            self.logger.error("Kuksa port is not set.")
            return False

        if self.token is None:
            print("[-] Warning: Kuksa auth token is not set.")
            self.logger.warning("Kuksa auth token is not set.")

        if self.protocol != "ws" and self.protocol != "grpc":
            print("[-] Error: Invalid Kuksa protocol. Only 'ws' and 'grpc' are supported.")
            self.logger.error("Invalid Kuksa protocol. Only 'ws' and 'grpc' are supported.")
            return False

        return True
    
    def set_token(self):
        """
        Set the Kuksa auth token.
        """
        if self.token_filename != "":
            token_file = open(self.token_filename, "r")
            self.token = token_file.read()
        else:
            self.token = ""

    def get_vss_client(self):
        """
        Get the VSS client instance.

        Returns:
            VSSClientThread: The VSS client instance.
        """
        if self.vss_client is None:
            return None
        return self.vss_client
    
    async def authorize_vss_client(self):
        """
        Authorize the VSS client.
        """
        if self.vss_client is None:
            print("[-] Error: Failed to authorize Kuksa client. Kuksa client is not initialized.")
            self.logger.error("Failed to authorize Kuksa client. Kuksa client is not initialized.")
            return False
        try:
            await self.vss_client.authorize(self.token)
            print(f"Authorized Kuksa client with token {self.token}")
            return True
        except Exception as e:
            print(f"[-] Error: Failed to authorize Kuksa client: {e}")
            self.logger.error(f"Failed to authorize Kuksa client: {e}")
            return False
        
    async def get_server_info(self):
        """
        Get the server information.

        Returns:
            dict: The server information.
        """
        if self.vss_client is None:
            return None
        try:
            return await self.vss_client.get_server_info()
        except Exception as e:
            print(f"[-] Error: Failed to get server info: {e}")
            self.logger.error(f"Failed to get server info: {e}")
            return None
    
    async def connect_vss_client(self):
        """
        Connect the VSS client.
        """
        print(f"Connecting to KUKSA.val databroker at {self.hostname}:{self.port}")
        try:
            self.vss_client = VSSClient(
                                self.hostname,
                                self.port,
                                root_certificates=Path(self.ca_cert_filename),
                                token=self.token,
                                tls_server_name=self.tls_server_name,
                                ensure_startup_connection=True)
            await self.vss_client.connect()
            print(f"[+] Connected to KUKSA.val databroker at {self.hostname}:{self.port}")
            self.is_connected = True
            return True
        except Exception as e:
            print(f"[-] Error: Failed to connect to Kuksa val databroker: {e}")
            self.logger.error(f"Failed to connect to Kuksa val databroker: {e}")
            self.is_connected = False
            return False


    async def set_current_values(self, path=None, value=None):
        """
        Set the current values.

        Args:
            updates (dict): The updates to set.
        """
        result = False
        if self.vss_client is None:
            print(f"[-] Error: Failed to send value '{value}' to Kuksa. Kuksa client is not initialized.")
            self.logger.error(f"Failed to send value '{value}' to Kuksa. Kuksa client is not initialized.")
            return result
        try:
            await self.vss_client.set_current_values({path: Datapoint(value)})
            result = True
        except Exception as e:
            print(f"[-] Error: Failed to send value '{value}' to Kuksa: {e}")
            self.logger.error(f"Failed to send value '{value}' to Kuksa: {e}")
        return result
    

    async def get_current_values(self, path=None):
        """
        Get the current values.

        Args:
            paths (list): The paths to get.

        Returns:
            dict: The current values.

        current_values = await client.get_current_values([
                'Vehicle.Speed',
                'Vehicle.ADAS.ABS.IsActive',
            ])
            speed_value = current_values['Vehicle.Speed'].value
        """

        if self.vss_client is None or self.is_connected is False:
            return None
        try:
            result = await self.vss_client.get_current_values([path])
            return result[path].value
        except Exception as e:
            print(f"[-] Error: Failed to get current values: {e}")
            self.logger.error(f"Failed to get current values: {e}")
            return None

    async def disconnect_vss_client(self):
        """
        Disconnect the VSS client.
        """
        if self.vss_client is None:
            print("[-] Error: Failed to disconnect Kuksa client. Kuksa client is not initialized.")
            self.logger.error("Failed to disconnect Kuksa client. Kuksa client is not initialized.")
            return False
        try:
            await self.vss_client.disconnect()
            print("Disconnected from Kuksa val databroker.")
            self.is_connected = False
            return True
        except Exception as e:
            print(f"[-] Error: Failed to disconnect from Kuksa val databroker: {e}")
            self.logger.error(f"Failed to disconnect from Kuksa val databroker: {e}")
            return False
    
    
