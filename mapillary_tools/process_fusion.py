import os
import sys
import subprocess

def process_fusion(import_path,
                   front,
                   back,
                   projection,
                   keep_original,
                   verbose):

    list = get_files(front, back)

    if len(list) == 0:
        sys.exit('no front files to process')

    for fn_front, fn_back in list:
        print fn_front, fn_back
        out_file = import_path + fn_front[len(front):]
        out_file = out_file.replace('GFRNT', '')
        out_dir = os.path.dirname(out_file)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        subprocess.check_output([
            '/Applications/Fusion Studio 1.2.app/Contents/MacOS/FusionStudio',
            '--front', fn_front,
            '--back', fn_back,
            '--output', out_file,
            '--iq', '1',
        ])

    print projection


def get_files(fpath, bpath):
    files = []

    for(dirpath, dirnames, filenames) in os.walk(fpath):
        for f in filenames:
            if f.lower().endswith('jpg'):
                back_path = dirpath[len(fpath):]
                back_path = back_path.replace('GFRNT', 'GBACK')
                back_path = os.path.join(bpath, back_path, f.replace('F', 'B'))
                if not os.path.isfile(back_path):
                    print('no back image for', f, ', skipping')
                    continue

                files.append((os.path.join(dirpath, f), back_path))

    return files
