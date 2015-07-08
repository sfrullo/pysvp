import tkinter as Tk
from os import path
from pprint import pprint

from player import *
from time import sleep
     
media = {1:path.join(path.dirname(path.abspath(__file__)), 'v1.avi'),
         2:path.join(path.dirname(path.abspath(__file__)), 'v2.avi'),
         3:path.join(path.dirname(path.abspath(__file__)), 'v4.avi')}
   
class App(Tk.Frame):
    
    def __init__(self, *arg, **kwarg):
        super(App, self).__init__(*arg, **kwarg)
        self.config(bd=30)
        self.grid(sticky=Tk.N+Tk.S+Tk.E+Tk.W)
        self.top=self.winfo_toplevel()
        self.top.rowconfigure(0, weight=1)
        self.top.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(2, weight=1)
        
        self.currenttime = Tk.DoubleVar()
        
        self.videoSelection = Tk.IntVar()
        self.videoSelection.set(1)
        
        self.createWidgets()
        self.init_player()
    
    def createWidgets(self):
        
        self.video = Tk.Frame(self, bg='white')
        self.video.configure(width=250, height=250)
        self.video.anchor(Tk.CENTER)
        self.video.grid(column = 0, row=0,sticky=Tk.N+Tk.S+Tk.E+Tk.W)
        
        self.video2 = Tk.Frame(self, bg='white')
        self.video2.configure(width=250, height=250)
        self.video2.anchor(Tk.CENTER)
        self.video2.grid(column = 1, row=0,sticky=Tk.N+Tk.S+Tk.E+Tk.W)
        
        self.video3 = Tk.Frame(self, bg='white')
        self.video3.configure(width=250, height=250)
        self.video3.anchor(Tk.CENTER)
        self.video3.grid(column = 2, row=0,sticky=Tk.N+Tk.S+Tk.E+Tk.W)
        
        
        
        self.controlcontainer  = Tk.LabelFrame(relief='flat', bg='white')
        self.controlcontainer.grid(column = 0, row=1)
        
        self.timelinecontainer = Tk.LabelFrame(self.controlcontainer, relief='flat', bg='blue', width=250*3)
        self.timelinecontainer.grid(sticky=Tk.N+Tk.S+Tk.E+Tk.W)
        self.timeline = Tk.Scale(self.timelinecontainer, from_=0.0, to=1.0, orient=Tk.HORIZONTAL, resolution=-1, sliderlength=5, sliderrelief='flat')
        self.timeline.grid()
        
        self.playbutton = Tk.Button(self.controlcontainer, text='Play', command=self.on_play)
        self.playbutton.grid(column=0, row=1)
        self.stopbutton = Tk.Button(self.controlcontainer, text='Stop', command=self.on_stop)
        self.stopbutton.grid(column = 1, row=1)
        self.revbutton = Tk.Button(self.controlcontainer, text='Rew', command=self.on_rew)
        self.revbutton.grid(column=2, row=1)
        self.ffwdbutton = Tk.Button(self.controlcontainer, text='FFWD', command=self.on_ffwd)
        self.ffwdbutton.grid(column = 3, row=1)
        self.debug = Tk.Button(self.controlcontainer, text='debug', command=self.on_debug)
        self.debug.grid(column = 4, row=1)
        self.switchScreen = Tk.Button(self.controlcontainer, text='switchScreen', command=self.on_switchScreen)
        self.switchScreen.grid(column = 5, row=1)
        
#         self.videoSelectorContainer = Tk.LabelFrame()
#         for index in [1,2]:
#             self.radio = Tk.Radiobutton(self.videoSelectorContainer, 
#                                         text=str(index),
#                                         value=index, 
#                                         variable=self.videoSelection, 
#                                         command=lambda:self.updateVideo(self.videoSelection.get()))
#             self.radio.grid(column=0, row=index)
#         self.videoSelectorContainer.grid(column=1,row=0)
    
    
    def init_player(self):
                
#         self.player1 = SimplePlayer(name='Player1')
#         self.player2 = SimplePlayer(name ='Player2')
        
#         self.player1.setXid(self.video.winfo_id())
#         self.player2.setXid(self.video2.winfo_id())

#         self.player1.setMedia(media[1], hasAudio=False, hasVideo=True)
#         self.player2.setMedia(media[2], hasVideo=True)
#         

        self.multiplayer = MultipleMediaPlayer('multiplayer')
        
        self.multiplayer.addMediaToPlaylist(media[1], hasAudio=False)
        self.multiplayer.addMediaToPlaylist(media[2], hasAudio=False)
        self.multiplayer.addMediaToPlaylist(media[3], hasAudio=False)
        
        self.multiplayer.setMediaXid(media[1], self.video.winfo_id())
        self.multiplayer.setMediaXid(media[2],self.video2.winfo_id())
        self.multiplayer.setMediaXid(media[3],self.video3.winfo_id())
        self.multiplayer.removeMediaFromPlaylist(media[3])
        
        self.players = [self.multiplayer]
        

    def on_play(self):
        for p in self.players:
            p.play()
    
    def on_stop(self):
        for p in self.players:
            p.stop()
    
    def on_rew(self):
        for p in self.players:
            p.rew()
    
    def on_ffwd(self):
        for p in self.players:
            p.ffwd()
            
    def on_debug(self):
        for p in self.players:
            p.debug()
    
    def on_switchScreen(self):
        for widget in self.video.winfo_children():
            widget.destroy()
        for widget in self.video2.winfo_children():
            widget.destroy()
        p1xid, p2xid, p3xid = self.multiplayer.getMediaXid(media[1]), self.multiplayer.getMediaXid(media[2]), self.multiplayer.getMediaXid(media[3])
        self.multiplayer.setMediaXid(media[1], p3xid)
        self.multiplayer.setMediaXid(media[2], p1xid)
        self.multiplayer.setMediaXid(media[3], p2xid)



if __name__ == '__main__':
    app = App()
    app.mainloop()
