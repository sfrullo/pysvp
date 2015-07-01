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


class SimplePlayer:
    ''' SimplePlayer class implements a single media player.
    
        basically it provides a pipeline in which there is a bin with ghostpad
        for audio and video streams. 
        Once a media is load with setMedia(path, hasAudio, hasVideo) method, 
        audio and video components are loaded in dependence of hasAudio and hasVideo flags
         
        on playing the Player links the src ghostpad of the loaded media and
        the self's sink ghostpad.
    '''
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
    # Init func
    #---------------------------------------------------------------------------
    def __init__(self, xid=None, name='SimplePlayer'):
        ''' Init function of SimplePlayer class'''
        self.xid = xid
        self.name = name
        
        self.pipeline = Gst.Pipeline('pipeline::' + self.name)
        if not self.pipeline: raise self.LoadingComponentException('pipeline')
        
        self.bin = Gst.Bin('bin::' + self.name)
        self.bin.connect('pad-added', self.on_pad_added)
        if not self.bin: raise self.LoadingComponentException('bin')
    
        # add ghostpad to bin
        self.videoghostsink = Gst.GhostPad.new_no_target('videoghostsink::' + self.name, Gst.PadDirection.SINK)
        self.videoghostsink.connect('linked', self.on_pad_linkded)
        self.bin.add_pad(self.videoghostsink)
        
        self.audioghostsink = Gst.GhostPad.new_no_target('audioghostsink::' + self.name, Gst.PadDirection.SINK)
        self.audioghostsink.connect('linked', self.on_pad_linkded)
        self.bin.add_pad(self.audioghostsink)
      
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
    def addVideoComponent(self):
        # load video and audio component
        self.videoconvert = Gst.ElementFactory.make('videoconvert', 'videoconvert::' + self.name)
        self.videosink = Gst.ElementFactory.make('autovideosink', 'video-output::' + self.name)
        if not (self.videoconvert and self.videosink):
            raise self.LoadingComponentException('video')
        self.bin.add(self.videoconvert)
        self.bin.add(self.videosink)
        self.videoconvert.link(self.videosink)
        
    def addAudioComponent(self):
        self.audioconvert = Gst.ElementFactory.make('audioconvert', 'audioconvert::' + self.name)
        self.audiosink = Gst.ElementFactory.make('autoaudiosink', 'audio-output::' + self.name)
        if not (self.audioconvert and self.audiosink):
            raise self.LoadingComponentException('audio')
        self.bin.add(self.audioconvert)
        self.bin.add(self.audiosink)
        self.audioconvert.link(self.audiosink)
   
    
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
        
    def rew(self):
        self.pipeline.set_state(Gst.State.PAUSED)
        rc, pos = self.pipeline.query_position(Gst.Format.TIME)
        newpos = pos - (10 * 10 ** 8)
        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, newpos)
        self.pipeline.set_state(Gst.State.PLAYING)
        return
        
    def ffwd(self):
        self.pipeline.set_state(Gst.State.PAUSED)
        rc, pos = self.pipeline.query_position(Gst.Format.TIME)
        newpos = pos + (10 * 10 ** 8)
        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, newpos)
        self.pipeline.set_state(Gst.State.PLAYING)
        return
        
    def debug(self):
        self.on_debug_activate(self.name + '-debug')

    #---------------------------------------------------------------------------
    # callback functions
    #---------------------------------------------------------------------------
    def on_message(self, bus, msg):
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
            imagesink = msg.src
            imagesink.set_property('force-aspect-ratio', True)
            imagesink.set_window_handle(self.getXid())
     
    def on_pad_added(self, decodebin, pad):
        print(pad.get_name(), ' added to ', decodebin.get_name())
    
    def on_pad_linkded(self, pad, src):
        print(src.get_name(), ' linked to ' ,pad.get_name())
        if pad.get_name().startswith('video'):
            self.videoghostsink.set_target(self.videoconvert.get_static_pad('sink'))
        else:
            self.audioghostsink.set_target(self.audioconvert.get_static_pad('sink'))
    
    #---------------------------------------------------------------------------
    # getter/setter definition 
    #---------------------------------------------------------------------------
    def getXid(self):
        return self.xid

    def setXid(self, value):
        print('Set new xid value:\nPrevious:{} -> New:{}'.format(self.__xid, value))
        self.xid = value

    def getMedia(self):
        return self.media

    def setMedia(self, filepath, hasAudio=None, hasVideo=None):
        # Create audio/video component
        if hasAudio: self.addAudioComponent()
        if hasVideo: self.addVideoComponent()
        
        print('Set new Media: {} '.format(filepath), 
              'with audio ' if hasAudio else 'with no audio ',
              'with video' if hasVideo else 'with no video')
        self.media = Media(filepath, hasAudio, hasVideo)
        self.pipeline.add(self.media.getBin())


class MultipleMediaPlayer:
    ''' This class implements a player that store multiple media.
        It is intended to be use as base class for advance player class '''
    
    def __init__(self, *arg, **kwarg):
        
        mediadict = dict()

class SwitchableMediaPlayer(MultipleMediaPlayer):
    ''' This class implements a player that accept multiple media
    with the possibility of switch between them'''
    
    def __init__(self, *arg, **kwarg):
        super(SwitchableMediaPlayer, self).__init__(*arg, **kwarg)
        
