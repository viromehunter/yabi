# -*- coding: utf-8 -*-
### BEGIN COPYRIGHT ###
#
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
# 
### END COPYRIGHT ###

from ExecConnector import ExecConnector, ExecutionError

# a list of system environment variables we want to "steal" from the launching environment to pass into our execution environments.
ENV_CHILD_INHERIT = ['PATH']

# a list of environment variables that *must* be present for this connector to function
ENV_CHECK = []

# the schema we will be registered under. ie. schema://username@hostname:port/path/
SCHEMA = "ssh+pbspro"

DEBUG = False

# where we temporarily store the submission scripts on the submission host
TMP_DIR = "/tmp"

from twisted.web2 import http, responsecode, http_headers, stream

import shlex
import os
import uuid
import json
from utils.protocol import globus
import stackless
import tempfile

from utils.stacklesstools import sleep
from utils.protocol import ssh

from conf import config

from TaskManager.TaskTools import RemoteInfo

sshauth = ssh.SSHAuth.SSHAuth()

# for Job status updates, poll this often
def JobPollGeneratorDefault():
    """Generator for these MUST be infinite. Cause you don't know how long the job will take. Default is to hit it pretty hard."""
    delay = 10.0
    while delay<60.0:
        yield delay
        delay *= 1.05           # increase by 5%
    
    while True:
        yield 60.0


class SSHQsubException(Exception):
    pass
class SSHQstatException(Exception):
    pass

