# Creating a Database with Land-Class Information from NASA HDF Files
## Introduction / Will This Project Fit Your Needs?

This project was created out of need for a product I could not readily find - a dataset of the land classification of specific geographic regions over specific periods of time. What I did find in NASA's database was a collection of HDF files with land class data, which can be found at the on EARTHDATA's project information page for their product, MCD12C1 v006. The web address is: https://lpdaac.usgs.gov/products/mcd12c1v006/. The product guide specifically states that *"the data product should not be used to determine post-classification land cover change between years due to the uncertainty in the land cover labels for any one year."* I personally use the product for land class percentages, not pixel to pixel comparisons from one year to another. If this is your intent, using the MCD12C1 product will not suit your needs, though you may have other HDF files which do, and those can be used in this application.

There are two script files in this project. The first takes the HDF files, creates TIFF files as bi-products from which the data is extracted, and creates and populates a phpMyAdmin SQL database with longitude, latitude, pixel (the pixel location in the x axis of the TIFF image), line (the pixel location in the y axis of the TIFF image), sample_id (the year), and land class. The second script allows you to query the database using a shapefile of the geographic location you wish to have data for. 

This Repo contains all the necessary files to replicate my process, tweak functionality as is needed, and create a dataset for your own research purposes. Please read the Project Description for a more in-depth explanation of the code if you need to modify it. 

Please do not monetize or use this code in commercial productions without my consent. 



## Setup

<u>Step 1:</u> Start the Docker File:

In order to properly run the GDAL for python module, it is necessary to run the docker file. Chose a folder - I chose to create a new folder and call it workingdir. Within the chosen folder place the docker file and create another folder called projects. All other files should go in the folder projects. 

Open PowerShell in the workingdir folder and run the following commands to build the docker image:

```python
docker build . -t pygdal

docker run -it --rm -p 8000:8888 -v "${PWD}/projects:/projects" pygdal
```



<u>Step 2:</u> Before running any scripts, set up the config.sample.py file with your phpMyAdmin credentials 

```python
c = {'passwd': '','user': '', 'host': '', 'database': ''}
```



<u>Step 3:</u> Once the docker image is running, run the script HDF_to_Data_arg.py by typing in the command line:

``` python
python HDF_to_Data_arg.py hdf_sourcefiles_MCD12Q1 Brazil -cleardata 1
```

where HDF_to_Data_arg.py is the script, hdf_sourcefiles_MCD12Q1 is the sourcefolder (folder with the HDF files - this is one of the two folders I included in this Repo as examples), Brazil is the database table name prefix, and -cleardata 1 is specifying that you wish to clear out the folder if it exists before populating it (if you wish to append, do not include -cleardata).

Depending on how many HDF files you have, and how large those files are, this process can take some time. You can check the progress by logging into your phpMyAdmin account.



<u>Step 4:</u> Now that your database is populated, you can use the Query_Data_arg.py script to query land class data for a specified region and time period by typing in the command line: 

```
python Query_Data_arg.py LegalAmazonArea.json -reduceboundary 10 2010 2011 2012
```

where HDF_to_Data_arg.py is the script, LegalAmazonArea.json is the boundary file I have provided in this Repo as an example, -reduceboundary 10 specifies that the number of points in the boundary file will be divided by 10 (so if there were 1000 points there will now be 100), and 2010 2011 2012 are the years for which you will query land class data. 



## Project Description 

#### Part 1: HDF to Data 

An overview of components of the script HDF_to_Data_arg.py

*Please note that while I go over many of the lines, I do not go over all the lines of code - please see the file for complete code*.

Instead of hard-coding many decisions and inputs, I use argparse to allow users to specify the files they would like to use and the name of the table they would like to create in the database which will be created. 

If you want to allow users to make additional decisions - for example, letting the user decide which SUBDATASET to use - you would need to make another parser argument. 

``` python

parser = argparse.ArgumentParser(description='Specify the name of the folder with the source files, the prefix of the SQL table you are creating, and whether you would like to clear that table before running the new code')

parser.add_argument('sourcefolder', type=str,help='The name of the directory in which your source files are located.')

parser.add_argument('tableprefix', type=str, help='What would you like to call the prefix of the SQL tablename')

parser.add_argument('-cleardata', type=str, help='Specifying cleardata means you wish to empty the SQL table before populating data - choosing not to include clear data will result in data appending to the table')

args = parser.parse_args()
```

I then set parameters using the user-defined arguments , and set up the folder structure. 

``` python
sourcefilefolder = args.sourcefolder

mypath = os.path.join('Data', str(args.tableprefix))
tifpath = os.path.join(mypath, 'tiffolder')
tokenpath = os.path.join(mypath, 'tokens')
```

I then create the directories I just defined: 

```python
if os.path.isdir(mypath):
    shutil.rmtree(mypath)

Path(mypath).mkdir(parents=True, exist_ok=True)
```

In order to extract the data from the HDF files I first converted them to GoTIFF images. I use the subprocess python module to call arguments in the command line. If you are using the NASA HDF files which I am using, they will have 'RANGEENDINGDATE' and 'SUBDATASET_1_NAME' and the code under **for line in out.splitlines():** will result in the selection of the sub dataset which follows the International Geosphere-Biosphere Programme (IGBP) legend (*see the MCD12_User_Guide pg 16). This code may need to be adjusted if you would like to select a different classification scheme or are using different HDF files whose output values may differ from the ones I have. The first command line call returns the sub dataset. The second command line call takes the sub dataset and translates it to the GeoTIFF image which will be used to extract the land class data. 

```python
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
        
		out,err=sp.communicate()
        # Separate the output and error.
        rc=sp.wait()

        if rc == 0:
            for line in out.splitlines():
            #RANGEENDINGDATE=2001 <- get the date from inside the file
                if 'RANGEENDINGDATE' in line:
                    filedate = line 
                    fileyear = filedate.split('=')[1].split('-')[0]
                if 'SUBDATASET_1_NAME' in line:
                    subdataset = line.split('=')[1]

        
        cmd2 = 'gdal_translate '+str(subdataset)+ ' ' +tifpath +'/'+ str(n)+'_'+str(fileyear)+'.tif'


        # Use shell to execute the command
        sp2 = subprocess.Popen(cmd2,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True)

        # Separate the output and error.
        out,err=sp2.communicate()

        rc2=sp2.wait()
        print(rc2)

    else:
        continue
```

Now that the GeoTIFF images have been created for the HDF files, a user-specified table will be created in your phpMyAdmin SQL database and the data extracted from the TIFF images will be written to that table. 

The following definition clears the data from the data table if that table already exists and if the user specifies they want the data cleared (from the -cleardata argument). Otherwise, the data will be appended. If you wanted to use this code for multiple sets of HDF files and store them in your database as different tables you can do so, because each time you create a new user defined prefix for the table. For example, if you had a set of HDF files for South America and a set for Africa and wanted those to be in two separate tables, you could run the script with for each set and give different table prefixes such that the script will build you a new table each time. Please be aware that this code presents a risk for python injection (I am still working on a solution to this problem).

The use of tokens is to take a group of data and dump it into the database at once. This simply limits the amount of times you are connecting to the database and can make the script run faster. I wrote this definition to be used further down in the code. Note that two data columns are created but not populated at this time: geo_point and pixel_point. 

``` python
def WriteToDatabase():   
    
    conn = pymysql.connect(host=config.sample.c['host'], port=3306, 	user=config.sample.c['user'], passwd=config.sample.c['passwd'], database=config.c['database'], autocommit=True)
                             
    
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

        sql ='''INSERT INTO `'''+config.c['database']+'''`.`'''+tablename+'''`
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
        
```

Next I create a text file called tokens.txt - this is an intermediary file into which I dump the data and then draw the data to populate the database. You can change the block size, if desired. 

```python
f = open(tokenpath+'/tokens.txt','w')
f.write('')
f.close()
f = open(tokenpath+'/tokens.txt','a')

blocksize = 10000
```

Now I run a loop for each tif file (one of which has been created for each source file). First I determine the raster size (the number of pixels and lines in the TIFF image).

```python
for filename in os.listdir(tifpath):
    tokens = []
    pixellist = []
    n=0
    if filename.endswith(".tif"):
    
        src = gdal.Open(tifpath+'/'+str(filename))
        X = src.RasterXSize 
        Y = src.RasterYSize

        P1=0
        L1=0
        P2=X
        L2=Y
```

I then create a list of all the pixels in the GeoTIFF image with the following loop:

```python
        p = P1
        while p < P2:
            l = L2 - 1
            
            while l > L1:
                pixellist.append(str(p)+' '+str(l))
                l -= 1
            p += 1 
   
```

I gather the sample (which is the year). I build the year into the GeoTIFF image file names so the following code would always apply - but if you have different HDF files you will need to make sure to adjust the code from the original sub process call to identify the year from that file's metadata. 

```python
		sample = filename.split('_')[1]
```

I then use the gdal module in python to gather the basic file dimension data using the GetGeoTransform(). 

```python
        ds = gdal.Open(tifpath+'/'+filename) 
        xoffset, px_w, rot1, yoffset, px_h, rot2 = ds.GetGeoTransform()
```

I then load the image into memory using Image from the PIL module in python. This is very important because if you try to get the land class data by calling gdal in the command line for each pixel, the image is loaded into memory for every single pixel (and there are millions of pixels per file) - the process is debilitatingly slow. The Image from PIL module allows you to query based on pixel, which is used later in the code.

```python
        im = Image.open(tifpath+'/'+filename)
        allpix = im.load()
```

I then use the iterate through all the pixels in the pixellist I previously created. pixel and latlon are generated, respectively, directly from the pixellist, and from the parameters gathered using GetGeoTransform() above. 

```python
        
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
            
```

At this point I use the image I have loaded into memory using Image to extract the data (land class) from the individual pixel. Try/except is used to catch any errors, but most issues I ran into were fixed by altering the way I generated the pixellist to include in the list only the amount of lines and pixels which actually exist in each image. 

```python
            try:
                landclass = allpix[int(P),int(L)] 
            except Exception as e:
                print("Pixel Error", P, L)
                print(e)
                exit()

```

All of the parameters I have gathered into the tokens list and, when the blocksize has been met, are written to the tokens.txt file. 

```python
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
```



I then update the SQL table, setting the two un-written columns to phpMyAdmin Point variables for geo_location and pixel_location. phpMyAdmin allows you to query points which are in or out of a boundary of points, which I will use in the second script to query based on shapefiles of geographic regions. 

```python
sql =''' UPDATE `%s` SET geo_point = ST_GeomFromText(testtable.geo_location), pixel_point = ST_GeomFromText(testtable.pixel_location);'''

cur = conn.cursor(pymysql.cursors.DictCursor)
cur.executem(sql, tablename)
conn.commit()
cur.close()  
```





#### Part 2: Query Data

An overview of components of the script  Query_Data_arg.py

*Please note that while I go over many of the lines, I do not go over all the lines of code - please see the file for complete code*.

After installing the modules I have set up the user arguments. I have three user arguments but find it pertinent to explain the last one. argyears takes multiple years separated by spaces. If can take one year, e.g. 2010, or multiple years, e.g. 2010 2011 2012. Since it is a mandatory argument the user does not specify argyears, and they are required to specify at least one year. 

```python
parser = argparse.ArgumentParser(description='Here the user must define the boundary file, whether you wish to reduce the boundary (which may be helpfull for very large shapefiles), and the years for which you wish to query data')

parser.add_argument('argyears', metavar='N', type=int, nargs='+', help='Specify all years for which you would like the data')

args = parser.parse_args()
```

I then set parameters based on the user defined arguments.

```python
argyearlist = args.argyears
boundaryfile = args.boundaryfile
reduction = args.reduceboundary
```

I then open the user-provided boundary file using json.load() and populate newMap, which I then write to a new json file using json.dump(), open the new file - again using json.load() - and defined the variable polygon as WKT. At this point you may need to alter the code to account for your particular boundary file as I did not make this code adaptable to different file formats. Make sure that when you adjust the file you do not change the format of newMap, or you may have issues running the rest of the script. 

```python
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
```

I then set up a loop which iterates over each year specified by the user, calling the points within the boundary file for that year by executing the SQL query. Currently the table is hard-coded, and you will need to replace `points2` with your table name (I am still working on making this a user argument).

```python
yearlist = []
coordslist = []

n = 0
for year in argyearlist:
    
    sql = '''SELECT geo_location, sample_id, land_class FROM `points2` 
    WHERE ST_CONTAINS(GeomFromText(%s), geo_point) 
    AND sample_id = %s'''
    
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute(sql, (polygon, year))
    conn.commit()
    cur.close()  
    
```

In order to be able to index properly the lines in the cursor must be converted from string type to dictionary type. I do this by creating linedict. I then use landclassdict as an intermediate step which tallies the number of pixels of each land class within the boundary. I also tally totalcount in order to determine land class percent. I use the landclassdict dictionary to populate the classdict dictionaries. Using this method also allows the code to be more adaptive - if your HDF file uses a different classification scheme, this code will accommodate that as I have not hard-coded the land-class text values to their number key values.

Note that I also include an if n = 0 statement which, only for the first iteration of the outer-most loop (see above where n is set), gathers the coordinates as a list and appends them to the coordslist (which is also set above). 

 I store the data for each land class in classdict dictionary, which are collectively stored in the classlist list. classlist is then stored as one of the values in the yearlist list, along with the year. 

```python
    landclassdict = {}
    totalcount = 0
    for line in cur:
        linedict = dict(line)
        
        if n = 0:
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
```



I then append the gathered data into nested levels of the json output, and print that output using json.dumps(). polydict contains metadata - and you can add data to this or other levels of the output depending on your needs. 

```python
polydict = {}
polydict['coordinates list'] = coordslist  
 
alldict = {}
alldict['yearlist'] = yearlist
alldict['polygon'] = polydict


print(json.dumps(alldict))

```

The output is in json format, and should be suitable to using or converting for your specific needs.



## Conclusion

This project can be modified to gather other types of data stored in HDF files, but will work particularly well with the NASA files I build the script around. It is important to note that there are a few limitations to using the data I used. This script and it's end product relies on the data generated by machine learning algorithms which identify land class. The machine learning algorithms are not stable enough to classify a single pixel of land data year-by-year. As those machine learning algorithms advance and become more precise with higher resolution, the potential applications for this script only grows. It is currently best used for broad-level summation land-class projects, and notable progress is being made from this point. Even currently, instead of having to manually observe and classify land in limited areas, a computer can classify the entire world. Having the ability to analyze land-class and it's relation to other factors is valuable for many applications. My personal scope involves analyzing land-degradation and food and environmental security, but this kind of data may be interesting to researchers, lawmakers, environmental groups, analysts, and others. 

