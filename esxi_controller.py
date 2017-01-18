#!/usr/bin/env python
# filename: esxi_controller.py
#
# This script will help you to manage the virtual machine which based on the ESXi.
# Please use: esxi_controller.py -h to get its usage.
#

import os
import re
import sys
import ssl
import logging
import multiprocessing
from argparse import ArgumentParser
from pysphere import VIServer

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    )

# disabling certificate verification by default for stdlib http clients
ssl._create_default_https_context = ssl._create_unverified_context


class EsxiController(object):
    def __init__(self, servername=None, password=None, username='root'):
        # Specify excluding VMs' preffix
        self.p = re.compile('xx|xx', re.I)

        self.class_name = self.__class__.__name__
        self.servername = servername
        self.username = username
        self.password = password
        self.vmlist = []
        self.vmstatusdict = {}
        self.inUse_vmstatusdict = {}
        self.vmfullnamelist = {}
        self.inUse_vmfullnamelist = {}
        self.vmdict = {}
        self.inUseDict = {}

    def connect(self):
        logging.debug('connecting to %s' % self.servername)
        self.server = VIServer()

        try:
            self.server.connect(self.servername, self.username, self.password,
                                trace_file='/tmp/esxi_debug.txt')
        except BaseException, e:
            logging.debug('Can not connect to %s: %s' % (self.servername, e))
            # sys.exit(1)
        else:
            if self.server.is_connected():
                logging.debug('connected to %s successfully' % self.servername)
                logging.debug('Currently server version is: %s %s'
                              % (self.server.get_server_type(), self.server.get_api_version()))

    def disconnect(self):
        self.server.disconnect()
        logging.debug('To disconnect from server %s\n' % self.servername)

    def get_vmlist(self):
        self.vmlist = self.server.get_registered_vms()
        return self.vmlist

    def get_vmstatus(self):
        for vmPath in self.get_vmlist():
            vm = self.server.get_vm_by_path(vmPath)
            vminfo = vm.get_properties(from_cache=False)
            vmstatus = vm.get_status()
            vmname = vminfo['name']
            self.vmstatusdict[vmname] = vmstatus
        return self.vmstatusdict

    def get_inuse_vmstatus(self):
        for vmPath in self.get_vmlist():
            vm = self.server.get_vm_by_path(vmPath)
            vminfo = vm.get_properties(from_cache=False)
            vmstatus = vm.get_status()
            vmname = vminfo['name']
            in_use_vm = self.p.match(vmname)
            if in_use_vm is not None:
                self.inUse_vmstatusdict[vmname] = vmstatus
        return self.inUse_vmstatusdict

    def get_vmnamelist(self):
        for vmPath in self.get_vmlist():
            vm = self.server.get_vm_by_path(vmPath)
            vminfo = vm.get_properties(from_cache=False)
            vmname = vminfo['name']
            vmfullnameinfo = vminfo['guest_full_name']
            self.vmfullnamelist[vmname] = vmfullnameinfo
        return self.vmfullnamelist

    def get_inuse_vmnamelist(self):
        for vmPath in self.get_vmlist():
            vm = self.server.get_vm_by_path(vmPath)
            vminfo = vm.get_properties(from_cache=False)
            vmname = vminfo['name']
            vmfullnameinfo = vminfo['guest_full_name']
            in_use_vm = self.p.match(vmname)
            if in_use_vm is not None:
                self.inUse_vmfullnamelist[vmname] = vmfullnameinfo
        return self.inUse_vmfullnamelist

    def get_inuse_vmdict(self):
        for vmPath in self.get_vmlist():
            vm = self.server.get_vm_by_path(vmPath)
            vminfo = vm.get_properties(from_cache=False)
            vmname = vminfo['name']
            vmpath = vminfo['path']
            in_use_vm = self.p.match(vmname)
            if in_use_vm is not None:
                self.vmdict[vmname] = vmpath
        return self.vmdict

    def power_off_all(self):
        for vmPath in self.get_vmlist():
            vm = self.server.get_vm_by_path(vmPath)
            if not vm.is_powered_off():
                logging.debug('%s is powered on, now doing power off' % vmPath)
                vm.power_off()

    def power_on_all(self):
        for vmPath in self.get_vmlist():
            vm = self.server.get_vm_by_path(vmPath)
            if not vm.is_powered_on():
                logging.debug('%s is powered off, now doing power on' % vmPath)
                vm.power_on()

    def power_on_in_use(self):
        for vmPath in self.get_vmlist():
            vm = self.server.get_vm_by_path(vmPath)
            vminfo = vm.get_properties(from_cache=False)
            vmname = vminfo['name']
            vmpath = vminfo['path']
            in_use_vm = self.p.match(vmname)
            if in_use_vm is not None and not vm.is_powered_on():
                logging.debug('%s is powered off, now doing power on' % vmname)
                vm.power_on()

    def power_off_in_use(self):
        for vmPath in self.get_vmlist():
            vm = self.server.get_vm_by_path(vmPath)
            vminfo = vm.get_properties(from_cache=False)
            vmname = vminfo['name']
            vmpath = vminfo['path']
            in_use_vm = self.p.match(vmname)
            if in_use_vm is not None and not vm.is_powered_off():
                logging.debug('%s is powered on, now doing power off' % vmname)
                vm.power_off()


