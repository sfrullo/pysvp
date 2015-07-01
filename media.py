from os.path import sep

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GstVideo  # @UnresolvedImport
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
            # video pad
            if structure.startswith('video'):
                videofakesink = self.bin.get_by_name('fakevideosink::' + self.filename)
                if videofakesink:
                    # è presente un videofakesink, la traccia video non deve essere mostrata
                    # quindi colleghiamo il pad al fakesink
                    sinkpad = videofakesink.get_compatible_pad(pad)
                    pad.link(sinkpad)
                else:
                    if not hasattr(self, 'videoghostsrc'):
                        self.videoghostsrc = Gst.GhostPad.new('ghostpadvideosrc::' + self.filename, pad)
                        self.videoghostsrc.set_active(True)
                        self.bin.add_pad(self.videoghostsrc)
                    self.videoghostsrc.link(self.videosink)
            # audio pad
            else:
                audiofakesink = self.bin.get_by_name('fakeaudiosink::' + self.filename)
                if audiofakesink:
                    # è presente un audiofakesink, la traccia audio non deve essere mostrata
                    # quindi colleghiamo il pad al fakesink
                    sinkpad = audiofakesink.get_compatible_pad(pad)
                    pad.link(sinkpad)
                else:
                    if not hasattr(self,'audioghostsrc'):
                        self.audioghostsrc = Gst.GhostPad.new('ghostpadaudiosrc::' + self.filename, pad)
                        self.audioghostsrc.set_active(True)
                        self.bin.add_pad(self.audioghostsrc)
                    self.audioghostsrc.link(self.audiosink)      
                    
    def __init__(self, sourcefile, audiosink, videosink, n=0):
        self.id = n
        self.location = sourcefile
        self.filename = sourcefile.split(sep)[-1]
        
        self.bin = Gst.Bin.new('bin::' + self.filename)
        self.bin.connect('pad-added', self.on_pad_added)
        
        self.decodebin = Gst.ElementFactory.make('uridecodebin', 'uridecodebin::' + self.filename)
        self.decodebin.connect('pad-added', self.on_pad_added)
        self.decodebin.set_property('uri', 'file:///' + sourcefile)
        self.decodebin.set_state(Gst.State.READY)
        self.bin.add(self.decodebin)

        if not audiosink:
            # non è specificato un audiosink: si crea un fakesink e si aggiunge al bin
            self.audiosink = Gst.ElementFactory.make('fakesink', 'fakeaudiosink::' + self.filename)
            self.bin.add(self.audiosink) 
        else:
            self.audiosink = audiosink
        
        if not videosink:
            # non è specificato un videosink: si crea un fakesink e si aggiunge al bin
            self.videosink = Gst.ElementFactory.make('fakesink', 'fakevideosink::' + self.filename)
            self.bin.add(self.videosink)
        else:
            self.videosink = videosink

    def setAudioConvert(self, destination):
        self.audioconvert = destination
            
    def setVideoConvert(self, destination):
        self.videoconvert = destination
    
    def on_stop(self):
        pass              