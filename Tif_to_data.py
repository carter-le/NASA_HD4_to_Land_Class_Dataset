#Take the .tif files you created and gather the data 

import osgeo
from osgeo import gdal, osr
import os       
import pymysql
import subprocess
from PIL import Image
import json

src = gdal.Open('MCD12C1/2001_MCD12C1.tif')
X = src.RasterXSize 
Y = src.RasterYSize
print(X, Y)

P1=0
L1=0
P2=X
L2=Y

#or manually choose your bounding pixels


def WriteToDatabase():   
    
    conn = pymysql.connect(host='mysql.clarksonmsda.org', port=3306, user='carterle',
                           passwd='lec123.php', db='carterle_RasterToRelational', autocommit=True)

    f = open('tokens.txt','r')
    for line in f:

        tokens = json.loads(line)

        sql ='''INSERT INTO `carterle_RasterToRelational`.`points2`
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

directory = r'MCD12C1'
for filename in os.listdir(directory):
    tokens = []
    n=0
    if filename.endswith(".tif"):
        #load file with pil 
        
        print(os.path.join(directory, filename))
        print(type(filename))
        sample = filename.split('_')[0]

        ds = gdal.Open('MCD12C1/'+filename) 
        xoffset, px_w, rot1, yoffset, px_h, rot2 = ds.GetGeoTransform()
      
        im = Image.open('MCD12C1/'+filename)
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