class SSHPbsproConnector(ExecConnector, ssh.KeyStore.KeyStore):
    def __init__(self):
        ExecConnector.__init__(self)
        
        configdir = config.config['backend']['certificates']
        ssh.KeyStore.KeyStore.__init__(self, dir=configdir)
    
    def _ssh_qsub(self, working, stdout, stderr, command, yabiusername, username, host, modules, remote_url, **creds):
        """This submits via ssh the qsub command. This returns the jobid, or raises an exception on an error"""
        assert type(modules) is not str and type(modules) is not unicode, "parameter modules should be sequence or None, not a string or unicode"
        
        submission_script = os.path.join(TMP_DIR,str(uuid.uuid4())+".sh")
        
        # build up our remote qsub command
        ssh_command = "cat >'%s' && "%(submission_script)
        ssh_command += "qsub -N '%s' -e '%s' -o '%s' '%s'"%(    
                                                                        "yabi-task-"+remote_url.rsplit('/')[-1],
                                                                        os.path.join(working,stderr),
                                                                        os.path.join(working,stdout),
                                                                        submission_script
                                                                    )
        ssh_command += " ; EXIT=$? "
        ssh_command += " ; rm '%s'"%(submission_script)
        #ssh_command += " ; echo $EXIT"
        ssh_command += " ; exit $EXIT"

        if not creds:
            creds = sshauth.AuthProxyUser(yabiusername, SCHEMA, username, host, "/")
    
        usercert = self.save_identity(creds['key'])
        
        # build our command script
        script = ["module load %s"%mod for mod in modules or []]
        script.append( "cd '%s'"%working )                                              # TODO: what if the path has a single quote in it?
        script.append( command )
        script_string = "\n".join(script)+"\n"
        
        if DEBUG:
            print "_ssh_qsub"
            print "usercert:",usercert
            print "command:",command
            print "username:",username
            print "host:",host
            print "working:",working
            print "port:","22"
            print "stdout:",stdout
            print "stderr:",stderr
            print "modules",modules
            print "password:","*"*len(creds['password'])
            print "script:",script_string
            
        pp = ssh.Run.run(usercert,ssh_command,username,host,working=None,port="22",stdout=None,stderr=None,password=creds['password'], modules=modules, streamin=script_string)
        while not pp.isDone():
            stackless.schedule()
          
        if DEBUG:
            print "EXITCODE:",pp.exitcode
            print "STDERR:",pp.err
            print "STDOUT:",pp.out
            
        if pp.exitcode==0:
            # success
            return pp.out.strip().split("\n")[-1]
        else:
            raise SSHQsubException("SSHQsub error: SSH exited %d with message %s"%(pp.exitcode,pp.err))
            
    def _ssh_qstat(self, jobid, working, stdout, stderr, command, yabiusername, username, host, modules, **creds):
        """This submits via ssh the qstat command. This takes the jobid"""
        assert type(modules) is not str and type(modules) is not unicode, "parameter modules should be sequence or None, not a string or unicode"
        
        ssh_command = "cat > /dev/null && qstat -x -f '%s'"%( jobid )
        ssh_command += " | sed -ne '1h;1!H;${;g;s/\\n\\t//g;p;}'"
        
        
        if not creds:
            creds = sshauth.AuthProxyUser(yabiusername, SCHEMA, username, host, "/")
    
        usercert = self.save_identity(creds['key'])
        
        if DEBUG:
            print "usercert:",usercert
            print "command:",command
            print "username:",username
            print "host:",host
            print "working:",working
            print "port:","22"
            print "stdout:",stdout
            print "stderr:",stderr
            print "modules",modules
            print "password:","*"*len(creds['password'])
            
        pp = ssh.Run.run(usercert,ssh_command,username,host,working=None,port="22",stdout=None,stderr=None,password=creds['password'], modules=modules )
        while not pp.isDone():
            stackless.schedule()
            
        if pp.exitcode==0:
            # success. lets process our qstat results
            output={}
            
            for line in pp.out.split("\n"):
                line = line.strip()
                if " = " in line:
                    key, value = line.split(" = ")
                    output[key] = value
                    
            return {jobid:output}
        else:
            raise SSHQstatException("SSHQstat error: SSH exited %d with message %s"%(pp.exitcode,pp.err))

    def run(self, yabiusername, command, working, scheme, username, host, remote_url, channel, stdout="STDOUT.txt", stderr="STDERR.txt", walltime=60, max_memory=1024, cpus=1, queue="testing", jobType="single", module=None, **creds):
        try:
            modules = [] if not module else [X.strip() for X in module.split(",")]
            jobid = self._ssh_qsub(working, stdout, stderr, command, yabiusername, username, host, modules, remote_url, **creds)
        except (SSHQsubException, ExecutionError), ee:
            channel.callback(http.Response( responsecode.INTERNAL_SERVER_ERROR, {'content-type': http_headers.MimeType('text', 'plain')}, stream = str(ee) ))
            return
        
        # send an OK message, but leave the stream open
        client_stream = stream.ProducerStream()
        channel.callback(http.Response( responsecode.OK, {'content-type': http_headers.MimeType('text', 'plain')}, stream = client_stream ))
        
        # now the job is submitted, lets remember it
        self.add_running(jobid, {'username':username})
        
        # lets report our id to the caller
        client_stream.write("id=%s\n"%jobid)
        
        try:
            self.main_loop( client_stream, jobid, remote_url, working, stdout, stderr, command, yabiusername, username, host, modules,  **creds)
        except (ExecutionError, SSHQstatException), ee:
            import traceback
            traceback.print_exc()
            client_stream.write("Error\n")
        finally:
                
            # delete finished job
            self.del_running(jobid)
            
            client_stream.finish()
            
    def main_loop(self, client_stream, jobid, remote_url, working, stdout, stderr, command, yabiusername, username, host, modules,  **creds):
        newstate = state = None
        delay = JobPollGeneratorDefault()
        while state!="Done":
            # pause
            sleep(delay.next())
            
            jobsummary = self._ssh_qstat(jobid, working, stdout, stderr, command, yabiusername, username, host, modules,  **creds)
            self.update_running(jobid,jobsummary)
            
            if jobid in jobsummary:
                # job has not finished
                if 'job_state' in jobsummary[jobid]:
                    status = jobsummary[jobid]['job_state']
                    
                    if status == 'F' or status == "X":
                        # state 'F' means complete OR error
                        if 'Exit_status' in jobsummary[jobid] and jobsummary[jobid]['Exit_status'] == '0':
                            newstate = "Done"
                        else:
                            newstate = "Error"
                    else:
                        newstate = dict(B="Running", E="Running", F="Done", H="Pending", M="Pending", Q="Unsubmitted", R="Running", S="Running", T="Pending", U="Pending", W="Pending", X="Done")[status]
                    
                else:
                    newstate = "Done"
                
                
            else:
                # job has finished
                sleep(15.0)                      # deal with SGE flush bizarreness (files dont flush from remote host immediately. Totally retarded)
                print "ERROR: jobid %s not in jobsummary"%jobid
                print "jobsummary is",jobsummary
                
                # if there is standard error from the qstat command, report that!
                
                
                newstate = "Error"
            
            #if DEBUG:
                #print "Job summary:",jobsummary
                
            
            if state!=newstate:
                state=newstate
                #print "Writing state",state
                client_stream.write("%s\n"%state)
                
                # report the full status to the remote_url
                if remote_url:
                    if jobid in jobsummary and jobsummary[jobid]:
                        RemoteInfo(remote_url,json.dumps(jobsummary[jobid]))
                    else:
                        print "Cannot call RemoteInfo call for job",jobid
                
            if state=="Error":
                #print "CLOSING STREAM"
                client_stream.finish()
                return        
 