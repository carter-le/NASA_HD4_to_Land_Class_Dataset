#Combined with the use of arguements 

import config 
from pathlib import Path
import os
import shutil
import argparse
import subprocess

#PART 1: HDF FILE TO TIF IMAGE

parser = argparse.ArgumentParser(description='Specify the name of the folder with the source files, the prefix of the SQL table you are creating, and whether you would like to clear that table before running the new code')
parser.add_argument('sourcefolder', type=str,help='The name of the directory in which your source files are located.')
parser.add_argument('tableprefix', type=str, help='What would you like to call the prefix of the SQL tablename')
parser.add_argument('-cleardata', type=str, help='Specifying cleardata means you wish to empty the SQL table before populating data - choosing not to include clear data will result in data appending to the table')
args = parser.parse_args()


sourcefilefolder = args.sourcefolder
#sourcefilefolder is folder with hdf files 

#Create partitioned folders - overwrite they just specify the same prefix 
mypath = os.path.join('Data', str(args.tableprefix))
tifpath = os.path.join(mypath, 'tiffolder')
tokenpath = os.path.join(mypath, 'tokens')

if os.path.isdir(mypath):
    shutil.rmtree(mypath)
    
if os.path.isdir(tifpath):
    shutil.rmtree(tifpath)
    
if os.path.isdir(tokenpath):
    shutil.rmtree(mypath)

Path(mypath).mkdir(parents=True, exist_ok=True)
Path(tifpath).mkdir(parents=True, exist_ok=True)
Path(tokenpath).mkdir(parents=True, exist_ok=True)


n=0
for filename in os.listdir(sourcefilefolder):
    if filename.endswith(".hdf"):
        n+=1
        cmd = 'gdalinfo ' +str(sourcefilefolder)+'/'+str(filename)

        # Use shell to execute the command
        sp = subprocess.Popen(cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True)

        # Separate the output and error.
        # This is similar to Tuple where we store two values to two different variables
        out,err=sp.communicate()

        rc=sp.wait()
        print(rc)

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
        
        cmd2 = 'gdal_translate '+str(subdataset)+ ' ' +tifpath +'/'+ str(n)+'_'+str(fileyear)+'.tif'


        # Use shell to execute the command
        sp2 = subprocess.Popen(cmd2,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True)

        # Separate the output and error.
        # This is similar to Tuple where we store two values to two different variables
        out,err=sp2.communicate()

        rc2=sp2.wait()
        print(rc2)

    else:
        continue




#PART 2: TIF IMAGE TO DATA 


import osgeo
import gdal
from osgeo import osr
import os       
import pymysql
import subprocess
from PIL import Image
import json



def WriteToDatabase():   
    
    conn = pymysql.connect(host=config.sample.c['host'], port=3306, user=config.sample.c['user'],
                           passwd=config.sample.c['passwd'], database=config.sample.c['database'], autocommit=True)
                             
    
    #if you want to use this on multiple HDF file sets you can use a different prefix for all of them 
    #ex if you have a HDF file for South America and one for Africa you can give those differend prefixes 
    tablename = args.tableprefix+'Points'
    
    if args.cleardata is not None: 
        sql = '''drop table if exists `%s`'''
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(sql, tablename)
        conn.commit()
        cur.close()  
        
        sql2 = '''create table `%s` (ID int NOT NULL AUTO_INCREMENT PRIMARY KEY, geo_location varchar(50), pixel_location varchar(50), land_class int(2), sample_id int(4), geo_point POINT, pixel_point POINT);'''
                
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(sql2,tablename)
        conn.commit()
        cur.close()          
        
    f = open(tokenpath+'/tokens.txt','r')
    for line in f:

        tokens = json.loads(line)

        sql ='''INSERT INTO `'''+tablename+'''`
                (`geo_location`, `pixel_location`, `land_class`, `sample_id`)
                VALUES 
                (%s,%s, %s, %s);'''

        #sql ='''INSERT INTO `%s`
        #        (`geo_location`, `pixel_location`, `land_class`, `sample_id`)
        #       VALUES 
        #        (%s,%s, %s, %s);'''

#the prob is that execute many is executing all the tokens (there are many) but there is only one tablename 
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.executemany(sql, tokens)
        conn.commit()
        cur.close()  
        
        f = open('tokens.txt','w')
        f.write('')
        f.close()
        

f = open(tokenpath+'/tokens.txt','w')
f.write('')
f.close()
f = open(tokenpath+'/tokens.txt','a')


blocksize = 10000


for filename in os.listdir(tifpath):
    tokens = []
    pixellist = []
    n=0
    if filename.endswith(".tif"):
    
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
        #it is going to slow the process down doing htis for each file! but not that much and it is worth it because the risk of files with different sizes is high 
        #or manually choose your bounding pixels
        
        print(os.path.join(tifpath, filename))
        print(type(filename))
        sample = filename.split('_')[1]

        ds = gdal.Open(tifpath+'/'+filename) 
        xoffset, px_w, rot1, yoffset, px_h, rot2 = ds.GetGeoTransform()
             
        #load file with pil 
        im = Image.open(tifpath+'/'+filename)
        allpix = im.load()
        
        for pixels in pixellist:

            P = int(pixels.split(' ')[0])
            L = int(pixels.split(' ')[1])

            pixel = 'POINT(' + str(P) + ' ' + str(L) + ')'

            # supposing x and y are your pixel coordinates, this is how to get the coordinates in space.
            posX = px_w * P + rot1 * L + xoffset
            posY = rot2 * L + px_h * P + yoffset

            # shift to the center of the pixel
            posX += px_w / 2.0
            posY += px_h / 2.0

            lonlat = 'POINT(' + str(posX) + ' ' + str(posY) + ')'
            #it would be more accurate to say lonlat here 
            #see if here it is possible to convert to bites using python 
            
            try:
                landclass = allpix[int(P),int(L)] 
            except Exception as e:
                print("Pixel Error", P, L)
                print(e)
                exit()
            #print(landclass)
            
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


sql =''' UPDATE `%s` SET geo_point = ST_GeomFromText(testtable.geo_location), pixel_point = ST_GeomFromText(testtable.pixel_location);'''


cur = conn.cursor(pymysql.cursors.DictCursor)
cur.execute(sql, tablename)
conn.commit()
cur.close()  


#Update the SQL database to convert the columns in php to the Point type 
