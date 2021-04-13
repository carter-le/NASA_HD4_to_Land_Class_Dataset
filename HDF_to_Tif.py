#take the sourcefiles (which are hdf files) and convert them to geotif images 
# library - argparse 

import subprocess
import os

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