def get_vmstatus_list(serverlist, module_n, class_n):
    output_formatter(serverlist, module=module_n, clsname=class_n, argfunc='connect',
                     argfunc2='get_vmstatus', argfunc3='disconnect', initk='vm_name', initv='vm_status')


def get_inuse_vmstatus_list(serverlist, module_n, class_n):
    output_formatter(serverlist, module=module_n, clsname=class_n, argfunc='connect',
                     argfunc2='get_inuse_vmstatus', argfunc3='disconnect', initk='vm_name', initv='vm_status')


def get_vmname_list(serverlist, module_n, class_n):
    output_formatter(serverlist, module=module_n, clsname=class_n, argfunc='connect',
                     argfunc2='get_vmnamelist', argfunc3='disconnect', initk='vm_name', initv='vm_os_type')


def get_inuse_vmname_list(serverlist, module_n, class_n):
    output_formatter(serverlist, module=module_n, clsname=class_n, argfunc='connect',
                     argfunc2='get_inuse_vmnamelist', argfunc3='disconnect', initk='vm_name', initv='vm_os_type')


def get_inusevm_list(serverlist, module_n, class_n):
    output_formatter(serverlist, module=module_n, clsname=class_n, argfunc='connect',
                     argfunc2='get_inuse_vmdict', argfunc3='disconnect', initk='vm_name', initv='vm_path')


def power_on_all_vm(serverlist, module_n, class_n):
    control_vm(serverlist, module=module_n, clsname=class_n,
               argfunc='connect', argfunc2='power_on_all', argfunc3='disconnect')


def power_off_all_vm(serverlist, module_n, class_n):
    control_vm(serverlist, module=module_n, clsname=class_n,
               argfunc='connect', argfunc2='power_off_all', argfunc3='disconnect')


def power_on_inuse_vm(serverlist, module_n, class_n):
    control_vm(serverlist, module=module_n, clsname=class_n,
               argfunc='connect', argfunc2='power_on_in_use', argfunc3='disconnect')


def power_off_inuse_vm(serverlist, module_n, class_n):
    control_vm(serverlist, module=module_n, clsname=class_n,
               argfunc='connect', argfunc2='power_off_in_use', argfunc3='disconnect')


def __printbf(str):
    print '\033[1;2;34m%s\033[0m' % str


def control_vm(serverlist, module=None, clsname=None, argfunc=None,
               argfunc2=None, argfunc3=None):
    for k, v in serverlist.items():
        obj = __import__(module, globals(), locals(), [clsname])
        cls = getattr(obj, clsname)
        obj = cls(k, v)
        con = getattr(obj, argfunc)
        con()

        func = getattr(obj, argfunc2)
        func()

        discon = getattr(obj, argfunc3)
        discon()


