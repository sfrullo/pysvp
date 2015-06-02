import threading
import tkinter as Tk

from moviepy.editor import VideoFileClip
from PIL import ImageTk, Image

class App(Tk.Frame):
    
    def __init__(self, *arg, **kwarg):
        super(App, self).__init__(*arg, **kwarg)
        self.grid()
        
        self.frame_number = 0
        self.basewidth = 500 
         
        self.vid = VideoFileClip('v1.avi')

        self.lab = Tk.Label(self)
        self.lab.grid(column=0, row=0)
        self.init_label()
        
        self.frame = Tk.Button(text='play', command=self.on_play)
        self.frame.grid(column=1, row=0)
        self.frame = Tk.Button(text='stop', command=self.on_stop)
        self.frame.grid(column=2, row=0)
        
        
    def scaleImage(self, img, basewidth):
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        return img.resize((basewidth, hsize), Image.ANTIALIAS)
        
        
    def init_label(self):
        frame = self.vid.get_frame(self.frame_number)
        im = Image.fromarray(frame)
        im = self.scaleImage(im, self.basewidth)
        im = ImageTk.PhotoImage(im)
        
        self.lab.configure(image=im, width=im.width(), height=im.height())
        self.lab.image = im
        
        
    def update_frame(self, t):
        if self.play_flag:
            frame = self.vid.get_frame(t)
            im = Image.fromarray(frame)
            im = self.scaleImage(im, self.basewidth)
            im = ImageTk.PhotoImage(im)
            
            self.lab.configure(image=im)
            self.lab.image = im
            
            self.frame_number += 1 / self.vid.fps  
            
            self.player = threading.Timer(1 / self.vid.fps, self.update_frame, args=[self.frame_number])
            self.player.start()
        else:
            self.player.cancel()
    
    def on_play(self):
        self.play_flag = True
        self.update_frame(self.frame_number)
    
        
    def on_stop(self):
        self.play_flag = False
    
if __name__ == '__main__':
    
    master = App()
    master.mainloop()
