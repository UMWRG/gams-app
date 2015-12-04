__author__ = 'Gust'
import _winreg as winreg
import hashlib
import os.path
import datetime
import subprocess
from subprocess import PIPE, Popen
from Crypto.Cipher import AES
from dateutil import parser
from Crypto import Random

import logging
log = logging.getLogger(__name__)


class License(object):
    '''
    Check lic status
    the lic has
    type: e.g ultimate (no time constrain)
              limited (time constraint)
              demo (90 days working version, this default no of day can be changed)
    '''
    def __init__(self, lic_file, REG_PATH, key, period=None):
         done=False
         self.REG_PATH=REG_PATH
         self.key=key
         #open lic file and get the required information from it
         if(os.path.exists(lic_file)):
             try:
                 file = open(lic_file, 'rb')
                 lic_string=file.read()
                 file.close()
                 lic_string=decrypt(lic_string, self.key)
                 lic_=lic_string.split(',')
                 self.type=lic_[0]
                 #self.startdate=lic_[1]
                 #self.period= (lic_[2])
                 #self.Id=lic_[3]
                 done=True
             except Exception, e:
                 raise LicencePluginError("Reading licence file error: "+e.message)
         #else:
             #if there is no lic file, create a temp file which contrains the curremt machine id, this should be send to the software vendor to genarte
             # licence file
             #get_lic_id(lic_file+".tmp", self.key)
             #log.info("No licence found, please send this file: "+lic_file+".tmp"+" to the software vendor if you want to get a licence")

         if(done is False):
             # set demo status
             self.type="demo"
             log.info("No licence found, contact software vendor (hydraplatform1@gmail.com) if you want to get a licence")
             self.startdate=None
             if(period is None):
                 self.period=90
             else:
                 self.period=period
             self.Id=None

    def is_licensed(self):
         cur=datetime.datetime.now()

         if(self.type.lower() == "ultimate"):
             log.info("ultimate licence is installed")
             return True
         else:
             st=get_reg(hash_name_method(self.REG_PATH+"startdate"),  "software\\")
             st=datetime.date.fromordinal(int(st))
             if(st is None):
                 if(self.startdate is None):
                     st=cur
                 else:
                     st=parser.parse(self.startdate)
                 set_reg(hash_name_method(self.REG_PATH+"startdate"), str( datetime.date.toordinal(st)), "software\\")

             startdate=st
             lst=get_reg(hash_name_method(self.REG_PATH+"last_date"),  "software\\")
             if(lst is not None):
                 lst=datetime.date.fromordinal(int(lst))
                 if(lst>cur.date()):
                     self.type="limited demo"
                     log.info("Machine time error")
                     log.info("The licence is limited demo (20 nodes, 20 times steps).  please contact software vendor (hydraplatform1@gmail.com) to get a full licence")
             set_reg(hash_name_method(self.REG_PATH+"last_date"), str(datetime.date.toordinal(cur)), "software\\")
             if(cur.date()> startdate+datetime.timedelta(days=int(self.period))):
                 self.type="limited demo"
                 log.info("The licence is limited demo (20 nodes, 20 times steps) due to time restriction, please contact software vendor (hydraplatform1@gmail.com) to get a full licence")
                 return False
             else:
                 self.type="demo"
                 log.info("Licence type: "+self.type+", will be limited to 20 nodes, and 20 times steps on: "+str(startdate+datetime.timedelta(days=int(self.period))))
                 return True
         return False

def set_reg(name, value, REG_PATH):
    try:
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0,
                                       winreg.KEY_WRITE)
        winreg.SetValueEx(registry_key, name, 0, winreg.REG_SZ, value)
        winreg.CloseKey(registry_key)
        return True
    except WindowsError:
        return False

def get_reg(name, REG_PATH):
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0,
                                       winreg.KEY_READ)
        value, regtype = winreg.QueryValueEx(registry_key, name)
        winreg.CloseKey(registry_key)
        return value
    except WindowsError:
        return None

def encrypt(text, key, key_size=256):
    text = text + b"\0" * (AES.block_size - len(text) % AES.block_size)
    text=text.decode()
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return iv + cipher.encrypt(text)

def decrypt(encrypted_text, key):
    iv = encrypted_text[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = cipher.decrypt(encrypted_text[AES.block_size:])
    return plaintext.rstrip(b"\0")


def get_machine_id():
    p=subprocess.Popen("wmic cpu get ProcessorId /format:csv",stdin=PIPE,stdout=PIPE)
    s= p.stdout.read()
    ss= s.split(',')
    return ss[len(ss)-1]


def  create_lic(type, period, file_name, key, machine_id):
     machine_id=decrypt(machine_id, key)
     print machine_id
     st=str(datetime.datetime.now())
     lic_str=type+","+st+","+str(period)+","+machine_id
     lic_str= encrypt(lic_str, key)
     file = open(file_name, "wb")
     file.write(lic_str)
     file.close()

def  create_lic(type, key, file_name):
     st=str(datetime.datetime.now())
     lic_str=type
     lic_str= encrypt(lic_str, key)
     file = open(file_name, "wb")
     file.write(lic_str)
     file.close()

def get_lic_id( file_name, key):
     machine_id=get_machine_id()
     lic_str= encrypt(machine_id, key)
     file = open(file_name, "wb")
     file.write(lic_str)
     file.close()

def hash_name_method(s):
    hash_object = hashlib.new('DSA')
    hash_object.update(s)
    return str(hash_object.hexdigest())

class LicencePluginError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)