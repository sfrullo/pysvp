import os
from gi.overrides.GObject import new
from builtins import isinstance
os.environ["GST_DEBUG_DUMP_DOT_DIR"] = "/tmp"
os.putenv('GST_DEBUG_DUMP_DOT_DIR', '/tmp')


from os.path import sep

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GstVideo #@UnresolvedImport
GObject.threads_init()
Gst.init(None)

class Media:
    ''' This class represents a Media object. It should be use with a Player to 
    be able to play content. It provides only filesource and decoding 
    functionalities and it's decodebin's src pad must be linked with an external 
    sink pad.
    
    Provides method to easily link/unlink. '''

    
    def on_pad_added(self, decodebin, pad):
        if pad.get_name().startswith('ghost'):
            print(pad.get_name(), ' added to ', decodebin.get_name())
        else: 
            padcaps = pad.query_caps(None)
            structure = padcaps.to_string()
            if structure.startswith('video'):
                if hasattr(self, 'videoghostpad'):
                    self.ghostsrc = Gst.GhostPad.new('ghostvideosrc::' + self.filename, pad)
                    self.ghostsrc.set_active(True)
                    self.decodebin.add_pad(self.ghostsrc)
                    self.ghostsrc.link(self.videoconvert.get_compatible_pad(self.ghostsrc))
                else:
                    sinkpad = self.videoconvert.get_compatible_pad(pad)
                    pad.link(sinkpad)
            else:
                if hasattr(self, 'audioghostpad'):
                    pad.link(self.audioghostpad)
                else:
                    sinkpad = self.audioconvert.get_compatible_pad(pad)
                    pad.link(sinkpad)
                
            
    def __init__(self, sourcefile, audioconvert, videoconvert, n=0):
        self.id = n
        self.location = sourcefile
        self.filename = sourcefile.split(sep)[-1]
        
        self.bin = Gst.Bin.new('bin::'+self.filename)
        self.decodebin = Gst.ElementFactory.make('uridecodebin', 'uridecodebin::' + self.filename)
        self.decodebin.connect('pad-added', self.on_pad_added)
        self.decodebin.set_property('uri', 'file:///' + sourcefile)
        
        self.bin.add(self.decodebin)

        if not audioconvert:
            self.audioconvert = Gst.ElementFactory.make('fakesink', 'fakeaudiosink::' + self.filename)
            self.bin.add(self.audioconvert) 
        else:
            self.audioconvert = audioconvert
            sinkpad = self.audioconvert.get_static_pad('sink')
            self.audioghostpad = Gst.GhostPad.new('ghostpadaudio::'+self.filename, sinkpad)
            self.audioghostpad.set_active(True)
            self.bin.add_pad(self.audioghostpad)
        
        if not videoconvert:
            self.videoconvert = Gst.ElementFactory.make('fakesink', 'fakevideosink::' + self.filename)
            self.bin.add(self.videoconvert)
        else:
            self.videoconvert = videoconvert
            sinkpad = self.videoconvert.get_static_pad('sink')
            self.videoghostpad = Gst.GhostPad.new('ghostpadvideo::'+self.filename, sinkpad)
            self.videoghostpad.set_active(True)
            self.bin.add_pad(self.videoghostpad)

        
        
    def setAudioConvert(self, destination):
        self.audioconvert = destination
            
    def setVideoConvert(self, destination):
        self.videoconvert = destination        

class SimplePlayer:
    
    def on_debug_activate(self, name):
        print('do debug image')
        dotfile = "/tmp/"+name+".dot"
        pdffile = "/tmp/"+name+".pdf"
        if os.access(dotfile, os.F_OK):
            os.remove(dotfile)
        if os.access(pdffile, os.F_OK):
            os.remove(pdffile)
        Gst.debug_bin_to_dot_file(self.pipeline,Gst.DebugGraphDetails.ALL, name)
        try:
            os.system("dot -Tpdf -o " + pdffile + " " + dotfile)
        except os.error:
            print("The debug feature requires graphviz (dot) to be installed.")
            
    class LoadingComponentException(Exception):
        def __init__(self, *arg, **kwarg):
            self.arg = arg
            self.kwarg = kwarg
        def __str__(self):
            print('Error occurred while loading {} component'.format(self.arg[1]))
        
    def __init__(self, xid=None, name='SimplePlayer'):
        ''' Init function of SimplePlayer class'''
        self.__xid = xid
        self.name = name
        
        self.pipeline = Gst.Pipeline('pipeline::' + self.name)
        if not self.pipeline: raise self.LoadingComponentException('pipeline')
        
        # load video and audio component
        self.videoconvert = Gst.ElementFactory.make('videoconvert', 'videoconvert::' + self.name)
        self.videosink = Gst.ElementFactory.make('autovideosink', 'video-output::' + self.name)
        if not (self.videoconvert and self.videosink):
            raise self.LoadingComponentException('video')
        
        self.audioconvert = Gst.ElementFactory.make('audioconvert', 'audioconvert::' + self.name)
        self.audiosink = Gst.ElementFactory.make('autoaudiosink', 'audio-output::' + self.name)
        if not (self.audioconvert and self.audiosink):
            raise self.LoadingComponentException('audio')
    
        # add component to pipeline
        for e in [self.videoconvert, self.videosink, self.audioconvert, self.audiosink]:
            self.pipeline.add(e)
            
        self.videoconvert.link(self.videosink)
        self.audioconvert.link(self.audiosink)

        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self.on_message)
        self.bus.enable_sync_message_emission()
        self.bus.connect('sync-message::element', self.on_sync_message)
    
    # control functions
    def play(self):
        self.pipeline.set_state(Gst.State.PLAYING)

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
        
    def debug(self):
        self.on_debug_activate(self.name + '-debug')

    # callback functions
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

    # getter/setter definition 
    def get_xid(self):
        return self.__xid

    def set_xid(self, value):
        print('Set new xid value:\nPrevious:{} -> New:{}'.format(self.__xid, value))
        self.__xid = value

    def del_xid(self):
        del self.__xid

    xid = property(get_xid, set_xid, del_xid)

    def getMedia(self):
        return self.media

    def setMedia(self, value):
        print('Set new Media: {}'.format(value))
        self.media = Media(value, None, self.videoconvert)
        self.pipeline.add(self.media.bin)


class MultipleMediaPlayer(SimplePlayer):
    ''' This class implements a player that store multiple media.
        It is intended to be use as base class for advance player class '''
    
    def __init__(self, *arg, **kwarg):
        super(MultipleMediaPlayer, self).__init__(*arg, **kwarg)
        

class SwitchableMediaPlayer(MultipleMediaPlayer):
    ''' This class implements a player that accept multiple media
    with the possibility of switch between them'''
    
    def __init__(self, *arg, **kwarg):
        super(SwitchableMediaPlayer, self).__init__(*arg, **kwarg)
        