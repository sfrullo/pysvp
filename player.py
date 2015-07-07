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
        self.bus.enable_sync_message_emission()
        self.bus.connect('sync-message::element', self.on_sync_message)
        self.bus.add_watch(0, self.on_message, None)
        self.bus.unref()
    
    #---------------------------------------------------------------------------
    # Methods
    #---------------------------------------------------------------------------
    def addMediaComponent(self, mediatype, idname=''):
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
        convert = Gst.ElementFactory.make(convertname, mediatype + 'convert:' + idname + ':' + self.name)
        sink = Gst.ElementFactory.make(sinkname, mediatype + 'sink:' + idname + ':' + self.name)
        if not convert or not sink:
            raise self.LoadingComponentException(mediatype)
        self.bin.add(convert)
        self.bin.add(sink)
        convert.link(sink)
        return convert, sink
    
    def addGhostPad(self, mediatype, padtype, idname=''):
        '''
        Add audio/video ghostpad to the bin of the player.
        
        input:
            mediatype : specifies what kind of components have to be made.
                        It could be "video" or "audio"
            padtype: specifies what direction the pad has to have. 
                        Admit "src" or "sink"
        return:
            ghostpad:   the specified direction mediatype ghostpad
        '''
        name = mediatype + 'ghost' + padtype + ':' + idname + ':' + self.name
        if padtype not in ['sink', 'src']:
            raise TypeError(padtype, ' is not a valid ghostpad type')
        else:
            padtype = Gst.PadDirection.SINK if padtype == 'sink' else Gst.PadDirection.SRC
        ghostpad = Gst.GhostPad.new_no_target(name, padtype)
        ghostpad.connect('linked', self.on_pad_linkded)
        self.bin.add_pad(ghostpad)
        return ghostpad
        
    
    #---------------------------------------------------------------------------
    # control functions
    #---------------------------------------------------------------------------
    def play(self):
        return self.pipeline.set_state(Gst.State.PLAYING)

    def stop(self):
        return self.pipeline.set_state(Gst.State.NULL)
    
    def pause(self):
        return self.pipeline.set_state(Gst.State.PAUSED)
    
    def rew(self):
        rc, pos = self.pipeline.query_position(Gst.Format.TIME)
        newpos = pos - (10 * 10 ** 8)
        return self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, newpos)
             
    def ffwd(self):
        rc, pos = self.pipeline.query_position(Gst.Format.TIME)
        newpos = pos + (10 * 10 ** 8)
        return self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, newpos)
        
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
     
    def on_pad_added(self, element, pad):
        print(pad.get_name(), ' added to ', element.get_name())
        
        
    def on_sync_message(self, bus, msg):
        print('in basic', end=' ')
        pass
            
            
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
        self.videoghostsink = self.addGhostPad('video', 'sink')
        self.audioghostsink = self.addGhostPad('audio', 'sink')
    
    
    #---------------------------------------------------------------------------
    # Callback
    #---------------------------------------------------------------------------
    def on_sync_message(self, bus, msg):
        if msg.get_structure().get_name() == 'prepare-window-handle':
            print('prepare-window-handle')
            self.imagesink = msg.src
            print(self.imagesink)
            self.imagesink.set_property('force-aspect-ratio', True)
            self.imagesink.set_window_handle(self.getXid())


    def on_pad_linkded(self, pad, src):
        print(src.get_name(), ' linked to ' , pad.get_name())
        if pad.get_name().startswith('video'):
            self.videoghostsink.set_target(self.videoconvert.get_static_pad('sink'))
        else:
            self.audioghostsink.set_target(self.audioconvert.get_static_pad('sink'))
    
    
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
        print('{} already in playing state'.format(self.name) 
              if self.pipeline.current_state is Gst.State.PLAYING 
              else 'set {} to playing state'.format(self.name))
        if not self.pipeline.current_state is Gst.State.PLAYING:
            if self.media.getAudioGhostPad():
                self.media.getAudioGhostPad().link(self.audioghostsink)
            if self.media.getVideoGhostPad():
                self.media.getVideoGhostPad().link(self.videoghostsink)
            return self.pipeline.set_state(Gst.State.PLAYING)

    def stop(self):
        print('{} is not playing'.format(self.name) 
              if self.pipeline.current_state is Gst.State.NULL 
              else 'set {} to null state'.format(self.name))
        self.pipeline.set_state(Gst.State.NULL)
        if self.media.getAudioGhostPad():
            self.media.getAudioGhostPad().unlink(self.audioghostsink)
        if self.media.getVideoGhostPad():
            return self.media.getVideoGhostPad().unlink(self.videoghostsink)
    
    
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

    def setMedia(self, filepath, hasAudio=True, hasVideo=True):
        # Create audio/video component
        name = filepath.split(sep)[-1]
        if hasAudio: 
            self.audioconvert, self.audiosink = self.addMediaComponent('audio', idname=name)
        if hasVideo: 
            self.videoconvert, self.videosink = self.addMediaComponent('video', idname=name)
        
        print('Set new Media: {} '.format(filepath),
              'with audio ' if hasAudio else 'with no audio ',
              'with video' if hasVideo else 'with no video')
        self.media = Media(filepath, hasAudio, hasVideo)
        self.pipeline.add(self.media.getBin())


