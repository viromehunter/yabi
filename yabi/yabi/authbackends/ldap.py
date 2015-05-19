import logging
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from yabi import ldaputils


logger = logging.getLogger(__name__)


class LDAPBackend(ModelBackend):
    def authenticate(self, username=None, password=None):
        if not password:
            logger.warning('Empty password supplied. Access denied')
            return None

        if not self.can_log_in(username, password):
            logger.info("Couldn't log in with LDAP user '%s' and the supplied password" % username)
            return None

        user = self.get_ldap_user(username)
        if user is None:
            logger.info("LDAP user '%s' doesn't exist" % username)
            return None

        if not (ldaputils.is_user_member_of_yabi_group(user.dn) or
                ldaputils.is_user_member_of_yabi_admin_group(user.dn)):
            logger.info("LDAP user '%s' not member of Yabi LDAP group '%s'" % user.dn)
            return None

        try:
            django_user = User.objects.get(username=username)
            if settings.AUTH_LDAP_SYNC_USER_ON_LOGIN:
                ldaputils.update_yabi_user(django_user, user)
        except User.DoesNotExist:
            django_user = ldaputils.create_yabi_user(user)

        logger.info("Login Success '%s'" % django_user)

        return django_user

    def can_log_in(self, username, password):
        user = self.get_ldap_user(username)
        if user is None:
            return False
        if not ldaputils.can_bind_as(user.dn, password):
            logger.info("Can't bind with LDAP user '%s' and the supplied password" % username)
            return False

        return True

    def get_ldap_user(self, username):
        try:
            user = ldaputils.get_user(username)
            return user
        except ldaputils.LDAPUserDoesNotExist:
            logger.info("LDAP user '%s' does not exist" % username)
