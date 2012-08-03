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
        flags = val['flags']
        cv_type = flags & 7
        channels = 1 + (flags >> 3) & 63;
        if cv_type == 0:
            cv_type_name = "CV_8U"
            cv_data_symbol = "B"
        elif cv_type == 1:
            cv_type_name = "CV_8S"
            cv_data_symbol = "b"
        elif cv_type == 2:
            cv_type_name = "CV_16U"
            cv_data_symbol = "H"
        elif cv_type == 3:
            cv_type_name = "CV_16S"
            cv_data_symbol = "h"
        elif cv_type == 4:
            cv_type_name = "CV_32S"
            cv_data_symbol = "i"
        elif cv_type == 5:
            cv_type_name = "CV_32F"
            cv_data_symbol = "f"
        elif cv_type == 6:
            cv_type_name = "CV_64F"
            cv_data_symbol = "d"
        else:
            print "Sorry but the type CV_USRTYPE1 is not supported"
            return
        rows = val['rows']
        cols = val['cols']

        line_step = val['step']['p'][0]

        # Print information about image.
        print "Image details: " + cv_type_name + " with # channels " + \
            str(channels) + ", rows: " + str(rows) + " cols: " + str(cols)

        data_address = unicode(val['data']).encode('utf-8').split()[0]
        data_address = int(data_address, 16)

        self.build(cols, rows, channels, line_step, data_address, cv_data_symbol)


    def iplimage(self, val):
        depth = val['depth']
        channels = val['nChannels']
        if depth == 0x8:
            cv_type_name = "IPL_DEPTH_8U"
            cv_data_symbol = "B"
            elem_size = 1
        elif depth == -0x7FFFFFF8:
            cv_type_name = "IPL_DEPTH_8S"
            cv_data_symbol = "b"
            elem_size = 1
        elif depth == 0x10:
            cv_type_name = "IPL_DEPTH_16U"
            cv_data_symbol = "H"
            elem_size = 2
        elif depth == -0x7FFFFFF0:
            cv_type_name = "IPL_DEPTH_16S"
            cv_data_symbol = "h"
            elem_size = 2
        elif depth == -0x7FFFFFE0:
            cv_type_name = "IPL_DEPTH_32S"
            cv_data_symbol = "i"
            elem_size = 4
        elif depth == 0x20:
            cv_type_name = "IPL_DEPTH_32F"
            cv_data_symbol = "f"
            elem_size = 4
        elif depth == 0x40:
            cv_type_name = "IPL_DEPTH_64F"
            cv_data_symbol = "d"
            elem_size = 8
        else:
            print "Sorry but the type CV_USRTYPE1 is not supported"
            return

        rows = val['height'] if str(val['roi']) == '0x0' else val['roi']['height']
        cols = val['width'] if str(val['roi']) == '0x0' else val['roi']['width']
        line_step = val['widthStep']

        # Print information about image.
        print 'Image details: ' + cv_type_name + ' with ' + str(channels) +\
          ' channels, rows: ' + str(rows) + " cols: " + str(cols)

        data_address = unicode(val['imageData']).encode('utf-8').split()[0]
        data_address = int(data_address, 16)
        if str(val['roi']) != '0x0':
            x_offset = int(val['roi']['xOffset'])
            y_offset = int(val['roi']['yOffset'])
            data_address += line_step * y_offset + x_offset * elem_size * channels

        self.build(cols, rows, channels, line_step, data_address, cv_data_symbol)


    def build(self, width, height, n_channel, line_step, data_address, data_type):
        """ Copies the image data to a PIL image and shows it.

        Args:
            width: The image width, in pixels.
            height: The image height, in pixels.
            n_channel: The number of channels in image.
            line_step: The offset to change to pixel (i+1, j) being
                in pixel (i, j), in bytes.
            data_address: The address of image data in memory.
            data_type: Python struct module code to the image data type.
        """
        width = int(width)
        height = int(height)
        n_channel = int(n_channel)
        line_step = int(line_step)
        data_address = int(data_address)

        infe = gdb.inferiors()
        memory_data = infe[0].read_memory(data_address, line_step * height)

        # Calculate the memory padding to change to the next image line.
        # Either due to memory alignment or a ROI.
        if data_type in ('b', 'B'):
            elem_size = 1
        elif data_type in ('h', 'H'):
            elem_size = 2
        elif data_type in ('i', 'f'):
            elem_size = 4
        elif data_type == 'd':
            elem_size = 8
        padding = line_step - width * n_channel * elem_size

        # Format memory data to load into the image.
        image_data = []
        if n_channel == 1:
            mode = "L"
            fmt = "%d%s%dx" % (width, data_type, padding)
            for line in chunker(memory_data, line_step):
                image_data.extend(struct.unpack(fmt, line))
        elif n_channel == 3:
            mode = "RGB"
            fmt = "%d%s%dx" % (width * 3, data_type, padding)
            for line in chunker(memory_data, line_step):
                image_data.extend(struct.unpack(fmt, line))

        # Fit the opencv elemente data in the PIL element data
        if data_type == 'b':
            image_data = [i+128 for i in image_data]
        elif data_type == 'H':
            image_data = [i>>8 for i in image_data]
        elif data_type == 'h':
            image_data = [(i+32768)>>8 for i in image_data]
        elif data_type == 'i':
            image_data = [(i+2147483648)>>24 for i in image_data]
        elif data_type in ('f','d'):
            # A float image is discretized in 256 bins for display.
            max_image_data = max(image_data)
            min_image_data = min(image_data)
            img_range = max_image_data - min_image_data
            if img_range > 0:
                image_data = [int(255 * (i - min_image_data) / img_range) \
                              for i in image_data]
            else:
                image_data = [0 for i in image_data]


        if n_channel == 3:
            # OpenCV stores the channels in BGR mode. Convert to RGB while packing.
            image_data = zip(*[image_data[i::3] for i in [2, 1, 0]])

        # Show image.
        img = Image.new(mode, (width, height))
        img.putdata(image_data)
        img.show()

cv_imshow()
