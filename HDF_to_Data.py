#Combined


#PART 1: HDF FILE TO TIF IMAGE
#sourcefolder = 
#newfolder = 
#make this a one input 

os.makedirs("MCD12C1")

directory = r'hdf_sourcefiles_MCD12Q1'
for filename in os.listdir(directory):
    if filename.endswith(".hdf"):
        #print(os.path.join(directory, filename))
        print(filename)
        year = filename.split('.')[1].split('A')[1][0:4]
        print(year)
            #os.makedirs("Years/"+str(year))

        cmd = 'gdalinfo hdf_sourcefiles_MCD12Q1/'+str(filename)

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
                if 'SUBDATASET_1_NAME' in line:
                    subdataset = line.split('=')[1]

        print(subdataset)


        #cmd2 = 'gdal_translate '+str(subdataset)+' '+'Years/'+str(year)+'/'+ str(year)+'landclass.tif'
        cmd2 = 'gdal_translate '+str(subdataset)+' MCD12C1/' +str(year)+'_MCD12C1.tif'


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
             
        #load file with pil 
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


