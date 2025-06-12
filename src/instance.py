#!/usr/bin/env python3
import os
import tempfile, fcntl
import psutil


class SingleInstance:
    def __init__(self, lockfile=None):
        self.lockfile = lockfile or os.path.join(tempfile.gettempdir(), "internet-monitor.lock")
        self.fd = None

    def already_running(self):
        if os.path.exists(self.lockfile):
            try:
                with open(self.lockfile, 'r') as f:
                    pid = int(f.read().strip())
                if psutil.pid_exists(pid):
                    return True
            except:
                pass
        try:
            os.unlink(self.lockfile)
        except:
            pass
        return False

    def create_lock(self):
        try:
            self.fd = open(self.lockfile, 'w')
            self.fd.write(str(os.getpid()))
            self.fd.flush()
            try:
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (IOError, BlockingIOError):
                return False
            return True
        except Exception as e:
            print(f"Error creando bloqueo: {e}")
            return False

    def remove_lock(self):
        if self.fd:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
                self.fd.close()
            except:
                pass
        try:
            os.unlink(self.lockfile)
        except:
            pass
