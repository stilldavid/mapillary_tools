import processing
import uploader
import os
import sys
import datetime
import process_import_meta_properties
from exif_write import ExifEdit
import csv

META_DATA_TYPES = ["string", "double", "long", "date", "boolean"]

MILLISECONDS_PRECISION_CUT_OFF = 10000000000


def format_time(timestamp, time_utc=False, time_format='%Y-%m-%dT%H:%M:%SZ'):
    if time_utc:
        division = 1.0 if int(
            timestamp) < MILLISECONDS_PRECISION_CUT_OFF else 1000.0
        t_datetime = datetime.datetime.utcfromtimestamp(
            int(timestamp) / division)
    else:
        t_datetime = datetime.datetime.strptime(timestamp, time_format)
    return t_datetime


def validate_meta_data(meta_columns, meta_names, meta_types):

    if any([x for x in [meta_columns, meta_names, meta_types]]):

        # if any of the meta data arguments are passed all must be
        if any([not(x) for x in [meta_columns, meta_names, meta_types]]):
            print(
                "Error, if extracting meta data you need to specify meta_columns, meta_names and meta_types.")
            sys.exit()

        # get meta data column numbers
        meta_columns = meta_columns.split(",")
        try:
            meta_columns = [int(field) - 1 for field in meta_columns]
        except:
            print('Error, meta column numbers could not be extracted. Meta column numbers need to be separated with commas, example "7,9,10"')
            sys.exit()

        # get meta data names and types
        meta_names = meta_names.split(",")
        meta_types = meta_types.split(",")

        # exit if they are not all of same length
        if len(meta_columns) != len(meta_names) or len(meta_types) != len(meta_names):
            print(
                "Error, number of meta data column numbers, types and names must be the same.")
            sys.exit()

        # check if types are valid
        for meta_type in meta_types:
            if meta_type not in META_DATA_TYPES:
                print("Error, invalid meta data type, valid types are " +
                      str(META_DATA_TYPES))
                sys.exit()
    return meta_columns, meta_names, meta_types


def convert_from_gps_time(gps_time):
    """ Convert gps time in ticks to standard time. """
    # TAI scale with 1970-01-01 00:00:10 (TAI) epoch
    os.environ['TZ'] = 'right/UTC'
    # time.tzset()
    gps_timestamp = float(gps_time)
    gps_epoch_as_gps = datetime.datetime(1980, 1, 6)

    # by definition
    gps_time_as_gps = gps_epoch_as_gps + \
        datetime.timedelta(seconds=gps_timestamp)

    # constant offset
    gps_time_as_tai = gps_time_as_gps + \
        datetime.timedelta(seconds=19)
    tai_epoch_as_tai = datetime.datetime(1970, 1, 1, 0, 0, 10)

    # by definition
    tai_timestamp = (gps_time_as_tai - tai_epoch_as_tai).total_seconds()

    # "right" timezone is in effect
    return (datetime.datetime.utcfromtimestamp(tai_timestamp))


def get_image_index(image, file_names):

    image_index = None
    try:
        image_index = file_names.index(image)
    except:
        try:
            file_names = [os.path.basename(entry) for entry in file_names]
            image_index = file_names.index(os.path.basename(image))
        except:
            pass
    return image_index


def parse_csv_geotag_data(csv_data, image_index, column_indexes, convert_gps_time=False, convert_utc_time=False, time_format="%Y:%m:%d %H:%M:%S.%f"):

    timestamp = None
    lat = None
    lon = None
    heading = None
    altitude = None

    timestamp_column = column_indexes[1]
    latitude_column = column_indexes[2]
    longitude_column = column_indexes[3]
    heading_column = column_indexes[4]
    altitude_column = column_indexes[5]

    if timestamp_column:
        timestamp = csv_data[timestamp_column][image_index]
        timestamp = convert_from_gps_time(
            timestamp) if convert_gps_time else format_time(timestamp, convert_utc_time, time_format)

    if latitude_column:
        lat = float(csv_data[latitude_column][image_index])
    if longitude_column:
        lon = float(csv_data[longitude_column][image_index])
    if heading_column:
        heading = float(csv_data[heading_column][image_index])
    if altitude_column:
        altitude = float(csv_data[altitude_column][image_index])

    return timestamp, lat, lon, heading, altitude


