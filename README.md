# NASA_HD4_to_Land_Class_Dataset
Convert HD4 files to tif images and gather land class data for all the pixels in a designated boundary

Problem Statement:

I began my Capstone research looking for a dataset which gave land classification info for land regions over time. I could not find such a dataset. NASA has several products which encode land class data for the entire global region, but they are encoded in HD4 files - not the format I needed them in. In order to analyze the change in land type over time, I would first need to decode the HD4 files into a usable format. 

I took the following steps to solve this problem:

1. Convert the HD4 Files to Geotif files (.tif images)
2. Use the Geotif files to extract the following data:
   1. Pixel
   2. Geographic Location
   3. Land Class 

