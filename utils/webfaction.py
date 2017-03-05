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
    def __init__(self, username="", password="", target_server=""):
        self.logger = logger.bind()
        self.session_id = None
        self.valid_db_types = ["mysql", "postgresql"]
        self.valid_addons = ["tsearch", "postgis"]
        self.valid_shells = ['none', 'bash', 'sh', 'ksh', 'csh', 'tcsh']

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
        self.server = xmlrpclib.ServerProxy(API_URL)
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
            None on success, False otherwise
        """
        try:
            result = self.server.system(self.session_id, cmd)
            print(result)
        except xmlrpclib.Fault:
            self.logger.exception(
                message="Error running system command {command}".format(
                    commad=cmd
                )
            )
            return False

    def account_stats(self, action):
        """
        http://docs.webfaction.com/xmlrpc-api/apiref.html#method-list_disk_usage
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-list_bandwidth_usage
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-list_apps
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-list_dbs
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-list_db_users
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-list_mailboxes
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-list_users
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-list_ips
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-list_machines

        Args:
            action (str): determines API to run. Possible options:
                disk: Returns disk usage stats for the user's account
                bandwidth: bandwidth stats for the account
                apps: retrieve all apps on the account
                dbs: retrieve all DBs on the account
                db_users: retrieve all DB users on the account
                mailboxes: retrieve mailboxes on the account
                users: list all shell users for the account
                ips: list all of the account's machines and their IP address
                machines: list account's machines

        Returns:
            on success, struct containing disk usage output
            False otherwise
        """
        operations = {
            'disk': self.server.list_disk_usage,
            'bandwidth': self.server.list_bandwidth_usage,
            'apps': self.server.list_apps,
            'dbs': self.server.list_dbs,
            'db_users': self.server.list_db_users,
            'mailboxes': self.server.list_mailboxes,
            'users': self.server.list_users,
            'ips': self.server.list_ips,
            'machines': self.server.list_machines
        }

        if action not in operations.keys():
            raise Exception(
                "Method {method_name} not implemented".format(
                    method_name=action
                )
            )

        try:
            result = operations[action](self.session_id)
            self.logger.debug(action=action, result=result)
            return result
        except xmlrpclib.Fault:
            self.logger.exception(
                action=action,
                message="operation failed"
            )
            return False

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
        """Create a new DB user in the account
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
                message="Could not create DB user {name} ({type} DB)".format(
                    name=username, type=db_type
                )
            )
            return False

    def change_db_user_password(
        self, username, password, db_type, enforce_password_strength=True
    ):
        """Change a DB user's password
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-change_db_user_password

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
            result = self.server.change_db_user_password(
                self.session_id, username, password, db_type
            )
            self.logger.debug(action="change_db_user_password", result=result)

            return WebFactionDBUser(username, password, db_type)
        except xmlrpclib.Fault:
            self.logger.exception(
                message="Could not change password for DB user {name} ({type} \
                    DB)".format(name=username, type=db_type)
            )
            return False

    def delete_db_user(self, username, db_type):
        """Deletes a specified DB user
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-delete_db_user

        Args:
            username (str): database user's name
            db_type (str): either `mysql` or `postgresql`

        Returns:
            on success, struct containing the output
            False otherwise
        """
        assert isinstance(
            username, string_types), 'username should be a string'
        assert isinstance(
            db_type, string_types), 'db_type should be a string'

        if db_type not in self.valid_db_types:
            raise ValueError(
                "db type should be either: {valid_db_types}".format(
                    valid_db_types=', '.join(self.valid_db_types)
                )
            )

        try:
            result = self.server.delete_db_user(
                self.session_id, username, db_type
            )
            self.logger.debug(action="delete_dbuser", result=result)
            return result
        except xmlrpclib.Fault:
            self.logger.exception(
                action="delete_dbuser",
                message="could not delete DB user {name}".format(
                    name=username
                )
            )
            return False

    def delete_db(self, dbname, db_type):
        """Deletes a specified DB
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-delete_db

        Args:
            dbname (str): database's name
            db_type (str): either `mysql` or `postgresql`

        Returns:
            on success, struct containing the output
            False otherwise
        """
        assert isinstance(
            dbname, string_types), 'dbname should be a string'
        assert isinstance(
            db_type, string_types), 'db_type should be a string'

        if db_type not in self.valid_db_types:
            raise ValueError(
                "db type should be either: {valid_db_types}".format(
                    valid_db_types=', '.join(self.valid_db_types)
                )
            )

        try:
            result = self.server.delete_db(
                self.session_id, dbname, db_type
            )
            self.logger.debug(action="delete_db", result=result)
            return result
        except xmlrpclib.Fault:
            self.logger.exception(
                action="delete_db",
                message="could not delete DB {name}".format(
                    name=dbname
                )
            )
            return False

    def enable_addon(self, dbname, addon):
        """Enables a DB addon for postgresql DBs
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-enable_addon

        Args:
            dbname (str): database's name

        Returns:
            on success, struct containing the output
            False otherwise
        """
        assert isinstance(
            dbname, string_types), 'dbname should be a string'
        assert isinstance(
            addon, string_types), 'addon should be a string'

        if addon not in self.valid_addons:
            raise ValueError(
                "addon should be either: {valid_addons}".format(
                    valid_addons=', '.join(self.valid_addons)
                )
            )

        try:
            result = self.server.enable_addon(
                self.session_id, dbname, 'postgresql', addon
            )
            self.logger.debug(action="enable_addon", result=result)
            return result
        except xmlrpclib.Fault:
            self.logger.exception(
                action="enable_addon",
                message="could not enable addon {addon} on DB {dbname}".format(
                    addon=addon, dbname=dbname
                )
            )
            return False

    def manage_db(self, username, database, db_type, action):
        """Depending on action:
            - either grant full permission to a user
            - revoke db permissions from a user
            - make user the owner of a specified DB
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-grant_db_permissions
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-revoke_db_permissions
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-make_user_owner_of_db

        Args:
            username (str): database user's name
            database (str): database to grant user full permissions to
            db_type (str): either `mysql` or `postgresql`
            action (str): either `make_owner`, `grant_perm`, `revoke_perm`

        Returns:
            on success, struct containing the output
            False otherwise
        """
        operations = {
            'make_owner': self.server.make_user_owner_of_db,
            'grant_perm': self.server.grant_db_permissions,
            'revoke_perm': self.server.revoke_db_permissions
        }

        assert isinstance(
            username, string_types), 'username should be a string'
        assert isinstance(
            db_type, string_types), 'db_type should be a string'
        assert isinstance(
            database, string_types), 'database should be a string'

        if db_type not in self.valid_db_types:
            raise ValueError(
                "db type should be either: {valid_db_types}".format(
                    valid_db_types=', '.join(self.valid_db_types)
                )
            )

        if action not in operations.keys():
            raise Exception(
                "DB method {method_name} not implemented".format(
                    method_name=action
                )
            )

        try:
            result = operations[action](
                self.session_id, username, database, db_type
            )
            self.logger.debug(action=action, result=result)
            return result
        except xmlrpclib.Fault:
            self.logger.exception(
                action=action,
                message="operation against the user {name} on\
                DB {dbname} failed".format(
                    name=username, dbname=database
                )
            )
            return False

    def create_db_user(
        self, username, shell, groups
    ):
        """Create a new shell user
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-create_user

        Args:
            username (str): intended username
            shell (string): user's CLI.
                If shell is 'none', user has FTP access only
            groups (array): extra groups user should be a member of (optional)
        """
        assert isinstance(username, string_types), 'username should be a string'
        assert isinstance(shell, string_types), 'CLI should be a string'
        assert isinstance(groups, list), 'groups should be a list'

        if shell not in self.valid_shells:
            raise ValueError(
                "shell should be either: {valid_shells}".format(
                    valid_shells=', '.join(self.valid_shells)
                )
            )

        try:
            result = self.server.create_user(
                self.session_id, username, shell, groups
            )
            self.logger.debug(action="create_user", result=result)
            return result
        except xmlrpclib.Fault:
            self.logger.exception(
                message="Could not create user {name}, shell {shell}, \
                groups {groups}".format(
                    name=username, shell=shell, groups=groups
                )
            )

            return False

    def delete_user(self, username):
        """Deletes a specified user account
        https://docs.webfaction.com/xmlrpc-api/apiref.html#method-delete_user

        Args:
            username (str):  account to delete
        """
        assert isinstance(username, string_types), 'username should be a string'

        try:
            result = self.server.delete_user(
                self.session_id, username
            )
            self.logger.debug(action="delete_user", result=result)
            return result
        except xmlrpclib.Fault:
            self.logger.exception(
                action="delete_user",
                message="could not delete user {name}".format(
                    name=username
                )
            )
            return False
