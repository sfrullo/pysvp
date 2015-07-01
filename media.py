from os.path import sep

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GstVideo  # @UnresolvedImport
GObject.threads_init()
Gst.init(None)

class Media:
    ''' This class represents a Media object. It should be use with a Player to 
    be able to play content. It provides only filesource and decoding 
    functionalities.
    Provide ghostpad for audio and video streams in dependency of hasAudio/hasVideo
    boolean parameter of constructor
    
    Provides getter and setter. '''

    def on_pad_added(self, decodebin, pad):
        if pad.get_name().startswith('ghost'):
            print(pad.get_name(), ' added to ', decodebin.get_name())
        else: 
            padcaps = pad.query_caps(None)
            structure = padcaps.to_string()
            # video pad
            if structure.startswith('video'):
                if hasattr(self, 'videoghostsrc'): self.videoghostsrc.set_target(pad)
            # audio pad
            else:
                if hasattr(self, 'audioghostsrc'): self.audioghostsrc.set_target(pad)
                
    def __init__(self, sourcefile, hasAudio, hasVideo, n=0):
        self.id = n
        self.location = sourcefile
        self.filename = sourcefile.split(sep)[-1]
        
        self.bin = Gst.Bin.new('bin::' + self.filename)
        self.bin.connect('pad-added', self.on_pad_added)
        
        self.decodebin = Gst.ElementFactory.make('uridecodebin', 'uridecodebin::' + self.filename)
        self.decodebin.connect('pad-added', self.on_pad_added)
        self.decodebin.set_property('uri', 'file:///' + sourcefile)
        self.decodebin.set_state(Gst.State.PAUSED)
        self.bin.add(self.decodebin)

        if hasAudio:
            self.audioghostsrc = Gst.GhostPad.new_no_target('ghostpadaudiosrc::' + self.filename, Gst.PadDirection.SRC)
            self.audioghostsrc.set_active(True)
            self.bin.add_pad(self.audioghostsrc)
                   
        if hasVideo:
            self.videoghostsrc = Gst.GhostPad.new_no_target('ghostpadvideosrc::' + self.filename, Gst.PadDirection.SRC)
            self.videoghostsrc.set_active(True)
            self.bin.add_pad(self.videoghostsrc)
            
    #---------------------------------------------------------------------------
    # getter/setter
    #---------------------------------------------------------------------------

    def getId(self): return self.id
    def getLocation(self): return self.location
    def getFilename(self): return self.filename
    def getBin(self):return self.bin

    def getVideoGhostPad(self):
        return None if not hasattr(self, 'videoghostsrc') else self.videoghostsrc
    
    def getAudioGhostPad(self):
        return None if not hasattr(self, 'audioghostsrc') else self.audioghostsrc
        