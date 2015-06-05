import tkinter as Tk
from PIL import Image, ImageTk
from os import path
from pprint import pprint

from player import *
     
uri1 = path.join(path.dirname(path.abspath(__file__)), 'v3.avi')
uri2 = path.join(path.dirname(path.abspath(__file__)), 'v2.avi')
   
class App(Tk.Frame):
    
    def __init__(self, *arg, **kwarg):
        super(App, self).__init__(*arg, **kwarg)
        self.config(bd=30)
        self.grid()
        
        self.createWidgets()
        self.init_player()
    
     
    def createWidgets(self):
        
        self.video = Tk.Frame(self, bg='white')
        self.video.configure(width=250, height=250)
        self.video.anchor(Tk.CENTER)
        self.video.grid(column = 0, row=0)
        
        self.video2 = Tk.Frame(self, bg='white')
        self.video2.configure(width=250, height=250)
        self.video2.anchor(Tk.CENTER)
        self.video2.grid(column = 1, row=0)
        
        self.buttoncontainer  = Tk.LabelFrame(relief='flat')
        self.buttoncontainer.grid(column = 0, row=1)
        self.playbutton = Tk.Button(self.buttoncontainer, text='Play', command=self.on_play)
        self.playbutton.grid(column=0, row=0)
        self.stopbutton = Tk.Button(self.buttoncontainer, text='Stop', command=self.on_stop)
        self.stopbutton.grid(column = 1, row=0)
        self.revbutton = Tk.Button(self.buttoncontainer, text='Rew', command=self.on_rew)
        self.revbutton.grid(column=0, row=1)
        self.ffwdbutton = Tk.Button(self.buttoncontainer, text='FFWD', command=self.on_ffwd)
        self.ffwdbutton.grid(column = 1, row=1)
        
            
    def init_player(self):
                
        self.player1 = Player(name='Player1')
        self.player2 = Player(name ='Player2')
        
        self.player1.set_xid(self.video.winfo_id())
        self.player2.set_xid(self.video2.winfo_id())

        self.player1.set_media(uri1)
        self.player2.set_media(uri2)
        
        self.players = [self.player1, self.player2]


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



if __name__ == '__main__':
    app = App()
    app.mainloop()