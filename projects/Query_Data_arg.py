#Query land class data from a region based on a shapefile or four points


import config 
from pathlib import Path
import os       
import pymysql
import shapefile
import json
import argparse
from geomet import wkt



parser = argparse.ArgumentParser(description='Here the user must define the boundary file, whether you wish to reduce the boundary (which may be helpfull for very large shapefiles), and the years for which you wish to query data')

parser.add_argument('boundaryfile', type=str,help='The name of the boundary file')

#parser.add_argument('tablename', help='The name of the phpMyAdmin table you want to query')
#I tried this but you cannot have user inputs for a tablename without exposing yourself to python injection risks - it will have to be hard-coded until an alt solution is found

parser.add_argument('-reduceboundary', type=int, default = 1 ,help='Specifying reduce boundary means you wish to reduce the number of lon/lat points which make up the boundary, by a factor which you specify. The default is 1, which will keep all points. Specifying 2 would cut the number of boundary points in half, and so on.')

parser.add_argument('argyears', metavar='N', type=int, nargs='+', help='Specify all years for which you would like the data')

args = parser.parse_args()

argyearlist = args.argyears
#print(argyearlist)

boundaryfile = args.boundaryfile
reduction = args.reduceboundary
#print(reduction)

with open(boundaryfile) as f:
  data = json.load(f)

newMap = {"type":"Polygon","coordinates":[[]]}

n = 0
for point in data['features'][0]['geometry']['coordinates'][0][0]:
    if n == 0:
        firstpoint = point
    if n % reduction == 0:
        newMap['coordinates'][0].append(point)
    n+=1 
newMap['coordinates'][0].append(firstpoint)

with open('wktboundaryfile.json', 'w') as json_file:
    json.dump(newMap, json_file)


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
    
    sql = '''SELECT geo_location, sample_id, land_class FROM `points2`
    WHERE ST_CONTAINS(GeomFromText(%s), geo_point) 
    AND sample_id = %s'''
    
    
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute(sql,(polygon, year))
    conn.commit()
    cur.close()  
    
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


#collect information about the polygon for output:
polydict = {}
#polydict['wkt format'] = 'wkt format'
#polydict['geoformat'] = 'geoformat'
polydict['coordinates list'] = coordslist  

 
alldict = {}
alldict['yearlist'] = yearlist
alldict['polygon'] = polydict

with open('Query_Results.json', 'w') as json_file:
    json.dump(alldict, json_file)
#print(json.dumps(alldict))

