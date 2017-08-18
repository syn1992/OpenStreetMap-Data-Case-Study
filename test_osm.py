
# coding: utf-8

# In[20]:

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema

from audit import audit


# In[21]:

OSM_PATH = "sample2.osm"

NODES_PATH = "nodes_sample.csv"
NODE_TAGS_PATH = "nodes_tags_sample.csv"
WAYS_PATH = "ways_sample.csv"
WAY_NODES_PATH = "ways_nodes_sample.csv"
WAY_TAGS_PATH = "ways_tags_sample.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema


# In[22]:

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


# In[23]:

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    #First call the audit function to update the xml data
    element = audit(element)
    
    if element.tag == 'node':
    	for key in node_attr_fields:
    		node_attribs[key] = element.attrib[key]
    	
    	for tag in element.iter('tag'):
    		tag_temp = {}
    		tag_key = tag.attrib['k']
    		tag_value = tag.attrib['v']
    		tag_temp['id'] = element.attrib['id']
    		tag_temp['key'] = tag.attrib['k']
    		tag_temp['value'] = tag.attrib['v']

    		if problem_chars.search(tag_key) != None:
    			continue    		
    		elif LOWER_COLON.search(tag_key) != None:
    			type_no = tag_key.index(':')
    			type_temp = tag_key[0:type_no]
    			tag_temp['type'] = type_temp
    			tag_temp['key'] = tag_key[type_no+1:len(tag_key)]

    		else:
    			tag_temp['type'] = default_tag_type
  
    		tags.append(tag_temp)
  		#print {'node': node_attribs, 'node_tags': tags}
        return {'node': node_attribs, 'node_tags': tags}
   
    elif element.tag == 'way':
    	
    	for way_key in way_attr_fields:
    		way_attribs[way_key] = element.attrib[way_key]
    	for way_tag in element.iter('tag'):
    		tag_temp = {}
    		tag_key = way_tag.attrib['k']
    		tag_value = way_tag.attrib['v']
    		tag_temp['id'] = element.attrib['id']
    		tag_temp['key'] = way_tag.attrib['k']
    		tag_temp['value'] = way_tag.attrib['v']

    		if LOWER_COLON.search(tag_key) != None:
    			type_no = tag_key.index(':')
    			type_temp = tag_key[0:type_no]
    			tag_temp['type'] = type_temp
    			tag_temp['key'] = tag_key[type_no+1:len(tag_key)]
    		elif problem_chars.search(tag_key) != None:
    			continue
    		else:
    			tag_temp['type'] = default_tag_type
  
    		tags.append(tag_temp)

    	way_node_no = 0
    	for way_node in element.iter('nd'):
    		way_node_temp = {}
    		way_node_temp['id'] = element.attrib['id']
    		way_node_temp['node_id'] = way_node.attrib['ref']
    		way_node_temp['position'] = way_node_no
    		way_node_no+=1
    		way_nodes.append(way_node_temp)

 		#print {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# In[24]:

# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# In[25]:

# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'wb') as nodes_file,          codecs.open(NODE_TAGS_PATH, 'wb') as nodes_tags_file,          codecs.open(WAYS_PATH, 'wb') as ways_file,          codecs.open(WAY_NODES_PATH, 'wb') as way_nodes_file,          codecs.open(WAY_TAGS_PATH, 'wb') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        #nodes_writer.writeheader()
        #node_tags_writer.writeheader()
        #ways_writer.writeheader()
        #way_nodes_writer.writeheader()
        #way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
          
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=False)


# In[ ]:



