import pyqrcode.tables
import pyqrcode.builder as builder

class QRCode:
    """This class represents a QR Code. To use this class simply give the
    constructor a string representing the data to be encoded, it will then
    build a code in memory. You can then save it in various formats. Note,
    codes can be written out as PNG files but this requires the PyPNG module.
    You can find the PyPNG module at http://packages.python.org/pypng/.
    
    Examples:
        >>> url = QRCode('http://uca.edu')
        >>> url.svg(sys.stdout, scale=1)
        >>> url.svg('uca.svg', scale=4)
        >>> number = QRCode(123456789012345)
        >>> number.png('big-number.png')
    """
    def __init__(self, content, error='H', version=None, mode=None):
        """When creating a QR Code only the content to be encoded is required,
        all the other properties of the code will be guessed based on the
        contents given. When the QRCode object is created the QR Code will be
        generated immediately.
        
        Unless you are familiar with QR Code's inner workings 
        it is recommended that you just specify the content and nothing else.
        However, there are cases where you may want to specify the various
        properties of the created code manually, this is what the other
        parameters do. Below, you will find a lengthy explanation of what
        each parameter is for.
        
        The error parameter sets the error correction level of the code. There
        are four levels defined by the standard. The first is level 'L' which
        allows for 7% of the code to be corrected. Second, is level 'M' which
        allows for 15% of the code to be corrected. Next, is level 'Q' which
        is the most common choice for error correction, it allow 25% of the
        code to be corrected. Finally, there is the highest level 'H' which
        allows for 30% of the code to be corrected. There are several ways to
        specify this parameter, you can use an upper or lower case letter,
        a float corresponding to the percentage of correction, or a string
        containing the percentage. See tables.modes for all the possible
        values. By default this parameter is set to 'H' which is the highest
        possible error correction, but it has the smallest available data
        capacity.
        
        The version parameter specifies the size and data capacity of the
        code. Versions are any integer between 1 and 40. Where version 1 is
        the smallest QR Code, and version 40 is the largest. If this parameter
        is left unspecified, then the contents and error correction level will
        be used to guess the smallest possible QR Code version that the 
        content will fit inside of. You may want to specify this parameter
        for consistency when generating several QR Codes with varying amounts
        of data.
        
        The mode parameter specifies how the contents will be encoded. By
        default, the best possible encoding for the contents is guessed. There
        are four possible encoding methods. First, is 'numeric' which is
        used to encode integer numbers. Next, is 'alphanumeric' which is
        used to encode ASCII characters. This mode can use only a limited
        set of characters. Most problematic is that it can only use upper case
        English characters, consequently, the content parameter will be
        subjected to str.upper() before encoding. See tables.ascii_codes for
        a complete list of available characters. We then have 'binary' encoding
        which just encodes the bytes directly into the QR Code (this encoding
        is the least efficient). Finally, there is 'kanji'  encoding (i.e.
        Japanese characters), this is unimplemented at this time.
        """
        #Coerce the content into a string
        self.data = str(content)
        
        #Check that the passed in error level is valid
        try:
            self.error = tables.error_level[str(error).upper()]
        except:
            raise ValueError('The error parameter is not one of '
                             '"L", "M", "Q", or "H."')
        
        #Guess the mode of the code, this will also be used for
        #error checking
        guessed_content_type = self._detect_content_type()
        
        #Force a passed in mode to be lowercase
        if mode:
            mode = mode.lower()
        
        #Check that the mode parameter is compatible with the contents
        if not mode:
            #Use the guessed mode
            self.mode = guessed_content_type
            self.mode_num = tables.modes[self.mode]
        elif guessed_content_type == 'binary' and \
             tables.modes[mode] != tables.modes['binary']:
            #Binary is only guessed as a last resort, if the
            #passed in mode is not binary the data won't encode
            raise ValueError('The content provided cannot be encoded with '
                             'the mode {}, it can only be encoded as '
                             'binary.'.format(mode))
        elif tables.modes[mode] == tables.modes['numeric'] and \
             guessed_content_type != 'numeric':
            #If numeric encoding is requested make sure the data can
            #be encoded in that format
            raise ValueError('The content cannot be encoded as numeric.')
        else:
            #The data should encode with the passed in mode
            self.mode = mode
            self.mode_num = tables.modes[self.mode]

        #Guess the "best" version
        self.version = self._pick_best_fit()
        
        #If the user supplied a version, then check that it has
        #sufficient data capacity for the contents passed in            
        if version:
            if version >= self.version:
                self.version = version
            else:
                raise ValueError('The data will not fit inside a version {} '
                                 'code with the given encoding and error '
                                 'level (the code must be at least a '
                                 'version {}).'.format(version, self.version))
        
        #Build the QR Code
        self.builder = builder.QRCodeBuilder(data=content,
                                     version=self.version,
                                     mode=self.mode,
                                     error=self.error)
       
        #Save the code for easier reference
        self.code = self.builder.code

    def _detect_content_type(self):
        """This method tries to auto-detect the type of the data. It first
        tries to see if the data is a valid integer, in which case it returns
        numeric. Next, it tests the data to see if it is 'alphanumeric.' QR
        Codes use a special table with very limited range of ASCII characters.
        The code's data is tested to make sure it fits inside this limited
        range. If all else fails, the data is determined to be of type
        'binary.'
        
        Note, encoding 'kanji' is not yet implemented.
        """
        #See if the data is an integer
        try:
            test = int(content)
            return 'numeric'
        except:
            #Content is not numeric, this is not an error
            pass
        
        #See if that data is alphanumeric based on the standards
        #special ASCII table
        valid_characters = tables.ascii_codes.keys()
        if all(map(lambda x: x in valid_characters, self.data.upper())):
            return 'alphanumeric'
           
        #All of the tests failed. The content can only be binary. 
        return 'binary'

    def _pick_best_fit(self):
        """This method return the smallest possible QR Code version number
        that will fit the specified data with the given error level.
        """
        for version in range(1,41):
            #Get the maximum possible capacity
            capacity = tables.data_capacity[version][self.error][self.mode_num]
            
            #Check the capacity
            if (self.mode_num == tables.modes['binary'] and \
               capacity >= len(self.data.encode('ascii'))) or \
               capacity >= len(self.data):
                return version
        
        raise ValueError('The data will not fit in any QR Code version '
                         'with the given encoding and error level.')
    
    def get_png_size(self, scale):
        """This is method helps users determine what scale to use when creating
        a PNG of this QR code. It is meant mostly to be used in the console
        to help a user figure out what scale to use. It will return an integer
        representing the width and height of the QR code if it was drawn using
        the given scale.
        
        Example:
            >>> code = pyqrcode.QRCode("I don't like spam!")
            >>> print(code.get_png_size(1))
            31
            >>> print(code.get_png_size(5))
            155
        """
        return builder._get_png_size(self.version, scale)
        
    def png(self, file, scale=1, module_color=None, background=None):
        """This method writes the QR Code out as an PNG image. The resulting
        PNG has a bit depth of 1, i.e. it is a black and white file. The
        file parameter is used to specify where to write the image to. It can
        either be an writable stream or a file path.
        
        The scale parameter is sets how large to draw a single module. By
        default one pixel is used to draw a single module. This may make the
        code to small to be read efficiently. Increasing the scale will make
        the code larger. Only integer scales are usable. This method will
        attempt to coerce parameter into an integer (e.g. 2.5 will become 2,
        and '3' will become 3).
        
        The module_color parameter sets what color to use for the encoded
        modules (the black part on most QR Codes). The background parameter
        sets what color to use for the background (the white part on most
        QR Codes). If either parameter is set, then both must be
        set or a ValueError is raised. Colors should be specified as either
        a list or a tuple of length 3 or 4. The components of the list must
        be integers between 0 and 255. The first three member give the RGB
        color. The fourth member gives the alpha component, where 0 is
        transparent and 255 is without transparency. Note, many color
        combinations are unreadable by scanners, so be careful.
        
        This method will write the given file out as a PNG file. Note, it
        depends on the PyPNG module to do this.
        
        Example:
            >>> code = pyqrcode.QRCode('Are you suggesting coconuts migrate?')
            >>> code.png('swallow.png', scale=5)
            >>> code.png('swallow.png', scale=5,
                         black=(0x66, 0x33, 0x0),        #Dark brown
                         white=(0xff, 0xff, 0xff, 0x88)) #50% transparent white
        """
        builder._png(self.code, self.version, file, scale,
                     module_color, background)
    
    def svg(self, file, scale=1, module_color='#000000', background=None):
        """This method writes the QR Code out as an SVG document. The
        code is drawn by drawing only the modules corresponding to a 1. They
        are drawn using a line, such that contiguous modules in a row
        are drawn with a single line. The file parameter is used to
        specify where to write the document to. It can either be an writable
        stream or a file path. The scale parameter is sets how large to draw
        a single module. By default one pixel is used to draw a single
        module. This may make the code to small to be read efficiently.
        Increasing the scale will make the code larger. This method will accept
        fractional scales (e.g. 2.5).
        
        Note, three things are done to make the code more appropriate for
        embedding in a HTML document. The "white" part of the code is actually
        transparent. The code itself has a class of "pyqrcode". The lines
        making up the QR code have a class pyqrline. These should make the code
        easier to style using CSS.
        
        You can also set the colors directly using the module_color and
        background parameters. The module_color parameter sets what color to
        use for the encoded modules (the black part on most QR Codes). The
        background parameter sets what color to use for the background (the
        white part on most QR Codes). The parameters can be set to any valid
        SVG or HTML color. If the background is set to None, then no background
        will be drawn, i.e. the background will be transparent.
        
        Example:
            >>> code = pyqrcode.QRCode('Hello. Uhh, can we have your liver?')
            >>> code.svg('live-organ-transplants.svg', 3)
        """
        builder._svg(self.code, self.version, file, scale,
                     module_color, background)
        
    def text(self):
        """This method returns a text based representation of the QR Code.
        This is useful for debugging purposes. The black modules are represented
        by 1's and the white modules are represented by 0's.
        """
        builder._text(self.code)

if __name__ == '__main__':
    code = QRCode('''This is an example!!''')
    code.png( "best-code.png", scale=4)
