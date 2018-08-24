
from mapillary_tools.process_fusion import process_fusion


class Command:
    name = 'process_fusion'
    help = "Preprocess tool: Combine front and back GoPro Fusion images in to equirectangular images"

    def add_basic_arguments(self, parser):
        parser.add_argument('--front', help="the directory of front images", required=True, action='store')
        parser.add_argument('--back', help="the directory of back images", required=True, action='store')
        parser.add_argument('--output', help="the directory of output images", required=True, action='store')
        parser.add_argument('--projection', help="the directory of back images", default='equirectangular', required=False, action='store')

    def add_advanced_arguments(self, parser):
        parser.add_argument('--keep_original', help='Do not overwrite original images, instead save the processed images in a new directory by adding suffix "_processed" to the import_path.',
                            action='store_true', default=False, required=False)

    def run(self, args):
        process_fusion(**vars(args))
