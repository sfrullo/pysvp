import os
os.environ["GST_DEBUG_DUMP_DOT_DIR"] = "/tmp"
os.putenv('GST_DEBUG_DUMP_DOT_DIR', '/tmp')


from os.path import sep
from media import Media

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GstVideo  # @UnresolvedImport
GObject.threads_init()
Gst.init(None)

class BasePlayer:
    
    #---------------------------------------------------------------------------
    # Exception
    #---------------------------------------------------------------------------
    class LoadingComponentException(Exception):
        def __init__(self, *arg, **kwarg):
            self.arg = arg
            self.kwarg = kwarg
        def __str__(self):
            print('Error occurred while loading {} component'.format(self.arg[1]))
            
    #---------------------------------------------------------------------------
    # Init
    #---------------------------------------------------------------------------
    def __init__(self, name):
        
        self.name = name
        
        self.pipeline = Gst.Pipeline('pipeline::' + self.name)
        if not self.pipeline: raise self.LoadingComponentException('pipeline')
        
        self.bin = Gst.Bin('bin::' + self.name)
        self.bin.connect('pad-added', self.on_pad_added)
        if not self.bin: raise self.LoadingComponentException('bin')
      
        # ..and add bin to pipeline
        self.pipeline.add(self.bin)

        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self.on_message)
        self.bus.enable_sync_message_emission()
        self.bus.connect('sync-message::element', self.on_sync_message)
    
    
    #---------------------------------------------------------------------------
    # Methods
    #---------------------------------------------------------------------------
    def addComponent(self, mediatype):
        '''
        Add audio/video convert and autosink to the bin of the player.
        
        input:
            mediatype : specifies what kind of components have to be made.
                        It could be "video" or "audio"
        return:
            convert:    the specified mediatype convert
            sink:       the specified mediatype autosink
        '''
        if mediatype not in ['video', 'audio']:
            raise AttributeError(mediatype, 'is not a valid type. mediatype can only be "video" or "audio"')
        convertname = mediatype + 'convert'
        sinkname = 'auto' + mediatype + 'sink'
        convert = Gst.ElementFactory.make(convertname, mediatype + 'convert::' + self.name)
        sink = Gst.ElementFactory.make(sinkname, mediatype + 'sink::' + self.name)
        if not (convert and sink):
            raise self.LoadingComponentException(mediatype)
        self.bin.add(convert)
        self.bin.add(sink)
        convert.link(sink)
        return convert, sink
        
    
    #---------------------------------------------------------------------------
    # control functions
    #---------------------------------------------------------------------------
    def play(self):
        self.pipeline.set_state(Gst.State.PLAYING)

    def stop(self):
        self.pipeline.set_state(Gst.State.NULL)
    
    def pause(self):
        self.pipeline.set_state(Gst.State.PAUSED)
    
    def rew(self):
        rc, pos = self.pipeline.query_position(Gst.Format.TIME)
        newpos = pos - (10 * 10 ** 8)
        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, newpos)
        return
        
    def ffwd(self):
        rc, pos = self.pipeline.query_position(Gst.Format.TIME)
        newpos = pos + (10 * 10 ** 8)
        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, newpos)
        return
        
    def debug(self):
        self.on_debug_activate(self.name + '-debug')
    
    
    #---------------------------------------------------------------------------
    # callback functions
    #---------------------------------------------------------------------------
    def on_message(self, bus, msg):
        print(bus, msg)
        t = msg.type
        print(t)
        if t == Gst.MessageType.EOS:
            print(self.name, 'on_eos(): seeking to start of video')
            self.stop()
        elif t == Gst.MessageType.ERROR:
            self.stop()
            print(self.name, 'on_error():', msg.parse_error())
        elif t == Gst.MessageType.STATE_CHANGED:
            print(self.name, 'state changed:', msg.parse_state_changed())
    
    def on_sync_message(self, bus, msg):
        if msg.get_structure().get_name() == 'prepare-window-handle':
            print('prepare-window-handle')
            self.imagesink = msg.src
            print(self.imagesink)
            self.imagesink.set_property('force-aspect-ratio', True)
            self.imagesink.set_window_handle(self.getXid())
     
    def on_pad_added(self, decodebin, pad):
        print(pad.get_name(), ' added to ', decodebin.get_name())
    
    def on_pad_linkded(self, pad, src):
        print(src.get_name(), ' linked to ' , pad.get_name())
        if pad.get_name().startswith('video'):
            self.videoghostsink.set_target(self.videoconvert.get_static_pad('sink'))
        else:
            self.audioghostsink.set_target(self.audioconvert.get_static_pad('sink'))
            
            
    #---------------------------------------------------------------------------
    # Debug Function
    #---------------------------------------------------------------------------
    def on_debug_activate(self, name):
        print('do debug image')
        dotfile = "/tmp/" + name + ".dot"
        pdffile = "/tmp/" + name + ".pdf"
        if os.access(dotfile, os.F_OK):
            os.remove(dotfile)
        if os.access(pdffile, os.F_OK):
            os.remove(pdffile)
        Gst.debug_bin_to_dot_file(self.pipeline, Gst.DebugGraphDetails.ALL, name)
        try:
            os.system("dot -Tpdf -o " + pdffile + " " + dotfile)
        except os.error:
            print("The debug feature requires graphviz (dot) to be installed.")


