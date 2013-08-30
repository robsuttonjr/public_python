#!/usr/bin/env python

# fedex_cir_import.py
# Created by Rob Sutton on 08/24/13
# robsuttonjr@yahoo.com 
#
# Simple script to extract Fedex CIR report from a file created from email.
# I prefer a simple script over building classes for everything.  
# Maybe one day I will put into a class who knows but for now, this is it!
# I am always open to ideas.

print 'begin script - fedex_cir_import.py'

import os, pdb, psycopg2

path = '/usr/local/cirdata/'
imported = '/usr/local/cirdata/imported/'
phoenixDB = psycopg2.connect("dbname='database' user='user' host='host' password='password'")
    

for file in os.listdir(path):
    current = os.path.join(path, file)
    if os.path.isfile(current):
        ediNumber = ''
        invoiceDate = ''
        invoiceNumber = ''
        accountNumber = ''
        numberAirbills = ''
        invoiceAmount = ''
        fileTotal = ''

        rowOn = False
        nextLineLast = False
        data = open(current, "rb")
        for line in data:
            
            #print line
            if 'Contact' in line:
                ediNumber = line.split(':')[2].replace('\r\n','').replace(' ','')
                
            if 'Address' in line:
                invoiceDate = line.split(':')[2].replace('\r\n','').replace(' ','')
                invoiceDate = invoiceDate[6:]+'-'+invoiceDate[:-8]+'-'+invoiceDate[3:-5]
    
            if 'Customer Nbr' in line:
                rowOn = True

            if rowOn  == True and 'Customer Nbr' not in line:

                if line == '\r\n':
                    nextLineLast = True
                else:
                    if nextLineLast == False:  
                        try:
                            invoiceNumber = line.split()[1].replace('\r\n','')
                            accountNumber = line.split()[0].replace('\r\n','').zfill(9)
                            numberAirbills = line.split()[2].replace('\r\n','')
                            invoiceAmount = line.split()[3].replace('\r\n','')
                        except:    
                            pass       
                

                cursorPhoenix = phoenixDB.cursor()
                insertText = """insert into configmgr_fedexcir (edi_number, invoice_date, account_number, invoice_number, number_of_airbills, invoice_amount, file_name) values ('%s', '%s', '%s', %s, %s, '%s', '%s')""" % (ediNumber, invoiceDate, accountNumber, invoiceNumber, numberAirbills, invoiceAmount, file)

                try:
                    if rowOn == True and nextLineLast == False:
                        print file, fileTotal, ediNumber, invoiceDate, accountNumber, invoiceNumber, numberAirbills, invoiceAmount
                        cursorPhoenix.execute("""select * from configmgr_fedexcir where edi_number = '%s' and invoice_date = '%s' and account_number = '%s' and invoice_number = '%s' """ % (ediNumber, invoiceDate, accountNumber, invoiceNumber))
                        results = cursorPhoenix.fetchone()
          
                        if results is None:
                            cursorPhoenix.execute(insertText)
                            phoenixDB.commit() 
                except:
                    print 'insert failed:  ' + insertText

                if nextLineLast == True and line != '\r\n':
                    rowOn = False
                    fileTotal = line.split()[2].replace('\r\n','')
                    cursorPhoenix = phoenixDB.cursor()
                    updateString = """update configmgr_fedexcir set file_total = '%s' where file_name = '%s'  """ % (fileTotal, file)
        
                    cursorPhoenix.execute(updateString)
                    phoenixDB.commit() 
                        
        os.rename(os.path.join(path, file), os.path.join(imported, file))

print 'end script - fedex_cir_import.py'