class MultipleMediaPlayer(BasePlayer):
    ''' This class implements a player that stores and plays multiple media
    synchronously, one with it's own xid.
    
    It implements BasicPlayer. A pipeline is instantiated for the top level control 
    and needed components are made based on loaded media.'''

    class PlaylistElement:
        def __init__(self, media, videocomponent, audiocomponent, xid=None):
            self.media = media
            self.xid = xid
            self.imagesink = None
            if videocomponent:
                self.videoconvert = videocomponent[0]
                self.videosink = videocomponent[1]
            if audiocomponent:
                self.audioconvert = audiocomponent[0]
                self.audiosink = audiocomponent[1]
             
        def getFilename(self):     
            return self.media.getFilename()
        
        def getXid(self):
            return self.xid
            
        def setXid(self, value):
            self.__oldxid = self.xid
            self.xid = value

        def getImagesink(self):
            return self.imagesink

        def setImagesink(self, value):
            self.imagesink = value
    

    #---------------------------------------------------------------------------
    # Initialization
    #---------------------------------------------------------------------------
    def __init__(self, name=None):
        super(MultipleMediaPlayer, self).__init__(name)
        self.playlist = dict()
        
    #---------------------------------------------------------------------------
    # Methods
    #---------------------------------------------------------------------------
    def addMediaToPlaylist(self, path, hasAudio=True, hasVideo=True):
        filename = path.split(sep)[-1]
        if hasVideo:
            self.addGhostPad('video', 'sink', idname=filename)
            videocomponent = self.addMediaComponent('video', idname=filename)
        else:
            videocomponent = None
        
        if hasAudio:
            self.addGhostPad('audio', 'sink', idname=filename)
            audiocomponent = self.addMediaComponent('audio', idname=filename)
        else: 
            audiocomponent = None
        
        media = Media(path, hasAudio, hasVideo)
        self.playlist[filename] = MultipleMediaPlayer.PlaylistElement(media, videocomponent, audiocomponent)
        print(path, ' added to playlist of ', self.name)
        self.pipeline.add(media.getBin())
    
    def removeMediaFromPlaylist(self, name):
        if name in self.playlist.values():
            self.playlist.pop(name)
        else:
            print(name, ' not in playlist of ', self.name)
            
    def getMediaXid(self, media):
        name = media.split(sep)[-1]
        try:
            xid = self.playlist[name].getXid()
            return xid
        except AttributeError as e:
            print(e)
            return
        
    def setMediaXid(self, media, xid):
        name = media.split(sep)[-1]
        try:
            self.playlist[name].setXid(xid)
            for m in self.playlist.values():
                m.getImagesink().prepare_window_handle()
        except AttributeError as e:
            print(e)
            return
    
    
    #---------------------------------------------------------------------------
    # Callbacks
    #---------------------------------------------------------------------------
    def on_pad_linkded(self, pad, src):
        print(src.get_name(), ' linked to ', pad.get_name())
        sinkpad, filename, parent = pad.get_name().split(':')
        if sinkpad.startswith('video'):
            convertname = 'videoconvert:' + filename + ':' + parent
        else:
            convertname = 'audioconvert:' + filename + ':' + parent
        convertpad = self.bin.get_by_name(convertname).get_static_pad('sink')
        pad.set_target(convertpad)
        print(pad.get_name(), ' linked to ', convertname)
        
    def on_sync_message(self, bus, msg):
        print('in multiplayer', end=' ')
        if msg.get_structure().get_name() == 'prepare-window-handle':
            imagesink = msg.src
            medianame = imagesink.get_name().split(':')[1]
            if self.playlist[medianame].getXid():
                print('prepare-window-handle for:', medianame)
                imagesink.set_property('force-aspect-ratio', True)
                imagesink.set_window_handle(self.playlist[medianame].getXid())
            else:
                print(medianame, 'doesn\'t have an associated xid.')
            self.playlist[medianame].setImagesink(imagesink)
    
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
                
    #---------------------------------------------------------------------------
    # control functions
    #---------------------------------------------------------------------------
    def play(self):
        if not self.pipeline.current_state is Gst.State.PLAYING:
            for media in self.playlist.values():
                videosinkpad = self.bin.get_static_pad('videoghostsink:{}:{}'.format(media.getFilename(), self.name))
                if videosinkpad:
                    media.media.getVideoGhostPad().link(videosinkpad)
                audiosinkpad = self.bin.get_static_pad('audioghostsink:{}:{}'.format(media.getFilename(), self.name))
                if audiosinkpad:
                    media.media.getAudioGhostPad().link(audiosinkpad)
            return self.pipeline.set_state(Gst.State.PLAYING)

    def stop(self):
        self.pipeline.set_state(Gst.State.NULL)
        for media in self.playlist.values():
            audiosinkpad = self.bin.get_static_pad('audioghostsink:{}:{}'.format(media.getFilename(), self.name))
            if audiosinkpad:
                media.media.getAudioGhostPad().unlink(audiosinkpad)
            videosinkpad = self.bin.get_static_pad('videoghostsink:{}:{}'.format(media.getFilename(), self.name))
            if videosinkpad:
                media.media.getVideoGhostPad().unlink(videosinkpad)
                
    
class SwitchableMediaPlayer(MultipleMediaPlayer):
    ''' This class implements a player that accept multiple media
    with the possibility of switch between them'''
    
    def __init__(self, *arg, **kwarg):
        super(SwitchableMediaPlayer, self).__init__(*arg, **kwarg)
        
