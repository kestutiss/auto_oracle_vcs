'''
Created on 2014 gruod. 12

@author: Kestutis Saldziunas
'''

import datetime
import re
import difflib

if __name__ == '__main__':
    pass

str2 = '/*\n'\
'\n'\
'MODIFICATION HISTORY\n'\
'\n'\
'Person           Date            Comments\n'\
'---------        ------          ------------------------------------------\n'\
'TKSA             2015-03-28      New Sproc\n'\
'\n'\
'*/ \n'


str = '/*\n'\
'\n'\
'MODIFICATION HISTORY\n'\
'\n'\
'Person           Date            Comments\n'\
'---------        ------          ------------------------------------------\n'\
'TKSA             2015-03-28      New Sproc\n'\
'\n'\
'*/ \n'

today = datetime.date.today()

today_str =  today.strftime('%Y-%m-%d')

print today_str

m = re.search('MODIFICATION.*HISTORY.*' + today_str + '(.*?)\n', str, re.DOTALL)

if m != None:
    print m.group(1)

#print re.search('m', 'm').group(1)
#print re.match('a','01a-09B',re.M)

diff = difflib.context_diff(str, str2)
#delta = ''.join(x[2:] for x in diff if x.startswith('+ '))

#print delta
print ''.join(diff),

#try:
#    while 1:
#        print diff.next(),
#except:
#    pass