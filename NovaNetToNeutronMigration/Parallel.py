#!/usr/bin/python

import subprocess
import threading


class Parallel():

    def __init__(self, LOG):
        self.hosts = []  # List of all hosts/ips in our input queue
        self.thread_count = 20
        self.LOG = LOG
        # Lock object to keep track the threads in loops, where
        # it can potentially be race conditions.
        self.lock = threading.Lock()
        self.result = []
        self.index = -1

    def task(self, command, arg):
        cmd = command.split()
        cmd.append(str(arg))
        self.LOG.debug(cmd)
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE) # flake8: noqa
        except OSError as e:
            self.LOG.error(e)

        stdout, stderr = p.communicate()
        code = p.returncode
        return {'code': code, 'stdout': stdout}

    def pop_queue(self):
        vm = None
        self.lock.acquire()  # Grab or wait+grab the lock.
        if self.index < (len(self.hosts)-1):
            self.index = self.index + 1
            vm = self.hosts[self.index]
        # Release the lock, so another thread could grab it.
        self.lock.release()
        return [vm, self.index]

    def dequeue(self, command):
        while True:
            [vm, index] = self.pop_queue()
            if not vm:
                return None
            self.result[index] = self.task(command, vm)

    def start(self, command):
        threads = []
        kwargs = {'command': command}
        # Initialize results before starting the threads
        self.result = [0]*len(self.hosts)
        for i in range(self.thread_count):
            # Create self.thread_count number of threads that together will
            # cooperate removing every task in the list.
            t = threading.Thread(target=self.dequeue, kwargs=kwargs)
            t.start()
            threads.append(t)
        # Wait until all the threads are done. .join() is blocking.
        [thread.join() for thread in threads]
        return self.result
