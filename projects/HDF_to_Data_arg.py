#Import libraries

import config 
from pathlib import Path
import os
import shutil
import argparse
import subprocess

#PART 1: HDF FILE TO TIF IMAGE

#First I add parser arguements - user arguements which are passed in the command line
parser = argparse.ArgumentParser(description='Specify the name of the folder with the source files, the prefix of the SQL table you are creating, and whether you would like to clear that table before running the new code')
parser.add_argument('sourcefolder', type=str,help='The name of the directory in which your source files are located.')
parser.add_argument('tableprefix', type=str, help='What would you like to call the prefix of the SQL tablename')
parser.add_argument('-cleardata', type=str, help='Specifying cleardata means you wish to empty the SQL table before populating data - choosing not to include clear data will result in data appending to the table')
args = parser.parse_args()


sourcefilefolder = args.sourcefolder
#sourcefilefolder is the folder with hdf files 

#Specify partitioned folders and folder paths
mypath = os.path.join('Data', str(args.tableprefix))
tifpath = os.path.join(mypath, 'tiffolder')
tokenpath = os.path.join(mypath, 'tokens')

#Create the partitioned folders 
if os.path.isdir(mypath):
    shutil.rmtree(mypath)
    
if os.path.isdir(tifpath):
    shutil.rmtree(tifpath)
    
if os.path.isdir(tokenpath):
    shutil.rmtree(mypath)

Path(mypath).mkdir(parents=True, exist_ok=True)
Path(tifpath).mkdir(parents=True, exist_ok=True)
Path(tokenpath).mkdir(parents=True, exist_ok=True)

#At this point I itterage through each of the source files in the sourefile folder 
n=0
for filename in os.listdir(sourcefilefolder):
    if filename.endswith(".hdf"):
        n+=1
        #cmd is the command I want to execute in the command line
        cmd = 'gdalinfo ' +str(sourcefilefolder)+'/'+str(filename)

        #Use shell via subprocess module to execute the command
        sp = subprocess.Popen(cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True)

        # Separate the output and error.
        # This is similar to Tuple where we store two values to two different variables
        out,err=sp.communicate()

        rc=sp.wait()
        #print(rc)

        if rc == 0:
            for line in out.splitlines():
            #RANGEENDINGDATE=2001 <- get the date from inside the file
                if 'RANGEENDINGDATE' in line:
                    filedate = line 
                    fileyear = filedate.split('=')[1].split('-')[0]
                if 'SUBDATASET_1_NAME' in line:
                    subdataset = line.split('=')[1]

        print(subdataset)
        #in this case I am looking for a specific item I know is in my HDF file - other HDF files may have different subdatasets (or none at all)
        
        #The next command line call will be using the subdataset I got from executing the first command line call
        #This command will create a tif file from the subdataset HD4 file and file it in my tiffolder 
        cmd2 = 'gdal_translate '+str(subdataset)+ ' ' +tifpath +'/'+ str(n)+'_'+str(fileyear)+'.tif'


        # Use shell to execute the command
        sp2 = subprocess.Popen(cmd2,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True)

        # Separate the output and error again
        out,err=sp2.communicate()
        
        # In this case I did not need to capture the output - I just needed the tif file to be created 
        rc2=sp2.wait()
        #print(rc2)

    else:
        continue




#PART 2: TIF IMAGE TO DATA 

#import additional libraries
import osgeo
import gdal
from osgeo import osr
import os       
import pymysql
import subprocess
from PIL import Image
import json


#this definition will create a connection to a phpMyAdmin SQL database, delete the table if it exists and if the user does not want to append the data, create the table, and insert the data generated from the main code into the database, using tokens to increase speed and help prevent a bottle-neck at this step

def WriteToDatabase():   
    
    #conn = pymysql.connect(host=config.sample.c['host'], port=3306, user=config.sample.c['user'],
     #                     passwd=config.sample.c['passwd'], database=config.sample.c['database'], autocommit=True)
    
    conn = pymysql.connect(host=config.c['host'], port=3306, user=config.c['user'],
                           passwd=config.c['passwd'], database=config.c['database'], autocommit=True)    
    
    #if you want to use this on multiple HDF file sets you can use a different prefix for all of them 
    #ex if you have a HDF file for South America and one for Africa you can give those differend prefixes 
    tablename = args.tableprefix+'Points'
    
    #based on optional user-specified parameter -cleardata
    if args.cleardata is not None: 
        #drop the table if the user has said to do so
        sql = '''drop table if exists `'''+tablename+'''` '''
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(sql)
        conn.commit()
        cur.close()  
        
        #create the SQL table using the user-specified table prefix 
        sql2 = '''create table `'''+tablename+'''` (ID int NOT NULL AUTO_INCREMENT PRIMARY KEY, geo_location varchar(50), pixel_location varchar(50), land_class int(2), sample_id int(4), geo_point POINT, pixel_point POINT);'''
                
        #execute the SQL statement        
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(sql2)
        conn.commit()
        cur.close()          
        
    f = open(tokenpath+'/tokens.txt','r')
    for line in f:

        tokens = json.loads(line)

        sql ='''INSERT INTO `'''+config.c['database']+'''`.`'''+tablename+'''`
                (`geo_location`, `pixel_location`, `land_class`, `sample_id`)
                VALUES 
                (%s,%s, %s, %s);'''



        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.executemany(sql, tokens)
        conn.commit()
        cur.close()  
        
        f = open('tokens.txt','w')
        f.write('')
        f.close()
        

