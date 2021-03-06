# (C) Copyright 2011, Centre for Comparative Genomics, Murdoch University.
# All rights reserved.
#
# This product includes software developed at the Centre for Comparative Genomics
# (http://ccg.murdoch.edu.au/).
#
# TO THE EXTENT PERMITTED BY APPLICABLE LAWS, YABI IS PROVIDED TO YOU "AS IS,"
# WITHOUT WARRANTY. THERE IS NO WARRANTY FOR YABI, EITHER EXPRESSED OR IMPLIED,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT OF THIRD PARTY RIGHTS.
# THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF YABI IS WITH YOU.  SHOULD
# YABI PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING, REPAIR
# OR CORRECTION.
#
# TO THE EXTENT PERMITTED BY APPLICABLE LAWS, OR AS OTHERWISE AGREED TO IN
# WRITING NO COPYRIGHT HOLDER IN YABI, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR
# REDISTRIBUTE YABI AS PERMITTED IN WRITING, BE LIABLE TO YOU FOR DAMAGES, INCLUDING
# ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE
# USE OR INABILITY TO USE YABI (INCLUDING BUT NOT LIMITED TO LOSS OF DATA OR
# DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES
# OR A FAILURE OF YABI TO OPERATE WITH ANY OTHER PROGRAMS), EVEN IF SUCH HOLDER
# OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
from yabi.yabiengine.urihelper import url_join
import logging


logger = logging.getLogger(__name__)


class BaseBackend(object):
    task = None
    cred = None
    yabiusername = None

    def working_dir_uri(self):
        """working dir"""
        return url_join(self.task.job.fs_backend, self.task.working_dir)

    def working_input_dir_uri(self):
        """working/input dir"""
        return url_join(self.working_dir_uri(), 'input')

    def working_output_dir_uri(self):
        """working/output dir"""
        return url_join(self.working_dir_uri(), 'output')

    # The following backend_auth description is used by multiple backends
    SSH_AUTH = {
        "class": "SSH",
        "username": "Login name for remote host",
        "key": "Optional SSH private key.",
        "password": "Can be a normal login password, passphrase for SSH key, or empty."
    }

    _backends = []

    @classmethod
    def register(cls, *schemes):
        for scheme in schemes:
            BaseBackend._backends.append((scheme, cls))
        return cls

    @classmethod
    def get_scheme_choices(cls):
        return [(k, "%s - %s" % (k, getattr(backendcls, "backend_desc", backendcls.__name__)))
                for k, backendcls in cls._backends]

    @classmethod
    def get_auth_class_choices(cls):
        auths = [getattr(backendcls, "backend_auth", {}).get("class", None)
                 for k, backendcls in cls._backends]
        return [(c, c) for c in sorted(set(auths)) if c]

    @classmethod
    def get_backend_cls_for_scheme(cls, scheme, basecls=None):
        """
        Returns the backend class registered with `scheme'. If `basecls' is
        given, the backend class must be a subclass of it. If no
        matching class is found, None is returned.
        """
        basecls = basecls or cls
        for backendscheme, backendcls in cls._backends:
            if backendscheme == scheme and issubclass(backendcls, basecls):
                return backendcls
        return None

    @classmethod
    def create_backend_for_scheme(cls, scheme, basecls=None, *args, **kwargs):
        """
        Instantiates a backend for the given URL scheme which is an
        instance of `basecls'.
        """
        BackendCls = cls.get_backend_cls_for_scheme(scheme, basecls)
        return BackendCls(*args, **kwargs) if BackendCls else None

    @classmethod
    def get_caps(cls):
        """
        Returns a dict mapping backend schemes to their "capabilities" --
        i.e. whether they are for filesystem or execution backends, or
        both.
        """
        caps = {}
        from . import FSBackend, ExecBackend
        for scheme, be in cls._backends:
            k = caps.setdefault(scheme, {})
            k["fs"] = k.get("fs", False) or issubclass(be, FSBackend)
            k["exec"] = k.get("exec", False) or issubclass(be, ExecBackend)
            if hasattr(be, "backend_auth"):
                k.setdefault("auth", {}).update(be.backend_auth)
            for attr in "lcopy_supported", "link_supported":
                k[attr] = k.get(attr, False) or getattr(be, attr, False)
        return caps
