"""
WebFaction XML-RPC API Library
https://docs.webfaction.com/xmlrpc-api/apiref.html
"""

import xmlrpclib
import os
import json

import passwordmeter
from six import string_types
from structlog import get_logger
from configobj import ConfigObj

logger = get_logger()

API_URL = "https://api.webfaction.com"
USER_CONFIG = os.path.expanduser("~/.wfcreds")


class WebFactionDBUser(object):
    def __init__(self, username, password, db_type):
        super(WebFactionDBUser, self).__init__()
        self.username = username
        self.password = password
        self.db_type = db_type


class WebFactionBase(object):
    def __init__(self, username, password, target_server):
        self.logger = logger.bind()
        self.session_id = None
        self.valid_db_types = ["mysql", "postgresql"]

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
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-system

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
                message="Error running system command {command}".format(
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
            self.logger.exception(
                message="could not list database users"
            )
            return []

    def list_mailboxes(self):
        """Retrieve mailboxes in the account
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-list_mailboxes

        Returns:
            An array of structs containing the account's mailboxes
            Empty list otherwise
        """
        try:
            return self.server.list_mailboxes(self.session_id)
        except xmlrpclib.Fault:
            self.logger.exception(
                message="Could not list existing mailboxes"
            )
            return []

    def create_mailbox(
        self, mailbox, enable_spam_protection=True, discard_spam=False,
        spam_redirect_folder="", use_manual_procmailrc=False,
        manual_procmailrc=""
    ):
        """Create a new mailbox in the account
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-create_mailbox

        Args:
            mailbox (str): mailbox name
            enable_spam_protection (boolean): enable spam protection (optional)
            discard_spam (boolean): discard spam messages (optional)
            spam_redirect_folder (str): IMAP folder to store spam (optional)
            use_manual_procmailrc (boolean): manual procmailrc rules (optional)
            manual_procmailrc (str): procmailrc rules for the inbox (optional)

        Returns:
            Returns a struct containing the new mailbox details
            Empty list otherwise
        """
        assert isinstance(
            mailbox, string_types), 'mailbox name should be a string'
        assert isinstance(
            spam_redirect_folder, string_types
        ), 'redirect folder should be a string'
        assert isinstance(
            manual_procmailrc, string_types
        ), 'procmailrc rules should be a string'

        if use_manual_procmailrc and not manual_procmailrc:
            raise ValueError("`manual_procmailrc` cannot be empty")

        try:
            result = self.server.create_mailbox(
                self.session_id, mailbox, enable_spam_protection, discard_spam,
                spam_redirect_folder, use_manual_procmailrc, manual_procmailrc
            )
            self.logger.debug(action="create_mailbox", result=result)
            print(
                "Password for the new mailbox: {password}".format(
                    password=result['password']
                )
            )
        except xmlrpclib.Fault:
            self.logger.exception(
                message="Could not create mailbox {name}".format(
                    name=mailbox
                )
            )

            return False

    def delete_mailbox(self, mailbox):
        """Deletes a specified mailbox
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-delete_mailbox

        Returns:
            on success, struct containing disk usage output
            False otherwise
        """
        assert isinstance(
            mailbox, string_types), 'mailbox name should be a string'
        try:
            result = self.server.delete_mailbox(
                self.session_id, mailbox
            )
            self.logger.debug(action="delete_mailbox", result=result)
            return result
        except xmlrpclib.Fault:
            self.logger.exception(
                action="delete_mailbox",
                message="could not delete mailbox {name}".format(
                    name=mailbox
                )
            )
            return False

    def create_db_user(
        self, username, password, db_type, enforce_password_strength=True
    ):
        """Create a new mailbox in the account
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-create_db_user

        Args:
            username (str): database user's name
            password (str): database user's password
            db_type (str): either `mysql` or `postgresql`
            enforce_password_strength (boolean): use passwordmeter to
                ensure strong passwords are used

        Returns:
            Returns an object of type WebFactionDBUser, otherwise False
        """
        assert isinstance(
            username, string_types), 'username should be a string'
        assert isinstance(
            password, string_types), 'password should be a string'
        assert isinstance(
            db_type, string_types), 'db_type should be a string'

        if enforce_password_strength:
            strength, improvements = passwordmeter.test(password)
            suggestions = [value for value in improvements.values()]

            if strength < 0.5:
                raise ValueError(
                    "Your password is weak. Suggested improvements: \
                    \n\t{improvements}".format(
                        improvements='\n\t'.join(suggestions)
                    )
                )

        if db_type not in self.valid_db_types:
            raise ValueError(
                "db type should be either: {valid_db_types}".format(
                    valid_db_types=', '.join(self.valid_db_types)
                )
            )

        try:
            result = self.server.create_db_user(
                self.session_id, username, password, db_type
            )
            self.logger.debug(action="create_db_user", result=result)

            return WebFactionDBUser(username, password, db_type)
        except xmlrpclib.Fault:
            self.logger.exception(
                message="Could not create DB user {name} for {type} DB".format(
                    name=username, type=db_type
                )
            )
            return False