#I create the text file tokenpath - it is an intermediate step to dump the data into a text file and read the data from that text file when the WriteToDatabsae() definition is called
f = open(tokenpath+'/tokens.txt','w')
f.write('')
f.close()
f = open(tokenpath+'/tokens.txt','a')


blocksize = 10000

#I itterate through all of the tif files in the tiffolder
for filename in os.listdir(tifpath):
    tokens = []
    pixellist = []
    n=0
    if filename.endswith(".tif"):
        #I find the file size of each tif file to use that to create a list (called pixellist) of all of the pixels in that tif image
        src = gdal.Open(tifpath+'/'+str(filename))
        X = src.RasterXSize 
        Y = src.RasterYSize
        #print(X, Y)

        P1=0
        L1=0
        P2=X
        L2=Y
        
        p = P1
        while p < P2:
            l = L2 - 1
            
            while l > L1:
            #while l > L1:
                pixellist.append(str(p)+' '+str(l))
                l -= 1
            p += 1 
        #print(pixellist[1:10])        
        #it is going to slow the process down doing this for each file! but not that much and it is worth it because the risk of files with different sizes is relatively high 
        #or manually choose your bounding pixels
        
        #Now I have the list of pixels I will need to gather land class and lat/lon data for 
        #I take the tif file and I load it into memory, this time using pil (this way I can extract the needed data from each pixel without loading the tif image into memory for every pixel) 
        print(os.path.join(tifpath, filename))
        print(type(filename))
        sample = filename.split('_')[1]

        #I use the gdal module functionality to gather the geometric features from the tif file
        ds = gdal.Open(tifpath+'/'+filename) 
        xoffset, px_w, rot1, yoffset, px_h, rot2 = ds.GetGeoTransform()
             
        #load file with pil 
        im = Image.open(tifpath+'/'+filename)
        allpix = im.load()
        
        for pixels in pixellist:

            P = int(pixels.split(' ')[0])
            L = int(pixels.split(' ')[1])

            pixel = 'POINT(' + str(P) + ' ' + str(L) + ')'

            # supposing P and L are your pixel coordinates, this is how to get the X and Y coordinates in space.
            posX = px_w * P + rot1 * L + xoffset
            posY = rot2 * L + px_h * P + yoffset

            # shift to the center of the pixel
            posX += px_w / 2.0
            posY += px_h / 2.0

            lonlat = 'POINT(' + str(posX) + ' ' + str(posY) + ')'
            #it would be more accurate to say lonlat here 
            #see if here it is possible to convert to bites using python 
            
            try:
                #here I am looking at the image I loaded with pil, saved once in memory as allpix
                landclass = allpix[int(P),int(L)] 
            #There should not be any errors because I use each file to gather the pixel list - but I use try/except to cover my bases
            except Exception as e:
                print("Pixel Error", P, L)
                print(e)
                exit()
            #print(landclass)
            
            #I then append the list of gather attributes into my tokens text file 
            tokens.append((lonlat,pixel,landclass,sample))
            
            
            if len(tokens) >= blocksize:
                f.write(json.dumps(tokens)+'\n')
                n+=1
                print('\t',n)
                tokens = []
                WriteToDatabase()
                
if len(tokens) >= 0:
    f.write(json.dumps(tokens)+'\n')
    WriteToDatabase()            

#I then update the table in sql to populate the two columns the same as geo_location and pixel_location but as Point type (which I use to query the data) 
sql =''' UPDATE `'''+tablename+'''` SET geo_point = ST_GeomFromText(testtable.geo_location), pixel_point = ST_GeomFromText(testtable.pixel_location);'''


cur = conn.cursor(pymysql.cursors.DictCursor)
cur.execute(sql)
conn.commit()
cur.close()  


#Update the SQL database to convert the columns in php to the Point type 
