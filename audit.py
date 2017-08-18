
# coding: utf-8

# In[6]:

import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint


# In[7]:

mapping_direction = {'NE': 'Northeast', 'SE': 'Southeast', 'NW': 'Northwest', 'SW': 'Southwest',
                'N': 'North', 'W': 'West', 'S': 'South', 'E': 'East'}
mapping_way = {'Ave': 'Avenue', 'Rd': 'Road', 'St': 'Street', 'Dr': 'Drive', 'Fwy': 'Freeway'}
mapping_way_inverse = {'Avenue': 'Ave', 'Road': 'Rd', 'Lane': 'Ln'}


# In[8]:

def audit_street(street):
    '''change the street name to the full name if it is overabbreviated'''
    
    street_names = street.split()
    for i,name in enumerate(street_names):
        if name in mapping_direction.keys():
            street_names[i] = mapping_direction[name]
        elif name in mapping_way.keys():
            street_names[i] = mapping_way[name]
    street = ' '.join(street_names)
    return street


# In[9]:

#dump the data when return False
def audit_postcode(postcode):
    
    '''dump the problematic postcodes by regulating the postcode data format to start from "77" and be a 5 digit number'''
    if len(postcode) != 5:
        return ''
    elif postcode[0:2] != '77':
        return ''
    else:   
        return postcode


# In[10]:

def audit_maxspeed(speed):
    
    '''add unit 'mph' to speed if it does not have one'''
    names = speed.split()
    if len(names) == 1 and names[0].isdigit() == True:
        names.append('mph')
        speed = ' '.join(names)
    return speed


# In[11]:

def audit(element):
    
    '''call certain function defined above to audit the tag value'''
    if element.tag == 'way' or element.tag == 'node':
        for tag in element.iter('tag'):
            tag_key = tag.attrib['k']
            tag_value = tag.attrib['v']
            if tag_key == 'maxspeed':
                tag.attrib['v'] = audit_maxspeed(tag_value)
            elif tag_key == 'addr:street':
                tag.attrib['v'] = audit_street(tag_value)
            elif tag_key == 'addr:postcode':
                tag.attrib['v'] = audit_postcode(tag_value)
    return element