class SimplePlayer(BasePlayer):
    ''' SimplePlayer class implements a single media player.
    
        basically it provides a pipeline in which there is a bin with ghostpad
        for audio and video streams. 
        Once a media is load with setMedia(path, hasAudio, hasVideo) method, 
        audio and video components are loaded in dependence of hasAudio and hasVideo flags
         
        on playing the Player links the src ghostpad of the loaded media and
        the self's sink ghostpad.
    '''
       
    #---------------------------------------------------------------------------
    # Init func
    #---------------------------------------------------------------------------
    def __init__(self, xid=None, name='SimplePlayer'):
        ''' Init function of SimplePlayer class'''
        super(SimplePlayer, self).__init__(name)
        self.xid = xid
        
        # create and add ghostpad to bin
        self.videoghostsink = Gst.GhostPad.new_no_target('videoghostsink::' + self.name, Gst.PadDirection.SINK)
        self.videoghostsink.connect('linked', self.on_pad_linkded)
        self.bin.add_pad(self.videoghostsink)
        
        self.audioghostsink = Gst.GhostPad.new_no_target('audioghostsink::' + self.name, Gst.PadDirection.SINK)
        self.audioghostsink.connect('linked', self.on_pad_linkded)
        self.bin.add_pad(self.audioghostsink)
            
    #---------------------------------------------------------------------------
    # Methods
    #---------------------------------------------------------------------------
    def changeXid(self, newXid):
        self.__oldXid = self.getXid()
        self.setXid(newXid)
        # force the imagesink to use new Xid
        if hasattr(self, 'imagesink'):
            self.imagesink.prepare_window_handle()
            
    
    #---------------------------------------------------------------------------
    # control functions
    #---------------------------------------------------------------------------
    def play(self):
        print(self.pipeline.current_state is Gst.State.PLAYING)
        if not self.pipeline.current_state is Gst.State.PLAYING:
            if self.media.getAudioGhostPad():
                self.media.getAudioGhostPad().link(self.audioghostsink)
            if self.media.getVideoGhostPad():
                self.media.getVideoGhostPad().link(self.videoghostsink)
            self.pipeline.set_state(Gst.State.PLAYING)

    def stop(self):
        self.pipeline.set_state(Gst.State.NULL)
        if self.media.getAudioGhostPad():
            self.media.getAudioGhostPad().unlink(self.audioghostsink)
        if self.media.getVideoGhostPad():
            self.media.getVideoGhostPad().unlink(self.videoghostsink)
    
    
    #---------------------------------------------------------------------------
    # getter/setter definition 
    #---------------------------------------------------------------------------
    def getXid(self):
        return self.xid

    def setXid(self, value):
        print('Set new xid value:\nPrevious:{} -> New:{}'.format(self.xid, value))
        self.xid = value
            

    def getMedia(self):
        return self.media

    def setMedia(self, filepath, hasAudio=None, hasVideo=None):
        # Create audio/video component
        if hasAudio: 
            self.audioconvert, self.audiosink = self.addComponent('audio')
        if hasVideo: 
            self.videoconvert, self.videosink = self.addComponent('video')
        
        print('Set new Media: {} '.format(filepath),
              'with audio ' if hasAudio else 'with no audio ',
              'with video' if hasVideo else 'with no video')
        self.media = Media(filepath, hasAudio, hasVideo)
        self.pipeline.add(self.media.getBin())


class MultipleMediaPlayer(BasePlayer):
    ''' This class implements a player that stores and plays multiple media
    synchronously, one with it's own xid.
    
    It implements BasicPlayer. A pipeline is instantiated for the top level control 
    and needed components are made based on loaded media.
    
    
    '''
    
    def __init__(self, name=None):
        super(MultipleMediaPlayer, self).__init__(name)
        
        self.playlist = dict()
        
    def addMediaToPlaylist(self, path, hasAudio=None, hasVideo=None):
        
        name = path.split(sep)[-1]
        self.playlist[name] = Media(path, hasAudio, hasVideo)
        print(path, ' added to playlist of ', self.name)
    
    def removeMediaFromPlaylist(self, name):
        if name in self.playlist.values():
            self.playlist.pop(name)
        else:
            print(name, ' not in playlist of ', self.name)
    
class SwitchableMediaPlayer(MultipleMediaPlayer):
    ''' This class implements a player that accept multiple media
    with the possibility of switch between them'''
    
    def __init__(self, *arg, **kwarg):
        super(SwitchableMediaPlayer, self).__init__(*arg, **kwarg)
        