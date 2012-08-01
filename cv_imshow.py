import gdb
import Image
import struct

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))


class cv_imshow (gdb.Command):
    """Diplays the content of an opencv image"""

    def __init__ (self):
        super (cv_imshow, self).__init__ ("cv_imshow",
                                          gdb.COMMAND_SUPPORT,
                                          gdb.COMPLETE_FILENAME)

    def invoke (self, arg, from_tty):
        # Access the variable from gdb.
        frame = gdb.selected_frame()
        val = frame.read_var(arg)
        if str(val.type.strip_typedefs()) == 'IplImage *':
            self.iplimage(val)
        else:
            self.cvmat(val)

    def cvmat(self, val):
        # Parse contents.
        flags = val["flags"]
        cv_type = flags & 7
        channels = 1 + (flags >> 3) & 63;
        if cv_type == 0:
            cv_type_name = "CV_8U"
            cv_byte_depth = 1
            cv_data_symbol = "B"
            isfloat = False
        elif cv_type == 1:
            cv_type_name = "CV_8S"
            cv_byte_depth = 1
            cv_data_symbol = "b"
            isfloat = False
        elif cv_type == 2:
            cv_type_name = "CV_16U"
            cv_byte_depth = 2
            cv_data_symbol = "H"
            isfloat = False
        elif cv_type == 3:
            cv_type_name = "CV_16S"
            cv_byte_depth = 2
            cv_data_symbol = "h"
            isfloat = False
        elif cv_type == 4:
            cv_type_name = "CV_32S"
            cv_byte_depth = 4
            cv_data_symbol = "i"
            isfloat = False
        elif cv_type == 5:
            cv_type_name = "CV_32F"
            cv_byte_depth = 4
            cv_data_symbol = "f"
            isfloat = True
        elif cv_type == 6:
            cv_type_name = "CV_64F"
            cv_byte_depth = 8
            cv_data_symbol = "d"
            isfloat = True
        else:
            print "Sorry but the type CV_USRTYPE1 is not supported"
            return
        rows = val["rows"]
        cols = val["cols"]

        # Print information about image.
        print "Image details: " + cv_type_name + " with # channels " + \
            str(channels) + ", rows: " + str(rows) + " cols: " + str(cols)

        if channels == 1:
            mode = "L"
        elif channels == 3:
            mode = "RGB"
        else:
            print "Number of channels not supported at the moment."
            return

        # Read memory from the inferior.
        infe = gdb.inferiors()
        data_address = unicode(val["data"]).encode('utf-8').split()[0]
        memory_data = infe[0].read_memory( \
            int(data_address, 16), rows * cols * cv_byte_depth * channels)

        # Format memory data to load into the image.
        if channels == 1:
            image_data = struct.unpack( \
                "%d%s" % (rows * cols, cv_data_symbol), memory_data)
        elif channels == 3:
            image_data = struct.unpack( \
                "%d%s" % (rows * cols * 3, cv_data_symbol), memory_data)
            if isfloat:
                # A float image is discretized in 256 bins for display.
                max_image_data = max(image_data)
                min_image_data = min(image_data)
                img_range = max_image_data - min_image_data
                if img_range > 0:
                    image_data = [int(255 * (i - min_image_data) / img_range) \
                                      for i in image_data]
                else:
                    image_data = [0 for i in image_data]
            # OpenCV stores the channels in BGR mode. Convert to RGB while
            # packing.
            image_data = zip(*[image_data[i::3] for i in [2, 1, 0]])

        # Show image.
        img = Image.new(mode, (cols, rows))
        img.putdata(image_data)
        img.show()



    def iplimage(self, val):

        depth = val['depth']
        channels = val['nChannels']
        if depth == 0x8:
            cv_type_name = "IPL_DEPTH_8U"
            cv_data_symbol = "B"
            isfloat = False
        elif depth == -0x7FFFFFF8:
            cv_type_name = "IPL_DEPTH_8S"
            cv_data_symbol = "b"
            isfloat = False
        elif depth == 0x10:
            cv_type_name = "IPL_DEPTH_16U"
            cv_data_symbol = "H"
            isfloat = False
        elif depth == -0x7FFFFFF0:
            cv_type_name = "IPL_DEPTH_16S"
            cv_data_symbol = "h"
            isfloat = False
        elif depth == -0x7FFFFFE0:
            cv_type_name = "IPL_DEPTH_32S"
            cv_data_symbol = "i"
            isfloat = False
        elif depth == 0x20:
            cv_type_name = "IPL_DEPTH_32F"
            cv_data_symbol = "f"
            isfloat = True
        elif depth == 0x40:
            cv_type_name = "IPL_DEPTH_64F"
            cv_data_symbol = "d"
            isfloat = True
        else:
            print "Sorry but the type CV_USRTYPE1 is not supported"
            return

        rows = int(val["height"])
        cols = int(val["width"])
        line_step = int(val['widthStep'])
        padding = line_step - cols * channels

        # Print information about image.
        print "Image details: " + cv_type_name + " with # channels " + \
            str(channels) + ", rows: " + str(rows) + " cols: " + str(cols)

        if channels == 1:
            mode = "L"
        elif channels == 3:
            mode = "RGB"
        else:
            print "Number of channels not supported at the moment."
            return

        # Read memory from the inferior.
        infe = gdb.inferiors()
        data_address = unicode(val["imageData"]).encode('utf-8').split()[0]
        memory_data = infe[0].read_memory( \
            int(data_address, 16), val['imageSize'])

        image_data = []
        # Format memory data to load into the image.
        if channels == 1:
            image_data = struct.unpack( \
                "%d%s" % (rows * cols, cv_data_symbol), memory_data)
        elif channels == 3:
            fmt = "%d%s%dx" % (cols * 3, cv_data_symbol, padding)
            for line in chunker(memory_data, line_step):
                image_data.extend(struct.unpack(fmt, line))

            # OpenCV stores the channels in BGR mode. Convert to RGB while
            # packing.
            image_data = zip(*[image_data[i::3] for i in [2, 1, 0]])

        # Show image.
        img = Image.new(mode, (cols, rows))
        img.putdata(image_data)
        img.show()

cv_imshow()
