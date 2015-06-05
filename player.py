import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GstVideo  # @UnresolvedImport
#print(Gst.version())


GObject.threads_init()
Gst.init(None)


class Player:
    
    def __init__(self, xid=None, name='Player'):
        self.__xid = xid
        self.__media = None
        self.name = name
        
        self.pipeline = Gst.Pipeline('pipeline')
        
        self.source = Gst.ElementFactory.make('filesrc', 'file-source')   
            
        self.decodebin = Gst.ElementFactory.make('decodebin', 'decodebin')
        self.decodebin.connect('pad-added', self.on_pad_added)
        
        self.videoconvert = Gst.ElementFactory.make('videoconvert', 'videoconvert')
        self.videosink = Gst.ElementFactory.make('autovideosink', 'video-output')
        
        # ADD TO PIPE
        for e in [self.source, self.decodebin, self.videoconvert, self.videosink]:
            self.pipeline.add(e)

        # LINKING TOGHETER
        self.source.link(self.decodebin)
        # decodebin link to videoconvert through on_pad_added() callback
        self.videoconvert.link(self.videosink)

        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self.on_message)
        self.bus.enable_sync_message_emission()
        self.bus.connect('sync-message::element', self.on_sync_message)
    
    # CONTROL FUNCTIONS
    def play(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        print(self.pipeline.get_state(10)[1])
        
    def stop(self):
        self.pipeline.set_state(Gst.State.NULL)
        
    def rew(self):
        rc, pos = self.pipeline.query_position(Gst.Format.TIME)
        newpos = pos - (10 * 10**8)
        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, newpos)
    
    def ffwd(self):
        rc, pos = self.pipeline.query_position(Gst.Format.TIME)
        newpos = pos + (10 * 10**8)
        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, newpos)

    # CALLBACK FUNCTIONS
    def on_message(self, bus, msg):
        t = msg.type
        if t == Gst.MessageType.EOS:
            print(self.name, 'on_eos(): seeking to start of video')
            self.stop()
        elif t == Gst.MessageType.ERROR:
            self.stop()
            print(self.name, 'on_error():', msg.parse_error())
    
    def on_sync_message(self, bus, msg):
        if msg.get_structure().get_name() == 'prepare-window-handle':
            print('prepare-window-handle')
            imagesink = msg.src
            imagesink.set_property('force-aspect-ratio', True)
            imagesink.set_window_handle(self.get_xid())
        
    def on_pad_added(self, decodebin, pad):                        
        sink = self.videoconvert.get_compatible_pad(pad)
        if sink:
            pad.link(sink)
        else:
            pass
         
    # GETTER/SETTER DEFINITION 
    def get_xid(self):
        return self.__xid

    def set_xid(self, value):
        print('Set new xid value:\nPrevious:{} -> New:{}'.format(self.__xid, value))
        self.__xid = value

    def del_xid(self):
        del self.__xid

    xid = property(get_xid, set_xid, del_xid)


    def get_media(self):
        return self.__media

    def set_media(self, value):
        print('Set new Media: {}'.format(value))
        self.__media = value
        self.source.set_property('location', value)


    def del_media(self):
        del self.__media

    media = property(get_media, set_media, del_media)
