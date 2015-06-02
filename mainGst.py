import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GstVideo  # @UnresolvedImport
#print(Gst.version())


import tkinter as Tk
from PIL import Image, ImageTk
from os import path
from pprint import pprint

GObject.threads_init()
Gst.init(None)
     
uri1 = 'file://' + path.join(path.dirname(path.abspath(__file__)), 'v1.avi')
uri2 = 'file://' + path.join(path.dirname(path.abspath(__file__)), 'v2.avi')
   
class App(Tk.Frame):
    
    def __init__(self, *arg, **kwarg):
        super(App, self).__init__(*arg, **kwarg)
        self.config(bd=30)
        self.grid()
        
        self.createWidgets()
        self.init_player()
    
    def on_play(self):
        self.xid1 = self.videocontainer.winfo_id()
        self.xid2 = self.video2container.winfo_id()
        self.pipeline_vid1.set_state(Gst.State.PLAYING)
        self.pipeline_vid2.set_state(Gst.State.PLAYING)
    
    
    def on_stop(self):
        self.pipeline_vid1.set_state(Gst.State.NULL)
        self.pipeline_vid2.set_state(Gst.State.NULL)
    
    
    def createWidgets(self):
        
        self.videocontainer = Tk.Frame(self, bg='white')
        self.videocontainer.configure(width=250, height=250)
        self.videocontainer.anchor(Tk.CENTER)
        self.videocontainer.grid(column = 0, row=0)
        
        self.video2container = Tk.Frame(self, bg='white')
        self.video2container.configure(width=250, height=250)
        self.video2container.anchor(Tk.CENTER)
        self.video2container.grid(column = 1, row=0)
        
        self.buttoncontainer  = Tk.LabelFrame(relief='flat')
        self.buttoncontainer.grid(column = 0, row=1)
        self.playbutton = Tk.Button(self.buttoncontainer, text='Play', command=self.on_play)
        self.playbutton.grid(column=0, row=0)
        self.stopbutton = Tk.Button(self.buttoncontainer, text='Stop', command=self.on_stop)
        self.stopbutton.grid(column = 1, row=0)
        
    
    def on_sync_message(self, bus, msg):
        if msg.get_structure().get_name() == 'prepare-window-handle':
            print('prepare-window-handle')
            if bus.get_name() == 'vid1':
                msg.src.set_window_handle(self.xid1)
            else:
                msg.src.set_window_handle(self.xid2)
    
    def on_error(self, bus, msg):
        print('on_error():', msg.parse_error())
    
    
    def on_eos(self, bus, msg):
        print('on_eos(): seeking to start of video')
        self.pipeline_vid1.seek_simple(
            Gst.Format.TIME,        
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            0
        )
        self.pipeline_vid2.seek_simple(
            Gst.Format.TIME,        
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            0
        )
    
    
    def init_player(self):
                
        self.pipeline_vid1 = Gst.Pipeline()
        self.pipeline_vid2 = Gst.Pipeline()
        
        self.bus1 = self.pipeline_vid1.get_bus()
        self.bus1.set_name('vid1')
        self.bus2 = self.pipeline_vid2.get_bus()
        self.bus2.set_name('vid2')
        
        for b in [self.bus1, self.bus2]: 
            b.add_signal_watch()
            b.connect('message::eos', self.on_eos)
            b.connect('message::error', self.on_error)
        
            b.enable_sync_message_emission()
            b.connect('sync-message::element', self.on_sync_message)
        
        self.playbin_vid1 = Gst.ElementFactory.make('playbin', None)
        self.playbin_vid2 = Gst.ElementFactory.make('playbin', None)
        self.pipeline_vid1.add(self.playbin_vid1)
        self.pipeline_vid2.add(self.playbin_vid2)
        
        self.playbin_vid1.set_property('uri', uri1)
        self.playbin_vid2.set_property('uri', uri2)
        

if __name__ == '__main__':
    app = App()
    app.mainloop()
