
# OpenStreetMap Data Case Study

## Map Area
Houston, TX, United States
 https://www.openstreetmap.org/node/27526178
 https://mapzen.com/data/metro-extracts/metro/houston_texas/

I choose Houston because it is the closest metropolis I could get, and I also like the NBA team Houston Rockets.

## Problems Encountered in the Map

After initially downloading the map data and checking the elements in a small sample size of the Houston area, I found three main problems, which I will discuss in the following order:
   
    Overabbreviated street names("W Clayton St")
    
    Problematic postal codes("77584-", "773867386")
    
    Ununified maxspeed format("30 mph" vs "30")
    
### Overabbreviated street names

    SELECT tags.value, COUNT(*) as count
    FROM (SELECT * FROM nodes_tags
    UNION ALL
    SELECT * FROM ways_tags) tags
    WHERE tags.key='street'
    GROUP BY tags.value
    ORDER BY count DESC;
    
According to the results of the query, there exists overabbreviated street names like "W Clayton St" and "Business Center Dr". To deal with correcting street names, I opted to creat a mapping dictionary and iterated over each word in a street name.

    mapping_direction = { 'NE': 'Northeast', 'SE': 'Southeast', 'NW': 'Northwest', 'SW': 'Southwest',
                'N': 'North', 'W': 'West', 'S': 'South', 'E': 'East'}
    mapping_way = {'Ave': 'Avenue', 'Rd': 'Road', 'St': 'Street', 'Dr': 'Drive', 'Fwy': 'Freeway'}
    
    def audit_street(street): 
    street_names = street.split()
    for i,name in enumerate(street_names):
        if name in mapping_direction.keys():
            street_names[i] = mapping_direction[name]
        elif name in mapping_way.keys():
            street_names[i] = mapping_way[name]
    street = ' '.join(street_names)
    return street
    

### Problematic postal codes

    SELECT tags.value, COUNT(*) as count
    FROM (SELECT * FROM nodes_tags
    UNION ALL
    SELECT * FROM ways_tags) tags
    WHERE tags.key='postcode'
    GROUP BY tags.value
    ORDER BY count DESC;

Part of the results are as follows:

    77077-9998|1
    77246|1
    773345|1
    77336|1
    773867386|1    
    77584-|1
    77587|1
    77591|1
    77802|1
    77868|1
    88581|1
    TX 77005|1
    TX 77009|1
    TX 77042|1
    TX 77043|1
    TX 77057|1
    TX 77494|1
    Weslayan Street|1
    tx 77042|1

From the query result, most postcodes start from "77", However, there exits a string "Weslayan Street" as a postcode. Also  we got problematic postcodes with leading and trailing characters before and after the main 5 digit zip code. Here I decided to dump the problematic postcodes by regulating the postcode data format to start from "77" and be a 5 digit number.

    #dump the data when return False
    def audit_postcode(postcode):
        if len(postcode) != 5:
            return False
        elif postcode[0:2] != '77':
            return False
        else:
            return True
   

### Ununified maxspeed format

    SELECT ways_tags.value, COUNT(*) as count
    FROM ways_tags
    WHERE ways_tags.key='maxspeed'
    GROUP BY ways_tags.value
    ORDER BY count DESC;

The results are as follows:

    35 mph|40
    65 mph|28
    45 mph|15
    40 mph|14
    60 mph|10
    30 mph|8
    50 mph|6
    15 mph|4
    20 mph|4
    30|2
    40|2
    55 mph|2
    45|1
    
It is obvious that some values have unit but others don't. I decided to add unit 'mph' to those who don't have units.

    def audit_maxspeed(speed):
        names = speed.split()
        if len(names) == 1 and names[0].isdigit() == True:
            names.append('mph')
            speed = ' '.join(names)
        return speed

## Data Overview

This section contains basic statistics about the dataset, the SQL queries used to gather them, and some additional ideas about the data in context.

### File sizes

    houston_texas.osm......661 MB
    houston.db.............381 MB
    nodes.csv..............242 MB
    nodes_tags.csv.........5.78 MB
    ways.csv...............20.8 MB
    ways_tags.csv..........65.1 MB
    ways_nodes.cv..........83 MB
    
    
### Number of nodes

    SELECT COUNT(*) FROM nodes;
    
    3049815
    
    
### Number of ways

    SELECT COUNT(*) FROM ways;
    
    369419
    
    
### Number of unique Users

    SELECT COUNT(DISTINCT(e.uid))
    FROM (SELECT uid FROM nodes UNION ALL SELECT uid FROM ways) e;
    
    1664
    
    
### Top 10 contributing users

    SELECT e.user, COUNT(*) as num
    FROM (SELECT user FROM nodes UNION ALL SELECT user FROM ways) e
    GROUP BY e.user
    ORDER BY num DESC
    LIMIT 10;
    
    woodpeck_fixbot,566376
    TexasNHD,538408
    afdreher,485740
    scottyc,204493
    cammace,192873
    claysmalley,136848
    brianboru,117186
    skquinn,86140
    RoadGeek_MD99,81662
    Memoire,56652
    
We can use the following code to get the total contribution of the top 10 contributing users:   
    
    SELECT sum(top10users.num) as sum
    FROM
    (SELECT e.user, COUNT(*) as num
    FROM (SELECT user FROM nodes UNION ALL SELECT user FROM ways) e
    GROUP BY e.user
    ORDER BY num DESC
    LIMIT 10) top10users;
    
    2466378

Then use the following code to get the total contribution by all users:

    SELECT count(e.user) as sum
    FROM
    (SELECT user FROM nodes UNION ALL SELECT user FROM ways) e;
    
    3419234
    
Therefore, the top 10 contributing users provide 2466378/3419234 = 72.13% of the whole data.