def output_formatter(serverlist, module=None, clsname=None, argfunc=None,
                     argfunc2=None, argfunc3=None, initk=None, initv=None):
    for k, v in serverlist.items():
        obj = __import__(module, globals(), locals(), [clsname])
        c = getattr(obj, clsname)
        obj = c(k, v)
        func = getattr(obj, argfunc)
        func()

        func2 = getattr(obj, argfunc2)
        vm_dict = func2()
        width = 110
        key_width = 60
        value_width = 20
        header_format = '%-*s%*s'
        format = '%-*s%*s'
        print '=' * width
        __printbf(header_format % (key_width, initk, value_width, initv))
        for k1, v1 in vm_dict.items():
            print '-' * width
            __printbf(format % (key_width, k1, value_width, v1))
        print '=' * width

        func3 = getattr(obj, argfunc3)
        func3()


def mul_proc_exec(serverlist, modulename, classname, argfunc):
    jobs = []
    for k, v in serverlist.items():
        sdict = {k: v}
        p = multiprocessing.Process(target=argfunc, args=(sdict, modulename, classname))
        jobs.append(p)
        p.start()


def main():
    parser = ArgumentParser(description='Esxi vm manager. Please check \
                             the log "/tmp/esxi_debug.txt" if have any questions. \
                             You can terminate the script by "Ctrl + c".', \
                            epilog='Ex: esxi_controller.py -list_inuse all ')
    parser.add_argument('-power_on', dest='power_on', choices=('all', 'usevms'), \
                        help='power on all vms or in using vms, the optional parameter (all | usevms)')
    parser.add_argument('-power_off', dest='power_off', choices=('all', 'usevms'), \
                        help='power off all vms or in using vms, the optional parameter (all | usevms)')
    parser.add_argument('-list_status', dest='list_status', choices=('all', 'usevms'), \
                        help='list all vms name and its status, the optional parameter (all | usevms)')
    parser.add_argument('-list_type', dest='list_type', choices=('all', 'usevms'), \
                        help='list all vms name and its os type, the optional parameter (all | usevms)')
    parser.add_argument('-list_inuse', nargs='?', dest='list_inuse', const='all', \
                        choices=('all',), help='list all of vms were using. Default is all, \
                         if don\'t specify parameter')
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    args = parser.parse_args()

    SERVERLIST = {
        # Esxi server IP address: password
        'xx.xx.xx.xx': 'xx',
        'xx.xx.xx.xx': 'xx',
    }

    # Obtain the current module name, class name
    FILENAME = os.path.realpath(sys.argv[0]).split(os.sep)[-1]
    MODULE_NAME = FILENAME.split('.')[0]
    CLASS_NAME = EsxiController().class_name

    if args.power_on == 'all':
        logging.debug('start all servers.')
        mul_proc_exec(SERVERLIST, MODULE_NAME, CLASS_NAME, power_on_all_vm)
    elif args.power_on == 'usevms':
        logging.debug('start all servers which we are using.')
        mul_proc_exec(SERVERLIST, MODULE_NAME, CLASS_NAME, power_on_inuse_vm)
    elif args.power_off == 'all':
        logging.debug('stop all servers.')
        mul_proc_exec(SERVERLIST, MODULE_NAME, CLASS_NAME, power_off_all_vm)
    elif args.power_off == 'usevms':
        logging.debug('stop all servers which we are using.')
        mul_proc_exec(SERVERLIST, MODULE_NAME, CLASS_NAME, power_off_inuse_vm)
    elif args.list_status == 'all':
        mul_proc_exec(SERVERLIST, MODULE_NAME, CLASS_NAME, get_vmstatus_list)
    elif args.list_status == 'usevms':
        mul_proc_exec(SERVERLIST, MODULE_NAME, CLASS_NAME, get_inuse_vmstatus_list)
    elif args.list_type == 'all':
        mul_proc_exec(SERVERLIST, MODULE_NAME, CLASS_NAME, get_vmname_list)
    elif args.list_type == 'usevms':
        mul_proc_exec(SERVERLIST, MODULE_NAME, CLASS_NAME, get_inuse_vmname_list)
    elif args.list_inuse == 'all':
        mul_proc_exec(SERVERLIST, MODULE_NAME, CLASS_NAME, get_inusevm_list)
    else:
        print 'Please specify an action. Aborting..\nUse -h for help'
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print '^C received. Termination of the script..'
