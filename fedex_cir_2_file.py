#!/usr/bin/env python

# fedex_cir_2_file.py
# Created by Rob Sutton on 08/24/13
# robsuttonjr@yahoo.com 
#
# Simple script to extract Fedex CIR report from email then copy to file.
# I prefer a simple script over building classes for everything.  
# Maybe one day I will put into a class who knows but for now, this is it!
# I am always open to ideas.

print 'begin script - fedex cir 2 file'

import sys, os, pdb,  imaplib, email, getpass, datetime, time, mimetypes, MySQLdb, psycopg2

def importFedexCirs():
    detach_dir = '/usr/local/cirdata'
     # TEST USER
    #user = "testuser@gmail.com"
    #pwd = "password"AIL
    # LIVE USER
    user = "liveuser@gmail.com"
    pwd = "password"

    ediNumber  = ''
    invoiceDate = ''
    lineContentTransferEncoding = ''

    # connecting to the gmail imap server
    m = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    m.login(user,pwd)
    m.select("INBOX") # here you a can choose a mail box like INBOX instead

    resp, items = m.search(None, "ALL") # you could filter using the IMAP rules here (check http://www.example-code.com/csharp/imap-search-critera.asp)
    items = items[0].split() # getting the mails id

    for emailid in items:
        resp, data = m.fetch(emailid, "(RFC822)") # fetching the mail, "`(RFC822)`" means "get the whole stuff", but you can ask for headers only, etc
        email_body = data[0][1] # getting the mail content
        mail = email.message_from_string(email_body) # parsing the mail content to get a mail object

        bodyLines = email_body.split('\r\n')

        bodyLineNumber = 0
        readRest = False
        
        for line in bodyLines:
            
            #print 'Processing Body Line Index Number:  %s' % bodyLineNumber      
            if  'FEDEX EDI CUSTOMER INVOICE REPORT' in line:
                readRest = True
                cirReport = ''

            if readRest == True:
                cirReport += line + '\r\n'
                
            if line == '****END OF REPORT****':
                readRest = False
                
                cirReportData = cirReport.split('\r\n')
                cirReport = cirReport.replace('Invoice Date:\r\n','Invoice Date: ')
                fileName = cirReportData[2][62:] + '_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                
                fp = open('/usr/local/cirdata/' + fileName, 'wb')
                fp.write(cirReport)
                fp.close() 

                

            bodyLineNumber += 1      
          
        #Check if any attachments at all
        if mail.get_content_maintype() != 'multipart':
            continue
        
        if mail["Body"] is None:
            print "["+mail["From"]+"] :" + mail["Subject"]
        else:
            pdb.set_trace()
            print "["+mail["From"]+"] :" + mail["Subject"]+ mail["Body"]


        # we use walk to create a generator so we can iterate on the parts and forget about the recursive headach
        for part in mail.walk():
            # multipart are just containers, so we skip them
            if part.get_content_maintype() == 'multipart':
                continue

            # is this part an attachment ?
            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()
            counter = 1

            # if there is no filename, we create one with a counter to avoid duplicates
            if not filename:
                filename = 'part-%03d%s' % (counter, 'bin')
                counter += 1

            att_path = os.path.join(detach_dir, filename)

            #Check if its already there
            if not os.path.isfile(att_path) :
                # finally write the stuff
                fp = open(att_path, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()


        # COPY EMAIL TO FOLDER
        copyStatus = m.copy(emailid, 'CIRIMPORTED')
        print 'id of message copied is: %s status: %s' % (emailid,copyStatus)
 
        # SET THE MESSAGE TO HAVE '\Deleted' FLAG (EXPUNGE WILL COMPLETE DELETE PROCESS)
        storeStatus = m.store(emailid,"+FLAGS", r'(\Deleted)')
        print 'id of message stored is: %s status: %s %s' % (emailid,storeStatus[0],storeStatus[1])
        #print '******'
    
    #DELETES ANY EMAIL MARKED \Deleted    
    m.expunge()
    m.close()
    m.logout()
    
importFedexCirs()

print 'end script - fedex cir 2 file'