def parse_csv_meta_data(csv_data, image_index, meta_columns, meta_types, meta_names):
    meta = {}
    if meta_columns:
        for field, meta_field in enumerate(meta_columns):
            try:
                tag_type = meta_types[field] + "s"
                tag_value = csv_data[meta_field][image_index]
                tag_key = meta_names[field]
                process_import_meta_properties.add_meta_tag(
                    meta, tag_type, tag_key, tag_value)
            except:
                print("Error, meta data {} could not be extracted.".format(tag_key))
    return meta


def read_csv(csv_path, delimiter=",", header=False):
    csv_data = []

    with open(csv_path, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=delimiter)
        if header:
            next(csvreader, None)

        csv_data = zip(*csvreader)
    return csv_data


def process_csv(import_path,
                csv_path,
                filename_column,
                timestamp_column=None,
                latitude_column=None,
                longitude_column=None,
                heading_column=None,
                altitude_column=None,
                time_format="%Y:%m:%d %H:%M:%S.%f",
                convert_gps_time=False,
                convert_utc_time=False,
                delimiter=",",
                header=False,
                meta_columns=None,
                meta_names=None,
                meta_types=None,
                verbose=False,
                keep_original=False):

    # sanity checks
    if not import_path or not os.path.isdir(import_path):
        print("Error, import directory " + import_path +
              " doesnt not exist, exiting...")
        sys.exit()

    if not csv_path or not os.path.isfile(csv_path):
        print("Error, csv file not provided or does not exist. Please specify a valid path to a csv file.")
        sys.exit()

    # get list of file to process
    process_file_list = uploader.get_total_file_list(import_path)
    if not len(process_file_list):
        print("No images found in the import path " + import_path)
        sys.exit()

    column_indexes = [filename_column, timestamp_column,
                      latitude_column, longitude_column, heading_column, altitude_column]
    if any([column == 0 for column in column_indexes]):
        print("Error, csv column numbers start with 1, one of the columns specified is 0.")
        sys.exit()

    column_indexes = map(lambda x: x - 1 if x else None, column_indexes)
    # checks for meta arguments if any
    meta_columns, meta_names, meta_types = validate_meta_data(
        meta_columns, meta_names, meta_types)

    # open and process csv
    csv_data = read_csv(csv_path,
                        delimiter=delimiter,
                        header=header)
    file_names = csv_data[filename_column - 1]

    # process each image
    for image in process_file_list:

        # get image entry index
        image_index = get_image_index(image, file_names)
        if image_index == None:
            print("Warning, no entry found in csv file for image " + image)
            continue

        # get required data
        timestamp, lat, lon, heading, altitude = parse_csv_geotag_data(
            csv_data, image_index, column_indexes, convert_gps_time, convert_utc_time, time_format)

        # get meta data
        meta = parse_csv_meta_data(
            csv_data, image_index, meta_columns, meta_types, meta_names)

        # insert in image EXIF
        exif_edit = ExifEdit(image)
        if timestamp:
            exif_edit.add_date_time_original(timestamp)
        if lat and lon:
            exif_edit.add_lat_lon(lat, lon)
        if heading:
            exif_edit.add_direction(heading)
        if altitude:
            exif_edit.add_altitude(altitude)
        if meta:
            exif_edit.add_image_history(meta["MAPMetaTags"])

        filename = image
        filename_keep_original = processing.processed_images_rootpath(image)

        if os.path.isfile(filename_keep_original):
            os.remove(filename_keep_original)

        if keep_original:
            if not os.path.isdir(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            filename = filename_keep_original

        try:
            exif_edit.write(filename=filename)
        except:
            print("Error, image EXIF could not be written back for image " + image)
            return None
