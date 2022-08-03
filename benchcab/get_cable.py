#!/usr/bin/env python

"""
Get the head of the CABLE trunk, the user branch and CABLE-AUX

That's all folks.
"""

__author__ = "Martin De Kauwe"
__version__ = "1.0 (09.03.2019)"
__email__ = "mdekauwe@gmail.com"

import os
import subprocess
import datetime
import getpass
import tempfile


class GetCable(object):
    def __init__(
        self, src_dir=None, root="https://trac.nci.org.au/svn/cable", user=None
    ):

        self.src_dir = src_dir
        self.root = root
        self.user = user
        self.msg = '"checked out repo"'
        self.aux_dir = "CABLE-AUX"
        self.home_dir = os.environ["HOME"]

    def main(self, name=None, trunk=False, share_branch=False, revision=-1):

        self.initialise_stuff()

        self.get_repo(name, trunk, share_branch, revision)

    def initialise_stuff(self):

        if not os.path.exists(self.src_dir):
            os.makedirs(self.src_dir)

    def get_repo(self, repo_name, trunk, share_branch, revision):

        need_pass = False
        cwd = os.getcwd()
        os.chdir(self.src_dir)

        # Check if a specified version is required. Negative value means take the latest
        rev_opt=""
        if revision > 0:
            rev_opt=f"-r {revision}"

        try:
            where = os.listdir("%s/.subversion/auth/svn.simple/" % (self.home_dir))
            if len(where) == 0:
                pswd = "'" + getpass.getpass("Password:") + "'"
                need_pass = True
        except FileNotFoundError:
            pswd = "'" + getpass.getpass("Password:") + "'"
            need_pass = True

        # Checkout the head of the trunk ...
        if trunk:

            if need_pass:
                cmd = f"svn checkout {rev_opt} {self.root}/trunk --password {pswd}"

                with tempfile.NamedTemporaryFile(mode="w+t") as f:
                    f.write(cmd)
                    f.flush()

                    error = subprocess.call(["/bin/bash", f.name])
                    if error == 1:
                        raise ("Error downloading repo")
                    f.close()
            else:
                cmd = f"svn checkout {rev_opt} {self.root}/trunk" 

                error = subprocess.call(cmd, shell=True)
                if error == 1:
                   raise ("Error downloading repo")

        # Checkout named branch ...
        else:

            if need_pass:

                if share_branch:
                    cmd = f"svn checkout {rev_opt} {self.root}/branches/Share/{repo_name} --password {pswd}"
                else:
                    cmd = f"svn checkout {rev_opt} {self.root}/branches/Users/{self.user}/{repo_name} --password {pswd}"

                with tempfile.NamedTemporaryFile(mode="w+t") as f:
                    f.write(cmd)
                    f.flush()

                    error = subprocess.call(["/bin/bash", f.name])
                    if error == 1:
                        raise ("Error downloading repo")
                    f.close()
            else:
                if share_branch:
                    cmd = f"svn checkout {rev_opt} {self.root}/branches/Share/{repo_name}"
                else:
                    cmd = f"svn checkout {rev_opt} {self.root}/branches/Users/{self.user}/{repo_name}"

                error = subprocess.call(cmd, shell=True)
                if error == 1:
                    raise ("Error downloading repo")

        # Checkout CABLE-AUX
        if need_pass:

            if not os.path.exists(self.aux_dir):
                cmd = "svn checkout %s/branches/Share/%s %s --password %s" % (
                    self.root,
                    self.aux_dir,
                    self.aux_dir,
                    pswd,
                )
                with tempfile.NamedTemporaryFile(mode="w+t") as f:
                    f.write(cmd)
                    f.flush()

                    error = subprocess.call(["/bin/bash", f.name])
                    if error == 1:
                        raise ("Error checking out CABLE-AUX")
                    f.close()
        else:
            if not os.path.exists(self.aux_dir):
                cmd = "svn checkout %s/branches/Share/%s %s" % (
                    self.root,
                    self.aux_dir,
                    self.aux_dir,
                )
                error = subprocess.call(cmd, shell=True)
                if error == 1:
                    raise ("Error checking out CABLE-AUX")

        os.chdir(cwd)


if __name__ == "__main__":

    now = datetime.datetime.now()
    date = now.strftime("%d_%m_%Y")

    # ------------- Change stuff ------------- #
    src_dir = "src"
    user = "mgk576"
    repo1 = "Trunk_%s" % (date)
    repo2 = "CABLE3.0/ReStructured4JAC.1"
    # ------------------------------------------- #

    G = GetCable(src_dir=src_dir, user=user)
    G.main(name=repo1, trunk=True)
    G.main(name=repo2, trunk=False, user_branch=False, share_branch=True)
