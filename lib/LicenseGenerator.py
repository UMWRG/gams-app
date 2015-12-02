__author__ = 'Gust'

from License import create_lic

#input file which sent by user, it contains his machine idenetitfications
file_="F:\\work\\Apps\\hydra_plugins\\GAMS\Export\\gasm_lic.txt.tmp"
#outputfile which contains the Licence
lic_file="F:\\work\\Apps\\hydra_plugins\\GAMS\Export\\gasm_lic.txt"


file = open(file_, 'rb')
machine_id=file.read()
file.close()

#key for encrypt and decrypt
# this should be the same asw the one in Hydar gams lib file
key="12/FfCHspo*&s}:QMwd><s?:"

try:
    create_lic( machine_id, "Time limited", 12, lic_file, key)
    print "Done ", lic_file , "is genrated"
except Exception, e:
    print e.message