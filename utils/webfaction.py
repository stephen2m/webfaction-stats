"""
WebFaction XML-RPC API Library
https://docs.webfaction.com/xmlrpc-api/apiref.html
"""

import xmlrpclib
import os

from structlog import get_logger
from configobj import ConfigObj

logger = get_logger()

API_URL = "https://api.webfaction.com"
USER_CONFIG = os.path.expanduser("~/.wfcreds")


class WebFactionBase(object):
    def __init__(self, username, password, target_server):
        self.logger = logger.bind()
        self.session_id = None

        if not (username and password and target_server):
            try:
                username, password, target_server = WebFactionBase.get_config()
            except NotImplemented as e:
                self.logger.error(
                    "config_error",
                    error=str(e),
                    message="Set target_machine, username and password via \
                        __init__ or your config file at {config}".format(
                            config=USER_CONFIG
                        )
                )

        self.username = username
        self.password = password
        self.target_server = target_server
        self.api_version = 2
        self.login()

    @staticmethod
    def get_config():
        """
        Read configuration from the directory specified in USER_CONFIG
        """
        if not os.path.exists(USER_CONFIG):
            raise NotImplementedError(
                "Set your target server, username and password in {config} \
                using the format \n\tusername=<your-username>\n\tpassword=\
                <your-password>\n\ttarget_server=<your-server-name>".format(
                    config=USER_CONFIG
                )
            )

        config = ConfigObj(USER_CONFIG)
        username = config['username']
        password = config['password']
        target_server = config['server']

        return username, password, target_server

    def login(self):
        """Logs into WebFaction using supplied credentials

        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-login

        Returns:
            Session ID
            Struct containing user-info
        """
        self.server = xmlrpclib.Server(API_URL)
        self.session_id, account = self.server.login(
            self.username, self.password, self.target_server, self.api_version
        )
        self.logger.debug(
            message="session ID: {session_id}, account {account}".format(
                session_id=self.session_id, account=account
            )
        )

    def system(self, cmd):
        """Runs a command as the user and prints the result

        Args:
            cmd (str): command to be excecuted

        Returns:
            None on success, 1 otherwise
        """
        try:
            result = self.server.system(self.session_id, cmd)
            print result
        except xmlrpclib.Fault:
            self.logger.exception(
                "Error running system command {command}".format(
                    commad=cmd
                )
            )
            return 1

    def list_disk_usage(self):
        """Returns disk usage stats for the user's account
        http://docs.webfaction.com/xmlrpc-api/apiref.html#method-list_disk_usage

        Returns:
            on success, struct containing disk usage output
            1 otherwise
        """
        try:
            result = self.server.list_disk_usage(self.session_id)
            self.logger.debug(
                action="disk_usage",
                result=result
            )
            return result
        except xmlrpclib.Fault:
            self.logger.exception(
                message="could not list disk usage stats"
            )
            return 1

    def list_bandwidth_usage(self):
        """Returns bandwidth stats for the user's websites
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-list_bandwidth_usage

        Returns:
            On success, struct containing two members 'daily' and 'monthly'
            1 otherwise
        """
        try:
            result = self.server.list_bandwidth_usage(self.session_id)
            return result
        except xmlrpclib.Fault:
            self.logger.exception(
                message="could not list disk usage stats"
            )
            return 1


    def list_apps(self):
        """Retrieve apps in the account
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-list_apps

        Returns:
            An array of structs containing the account's apps
            Empty list otherwise
        """
        try:
            return self.server.list_apps(self.session_id)
        except xmlrpclib.Fault:
            self.logger.exception(
                message="Could not list existing apps"
            )
            return []

    def list_dbs(self):
        """Retrieve databases in the account
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-list_dbs

        Returns:
            An array of structs containing the account's DBs
            Empty list otherwise
        """
        try:
            return self.server.list_dbs(self.session_id)
        except xmlrpclib.Fault:
            self.logger.exception(
                message="Could not list existing databases"
            )
            return []

    def list_db_users(self):
        """Retrieve all database users
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-list_db_users

        Returns:
            An array of structs containing the account's DBs
            Empty list otherwise
        """
        try:
            return self.server.list_db_users(self.session_id)
        except xmlrpclib.Fault:
            self.log.exception("Error listing database users")
            return []
