#Combined with the use of arguements 

import config 

#PART 1: HDF FILE TO TIF IMAGE



sourcefilefolder = args.sourcefolder
#source is folder with hdf files 
tiffolder = args.tiffolder

os.makedirs(str(tiffolder))

directory = 'r'+str(sourcefilefolder)
for filename in os.listdir(directory):
    if filename.endswith(".hdf"):
        #print(filename)
        #year = filename.split('.')[1].split('A')[1][0:4]
        #RANGEENDINGDATE=2001 <- get the date from inside the file
        # this is specific to the format of the NASA data files I used for this project - other HDF files may not have the year in this location 
        #print(year)

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
                    date = line 
                    year = date.split('=')[1].split('-')[0]
                if 'SUBDATASET_1_NAME' in line:
                    subdataset = line.split('=')[1]

        print(subdataset)
        #in lines 35 to 38 I am looking for a specific item I know is in my HDF file - other HDF files may have different subdatasets (or none at all)

        #cmd2 = 'gdal_translate '+str(subdataset)+' '+'Years/'+str(year)+'/'+ str(year)+'landclass.tif'
        cmd2 = 'gdal_translate '+str(subdataset)+ ' ' +str(tiffolder)+'/' + str(year)+'_'+str(tiffolder)+'.tif'


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
from osgeo import gdal, osr
import os       
import pymysql
import subprocess
from PIL import Image
import json


src = gdal.Open(str(tiffolder)+'/'+'2001_MCD12C1.tif')
#in this case, all my files are for the same area (so the raster size and pixels will be consistent - if they are not, this step needs to be included in the loop on line 131
X = src.RasterXSize 
Y = src.RasterYSize
print(X, Y)

P1=0
L1=0
P2=X
L2=Y
#or manually choose your bounding pixels


def WriteToDatabase():   
    
    conn = pymysql.connect(host=config.c['host'], port=3306, user=config.c['user'],
                           passwd=config.c['passwd'], database=config.c['database'], autocommit=True)
    #how to deal with this for the GitHub repo? 
    
    f = open('tokens.txt','r')
    for line in f:

        tokens = json.loads(line)

        sql ='''INSERT INTO `carterle_RasterToRelational`.`GitHubTest`
                (`geo_location`, `pixel_location`, `land_class`, `sample_id`)
                VALUES 
                (%s,%s, %s, %s);'''


        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.executemany(sql,tokens)
        conn.commit()
        cur.close()  
        
        f = open('tokens.txt','w')
        f.write('')
        f.close()
        

f = open('tokens.txt','w')
f.write('')
f.close()
f = open('tokens.txt','a')


directory = r'MCD12C1'
blocksize = 10000
#tokens = []

directory = 'r'+str(tiffolder)
for filename in os.listdir(directory):
    tokens = []
    n=0
    if filename.endswith(".tif"):
        #load file with pil 
        
        print(os.path.join(directory, filename))
        print(type(filename))
        sample = filename.split('_')[0]

        ds = gdal.Open(str(tiffolder)+'/'+filename) 
        xoffset, px_w, rot1, yoffset, px_h, rot2 = ds.GetGeoTransform()
             
        #load file with pil 
        im = Image.open(str(tiffolder)+'/'+filename)
        allpix = im.load()
        
        for pixels in pixellist:

            P = int(pixels.split(' ')[0])
            L = int(pixels.split(' ')[1])

            pixel = 'Point(' + str(P) + ' ' + str(L) + ')'

            # supposing x and y are your pixel coordinates, this is how to get the coordinates in space.
            posX = px_w * P + rot1 * L + xoffset
            posY = rot2 * L + px_h * P + yoffset

            # shift to the center of the pixel
            posX += px_w / 2.0
            posY += px_h / 2.0

            latlon = 'POINT(' + str(posX) + ' ' + str(posY) + ')'
            #see if here it is possible to convert to bites using python 
          
            landclass = allpix[int(P),int(L)]
            #print(landclass)
            
            tokens.append((latlon,pixel,landclass,sample))

            if len(tokens) >= blocksize:
                f.write(json.dumps(tokens)+'\n')
                n+=1
                print('\t',n)
                tokens = []
                WriteToDatabase()
                
if len(tokens) >= 0:
    f.write(json.dumps(tokens)+'\n')
    WriteToDatabase()            