### Number of users appearing only once (having 1 post)

    SELECT COUNT(*) 
    FROM
        (SELECT e.user, COUNT(*) as num
         FROM (SELECT user FROM nodes UNION ALL SELECT user FROM ways) e
         GROUP BY e.user
         HAVING num=1)  u;
         
    362
    
    
### Top 10 sources

    SELECT e.value, COUNT(*) as num
    FROM (SELECT key,value FROM nodes_tags UNION ALL SELECT key,value FROM ways_tags) e
    WHERE e.key = 'source'
    GROUP BY e.value
    ORDER BY num DESC
    LIMIT 10;
    
    tiger_import_dch_v0.6_20070830|50270
    tiger_import_dch_v0.6_20070829|23279
    Bing|6269
    2011|987
    USGS Geonames|877
    Yahoo|589
    bing|300
    2010|295
    Mapbox|282
    PGS|221
    
    It seems that lots of data are from tiger GPS.

## Additional Data Exploration

### Top 10 appearing amenities

    SELECT value, COUNT(*) as num
    FROM nodes_tags
    WHERE key='amenity'
    GROUP BY value
    ORDER BY num DESC
    LIMIT 10;
    
    place_of_worship,2222
    school,824
    fountain,712
    restaurant,703
    fast_food,632
    fire_station,351
    fuel,279
    pharmacy,176
    bank,173
    police,161
    
I didn't know Houston has so many fountains. Maybe Houston is more beautiful than I thought.
    
    
### Biggest religion

    SELECT nodes_tags.value, COUNT(*) as num
    FROM nodes_tags 
        JOIN (SELECT DISTINCT(id) FROM nodes_tags WHERE value='place_of_worship') i
        ON nodes_tags.id=i.id
    WHERE nodes_tags.key='religion'
    GROUP BY nodes_tags.value
    ORDER BY num DESC
    
    christian|2154
    buddhist|16
    jewish|12
    muslim|9
    unitarian_universalist|5
    
According to wikipeida, 70.6% of adults identified themselves as Christian in the United States.
    
### Most popular cuisines

    SELECT value, COUNT(*) as num
    FROM nodes_tags
    WHERE key = 'cuisine'
    GROUP BY value
    ORDER BY num DESC
    LIMIT 10;
    
    burger|194
    sandwich|121
    mexican|113
    pizza|70
    chicken|60
    american|48
    coffee_shop|45
    italian|34
    chinese|33
    seafood|22
    
No surprise that most are american restaurants. Also there are a lot of mexican restaurants, which makes sense because Texas is close to Mexican. Well it seems like I got a lot of choices. May drive to Houston to eat some good stuff after finishing this project. 

## Suggestions

### Key value for postal codes

I happened to find that there are two different key values for postal codes. To see that, we can do a query again using "WHERE tags.key='postal_code'" instead of  "WHERE tags.key='postcode'".

The results are as follows:

    77396|65
    77060|58
    77079|57
    77032|47
    77338|42
    77090|36
    77401|34
    77346|31
    77093|18
    77067|12
    77377|11
    77520|11
    77070|10
    77050|6
    77583|6
    77047|4
    77578|4
    77096|3
    77086|2
    77375|2
    77028|1
    77043|1
    77095|1
    77385|1
    77530|1
    77536|1

There are some postcodes with key value "postal_code". It is surely not a problem as big as wrong postcode values. But my opinion is that to keep consistent, we'd better convert all the "postal_code" to "postcode".

    def audit_postal_code(key_value):
        if key_value == 'postal_code':
            key_value = 'postcode'
        return key_value
        
### Name tags
After exploring the key values of the tags, I noticed that there are many kinds of name tags. For example, 'name',
'name_base' and 'name_direction_prefix'. So I searched osm document on wiki and according to wiki, there are actually 5 types of names:
![image.png](attachment:image.png)

These data come from TIGER GPS and TIGER names are split across four fields: name_direction_prefix, name_base, name_type, name_direction_suffix.
Refer to the imformation above, a cross-validation could be built among the four fields, since 'name' is supposed to contain the information that other name-related tags offer. If not, then the name-related tags are problematic.

    SELECT key, value FROM ways_tags WHERE id = 53124031
    AND (key = 'name' or key = 'name_base' or key = 'name_type' or key = 'name_direction_prefix' or key = 'name_direction_suffix');
    
    name|East Loop North
    name_base|I-610:Loop; I-610
    name_type|Fwy
    name_direction_prefix|E
    name|East Loop North
    name_base|I-610:Loop; I-610
    name_type|Fwy
    name_direction_prefix|E

The example above is a problematic one. The name_type should be 'Loop' instead of 'Fwy' and the name_base should be none. It is hard to explain why these information contradicts with each other. Since OSM documents use 'fixme' tags to store the information that is temporarily uncertain, a possible solution is to dump the problematic data and create new 'fixme' tags.

Benefit: 1. After dumping the problematic data the name tags will be consistant. 2. By using 'fixme' tags other users may help improve the names in the future.

Anticipated Issues: 1. The problematic name-related tags may contain useful information and if we just dump these tags we could lose those important information. 2. It is possible that the name tag is problematic, not its related tags and thus we need a check function to see which we need to dump. This may require a very complex cross-validation algorithm to tell us which is more likely the problematic one.

## Conclusion

In general, the openstreetmap of Houston is clean after auditing the data following the steps mentioned in this report. By importing the data into sqlite and querying the results, I got information about basic statistics about the dataset like number of nodes and top 10 contributing users. I also did some interesting research like top 10 appearing amenities and most popular cuisines. After exploring the data, I also found a problem about the name-related tags, which may need further attention as we discussed.
