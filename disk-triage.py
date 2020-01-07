#!python
import os, sys, argparse, math, binascii
from collections import OrderedDict
from colorama import Fore, Back, Style
import QCOW, screen
# Output functions

VERSION = "0.0.5"

def get_info(img, args):
    img.get_info(args)

def get_map(img, args):
    img.get_map(args)

def get_snapshots(img, args):
    img.get_snapshots(args)


def get_header(img, args):
    img.get_header(args)

def get_tables(img, args):
    img.get_tables(args)

def get_data(img, args):
    img.get_data(args)

def get_check(img, args):
    img.check(args)

def do_mount(img, args):
    img.mount(args)

def do_unmount(img, args):
    img.unmount(args)

def main(argv):
    parser = argparse.ArgumentParser(
        description='Perform various low level triage functions on the provided disk image file.',
        epilog="Exit status: \n0 if OK, \n1 if minor problems(e.g., ...), \n2 if serious trouble (e.g. invalid filename).")
    # exclusive_group = parser.add_mutually_exclusive_group()
    # table_group = parser.add_argument_group('group')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + VERSION)
    parser.add_argument('-v', '--verbosity', type=int, default=0)
    parser.add_argument(
        '-j', '--json', action='store_true',
        help='Output results in JSON format.')  # TODO:
    parser.add_argument(
        '-z', '--zeros', action='store_true',
        help='Output all values including empty entries (Do not suppress unused entries/clusters/blocks).')
    subparsers = parser.add_subparsers()

    # Info command subparser
    info_subparser = subparsers.add_parser(
        'info', help='Output metadata from the disk image file.')
    info_subparser.add_argument(
        '-a', '--all', action='store_true',
        help='Output additional information including disk image tables.')
    info_subparser.add_argument(
        '-d', '--detailed', action='store_true',
        help='Perform deep inspection of values and additional validations addresses and data.')
    info_subparser.set_defaults(func=get_info)

    # Map command subparser
    map_subparser = subparsers.add_parser(
        'map', help='Output a visual block depiction of the disk image file.')
    map_subparser.add_argument(
        '-d', '--detailed', action='store_true',
        help='Perform deep inspection of values and additional validations addresses and data.')
    map_subparser.set_defaults(func=get_map)

    # Snapshots command subparser
    snapshot_subparser = subparsers.add_parser(
        'snapshots', help='Output snapshot info of the disk image file.')
    snapshot_subparser.add_argument(
        '-d', '--detailed', action='store_true',
        help='Perform deep inspection of values and additional validations addresses and data.')
    snapshot_subparser.set_defaults(func=get_snapshots)

    # Header command subparser
    header_subparser = subparsers.add_parser(
        'header', help='Output header of disk image file.')
    header_subparser.add_argument(
        '-d', '--detailed', action='store_true',
        help='Perform deep inspection of values and additional validations addresses and data.')
    header_subparser.set_defaults(func=get_header)

    # Tables command subparser
    tables_subparser = subparsers.add_parser(
        'tables', help='Output file tables.')
    tables_subparser.add_argument(
        '-a', '--all', action='store_true',
        help='Output all tables.')
    tables_subparser.add_argument(
        '-p', '--primary', action='store_true',
        help='Output primary allocation tables.')
    tables_subparser.add_argument(
        '-s', '--secondary', action='store_true',
        help='Output secondary allocation tables.')
    tables_subparser.add_argument(
        '-R', '--raw', action='store_true',
        help='Output array of raw entries from parsed table(s).')
    tables_subparser.add_argument(
        '-d', '--detailed', action='store_true',
        help='Perform deep inspection of values and additional validations addresses and data.')
    tables_subparser.add_argument(
        '-n', '--nonzero', action='store_true',
        help='Include possible non-zero entries beyond allocated in header (Enumerates all entries up to cluster boundary).')
    tables_subparser.set_defaults(func=get_tables)

    # Data command subparser
    data_subparser = subparsers.add_parser(
        'data', help='Output cluster meta-data of disk image file.')
    data_subparser.add_argument(
        '-a', '--address', metavar='0xFFFFFFFFFFFFFFFF',
        default='0x0000000000000000',
        help='Starting virtual address of output.')
    data_subparser.add_argument(
        '-H', '--human-readable', action='store_true',
        help='Output decoded data.')
    data_subparser.add_argument(
        '-d', '--detailed', action='store_true',
        help='Perform deep inspection of values and additional validations addresses and data.')
    data_qty_group = data_subparser.add_mutually_exclusive_group()
    data_qty_group.add_argument(
        '-n', '--number_of_chunks', type=int, default=1,
        help='Number of data chunks to output.')
    data_qty_group.add_argument(
        '-A', '--all', action='store_true',
        help='Number of data chunks to output.')

    data_chunk_type_group = data_subparser.add_mutually_exclusive_group()
    data_chunk_type_group.add_argument(
        '-B', '--bytes', action='store_true',
        help='Output data in byte sized chunks.')
    data_chunk_type_group.add_argument(
        '-S', '--sectors', action='store_true',
        help='Output data in sector sized chunks.')

    data_set_group = data_subparser.add_mutually_exclusive_group()
    data_set_group.add_argument(
        '-r', '--raw', action='store_true',
        help='Only a single block of raw data.')
    data_set_group.add_argument(
        '-0', '--no-data', action='store_true',
        help='Only output cluster metadata and no actual data.')
    data_set_group.add_argument(
        '-m', '--no-metadata', action='store_true',
        help='Only output data and no cluster metadata.')

    data_subparser.set_defaults(func=get_data)

    # Check command subparser
    check_subparser = subparsers.add_parser(
        'check', help='Output header of disk image file.')
    check_subparser.add_argument(
        '-d', '--detailed', action='store_true',
        help='Perform deep inspection of values and additional validations addresses and data.')
    check_subparser.add_argument(
        '-a', '--all', action='store_true',
        help='Perform all consistency checks on disk image file.')
    check_subparser.add_argument(
        '-D', '--dereferenced', action='store_true',
        help='Check for dereferenced clusters.')
    check_subparser.add_argument(
        '-l', '--leaks', action='store_true',
        help='Check for leaked clusters.')
    check_subparser.set_defaults(func=get_check)

    # Do command subparser
    do_subparser = subparsers.add_parser(
        'do', help='Various command shortcuts for manipulating a disk image file.')
    do_subparsers = do_subparser.add_subparsers()
    mount_subparser = do_subparsers.add_parser(
        'mount', help='Attempt to mount disk image file.')
    mount_subparser.set_defaults(func=do_mount)
    unmount_subparser = do_subparsers.add_parser(
        'unmount', help='Attempt to unmount disk image file.')
    unmount_subparser.set_defaults(func=do_unmount)

    # Positional filename argument
    parser.add_argument(
        # 'file', type=argparse.FileType('rb', 0), metavar='FILE',
        # help='Filename of the disk image to be triaged.')
        'file',
        type=str,
        metavar='FILE',
        help='Filename of the disk image to be triaged.')
    args = parser.parse_args()
    print(Style.RESET_ALL)
    if args.verbosity > 0:
        print(args)
    if not os.path.isfile(args.file):
        print("Invalid file")
        exit(3)
    with open(args.file, 'rb') as disk_file:
        file_ext = os.path.splitext(args.file)[1][1:]
        if file_ext in {'qcow','qcow2','qcow3'}:
            img = QCOW.Image(disk_file)
            args.func(img, args)
        elif file_ext in {'raw', 'cloop', 'cow', 'img', 'iso', 'vdi', 'vhd', 'vmdk', 'vpc', 'wim', 'dmg'}:
            print("Not Implemented Yet.")
        else:
            print("Unsupported filetype: " + file_ext)

if __name__ == "__main__":
    main(sys.argv[1:])
