#Query land class data from a region based on a shapefile or four points

#Import libraries
import config 
from pathlib import Path
import os       
import pymysql
import shapefile
import json
import argparse
from geomet import wkt


#Use the argparse library to allow users to define variables in the command line
parser = argparse.ArgumentParser(description='Here the user must define the boundary file, whether you wish to reduce the boundary (which may be helpfull for very large shapefiles), and the years for which you wish to query data')
parser.add_argument('boundaryfile', type=str,help='The name of the boundary file')
parser.add_argument('tablename', type=str, help='What is your SQL tablename')
parser.add_argument('-reduceboundary', type=int, default = 1 ,help='Specifying reduce boundary means you wish to reduce the number of lon/lat points which make up the boundary, by a factor which you specify. The default is 1, which will keep all points. Specifying 2 would cut the number of boundary points in half, and so on.')
parser.add_argument('argyears', metavar='N', type=int, nargs='+', help='Specify all years for which you would like the data')

args = parser.parse_args()

argyearlist = args.argyears
#print(argyearlist)

tablename = args.tablename
boundaryfile = args.boundaryfile
reduction = args.reduceboundary
#print(reduction)

#If the boundary file contains a lot of points, a user can specify -reduceboundary to reduce the number of points which make up the boundary 
with open(boundaryfile) as f:
  data = json.load(f)

#Set up a new dictionary with coordinates being a list of lists, where the lon lat points will be the list and those will be combined in the coordinates list 
newMap = {"type":"Polygon","coordinates":[[]]}

#Itterate over the old list and append every *whatever number the user specified* point to the coordinates list in newMap
n = 0
for point in data['features'][0]['geometry']['coordinates'][0][0]:
    if n == 0:
        firstpoint = point
    if n % reduction == 0:
        newMap['coordinates'][0].append(point)
    n+=1 
newMap['coordinates'][0].append(firstpoint)

#Use json.dump to create a json file from nweMap
with open('wktboundaryfile.json', 'w') as json_file:
    json.dump(newMap, json_file)

#Open the json file set polygon as well know text (WKT) of the json structure of newMap - newMap is set up to work with the phpMyAdmin function of searching within a boundary of geom points 
with open('wktboundaryfile.json') as f:
    polygon = json.load(f)

polygon = wkt.dumps(polygon, decimals=4)
#print(polygon)


conn = pymysql.connect(host=config.sample.c['host'], port=3306, user=config.sample.c['user'],
                       passwd=config.sample.c['passwd'], database=config.sample.c['database'], autocommit=True)

yearlist = []
coordslist = []

n = 0
for year in argyearlist:
    
    #SQL is converting polgon to the Geom type in phpMyAdmin which allows you to search for the points (from the goe_points column) contained within that polygon 
    
    sql = '''SELECT geo_location, sample_id, land_class FROM `'''+tablename+'''`
    WHERE ST_CONTAINS(GeomFromText(%s), geo_point) 
    AND sample_id = %s'''
    
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute(sql,(polygon, year))
    conn.commit()
    cur.close()  
    
    #The following code takes the output (stored as cur) and stores it in json format 
    landclassdict = {}
    
    totalcount = 0
    for line in cur:
        linedict = dict(line)
        
        if n == 0:
            lon = linedict['geo_location'].split('POINT')[1].split(' ')[0]
            lat = linedict['geo_location'].split('POINT')[1].split(' ')[1]
            coords = [lon+','+lat]
            coordslist.append(coords)       
        
        classkey = linedict['land_class']
        
        if classkey in landclassdict.keys():
            landclassdict[classkey]+=1
            totalcount+=1
        else:
            landclassdict[classkey]=1
            totalcount+=1
            
    classeslist = []    
    
    for key, value in landclassdict.items():
        classdict = {}
        classdict['Class'] = int(key)
        classdict['Percent'] = int(value)/int(totalcount)
        classdict['Count'] = int(value)
        classeslist.append(classdict)
    

    yearinfodict = {}
    yearinfodict['year'] = year
    yearinfodict['classes'] = classeslist
    
    yearlist.append(yearinfodict)
    
    n+=1


#collect information about the polygon for output - I could get a lot more in depth with this, but for now I do not really need to for my purposes 
polydict = {}
#polydict['wkt format'] = 'wkt format'
#polydict['geoformat'] = 'geoformat'
polydict['coordinates list'] = coordslist  

 
alldict = {}
alldict['yearlist'] = yearlist
alldict['polygon'] = polydict

#Taking the output stored in my json configuration and using json.dump to save to a json file 
with open('Query_Results.json', 'w') as json_file:
    json.dump(alldict, json_file)
#print(json.dumps(alldict))

