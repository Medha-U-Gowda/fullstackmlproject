import re
# This file contains all the business validation logic
def validationid(userid):
    if(len(userid)>=6):
        return True
    return False
def validatepassword(password):
    if (len(password)>=8):
        return True
    return False
def confirmpassword(value1,value2):
    if (value1==value2):
        return True
    return False
def validatename(value):
    value = value.strip()           
    if value.replace(" ", "").isalpha() and len(value) >= 1:
        return True
    return False
def validatenumber(contact):
    if(len(contact)==10 and contact.isdigit()):
        return True
    return False
def validateemail(emailid):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, emailid):
        return True
    return False
def comparecaptcha(v1,v2):
    if (v1==v2):
        return True
    return False

    