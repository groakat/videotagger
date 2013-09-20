"""
uses:
http://bazaar.launchpad.net/~jderose/+junk/gst-examples/view/head:/webcam-1.0
"""

import time,sys

from time import localtime, strftime
import datetime as dt
import os
import subprocess as sp 
import textwrap
from multiprocessing import Process

import gc

import socket, struct

# import pyTools.videoCapture.relay as relay


# gc.set_debug(gc.DEBUG_LEAK)

def get_cell_value(cell):
    """
    http://code.activestate.com/recipes/439096-get-the-value-of-a-cell-from-a-closure/
    """
    return type(lambda: 0)(
        (lambda x: lambda: x)(0).func_code, {}, None, None, (cell,)
    )()
    

# gstreamer imports
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, Gtk, GdkX11, GstVideo, GLib
print "Gstreamer version:", Gst.version()

GObject.threads_init()
Gst.init(None)

class pipelineSwap(object):
    
    def __init__(self, 
                baseDir="/run/media/peter/Elements/peter/data/tmp-20130801/",
                device="/dev/video1",
                timeoutSec=3600,
                relayPowerSwitch=6,
                relayLightSwitch=7,
                dayFocus=100,
                dayExposure=98,
                dayGain=0,      
                nightFocus=130,
                nightExposure=98,
                nightGain=0,
                selfTermination=0):
        
        # user parameters #
        self.baseDir = baseDir
        self.device = device
        self.timeoutSec = timeoutSec
        
        self.relayPowerSwitch = relayPowerSwitch
        self.relayLightSwitch = relayLightSwitch
    
        self.dayFocus = dayFocus
        self.dayExposure = dayExposure
        self.dayGain = dayGain
    
        self.nightFocus = nightFocus
        self.nightExposure = nightExposure
        self.nightGain = nightGain
        
        self.selfTermination = selfTermination
        
        # end user parameters #
        
        self.inFirstMinute = True
        self.exitByTimer = False
        
        # assuming the vials are changed at day time, otherwise it will be 
        # changed back after the first minute        
        self.isSetToNightTime = None
        self.updateLight()
        
        
        
        import logging, logging.handlers        
        # Make a global logging object.
        self.log = logging.getLogger("log")
        self.log.setLevel(logging.DEBUG)
        h = logging.StreamHandler()
        f = logging.Formatter("%(levelname)s %(asctime)s <%(funcName)s> [%(lineno)d] %(message)s")
        h.setFormatter(f)
        for handler in self.log.handlers:
            self.log.removeHandler(handler)
            
        self.log.addHandler(h)

        
        # create gtk interface
        self.log.debug("create Gtk interface")
        self.window = Gtk.Window()
        self.log.debug("create Gtk interface 1")
        self.window.connect('destroy', self.quit)
        self.log.debug("create Gtk interface 2")
        self.window.set_default_size(800, 450)
        
        self.log.debug("create Gtk interface 3")
        self.box = Gtk.Box(homogeneous=False, spacing=6)
        self.window.add(self.box)
        
        self.log.debug("create Gtk interface 4")
        self.drawingarea = Gtk.DrawingArea()
        self.drawingarea.set_size_request(800, 350)
        self.box.pack_start(self.drawingarea, True, True, 0)        

        self.button = Gtk.Button(label="Click Here")
        self.button.connect("clicked", self.on_button_clicked)
        self.box.pack_start(self.button, True, True, 0)  

        self.log.debug("create self.pipelines")
        self.pipelines = dict()
        self.pipelines["main"] = Gst.Pipeline()
        self.pipelines["catch"] = Gst.Pipeline()
        
        self.log.debug("link message bus")
        # Create bus to get events from GStreamer pipeline
        self.bus = self.pipelines["main"].get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message::error', self.on_error)

        # This is needed to make the video output in our DrawingArea:
        self.bus.enable_sync_message_emission()
        self.bus.connect('sync-message::element', self.on_sync_message)      
        
        # create all self.elements that we will need later
        self.log.debug("create gst elements")


        # gst-launch-1.0 -e filesrc location="/run/media/peter/home/tmp/webcam/Video 66.mp4" ! qtdemux ! queue ! tee name=t ! queue ! h264parse ! avdec_h264 ! autovideosink t. ! queue ! h264parse ! mp4mux ! filesink location=/run/media/peter/home/tmp/webcam/test.mp4
        self.elements = dict()
        self.pads = dict()
        self.elements["src"] = Gst.ElementFactory.make("uvch264src", "src")
        
        self.elements["prevQueue"] = Gst.ElementFactory.make("queue", "prevQueue")  
        self.elements["vfcaps"] = Gst.ElementFactory.make("capsfilter", "vfcaps")
        self.elements["preview_sink"] = Gst.ElementFactory.make( "autovideosink", "previewsink")
        
        self.elements["vidQueue"] = Gst.ElementFactory.make( "queue", "vidQueue")  
        self.elements["vidcaps"] = Gst.ElementFactory.make("capsfilter", "vidcaps")
        self.elements["t"] = Gst.ElementFactory.make( "tee", "t")
        
        self.elements["srcQueue"] = Gst.ElementFactory.make( "queue", "srcQueue")       
        self.elements["recBin1"] = Gst.Bin.new("recoding bin 1")
        self.elements["fileQueue1"] = Gst.ElementFactory.make( "queue", "fileQueue1")
        self.elements["ph264_1"] = Gst.ElementFactory.make ("h264parse", "ph264_1")
        self.elements["mux_1"] = Gst.ElementFactory.make("mp4mux", "mux1")
        self.elements["filesink1"] = Gst.ElementFactory.make( "filesink", "filesink1")
         
        self.elements["recBin2"] = Gst.Bin.new("recoding bin 2")
        self.elements["fileQueue2"] = Gst.ElementFactory.make( "queue", "fileQueue2")
        self.elements["ph264_2"] = Gst.ElementFactory.make ("h264parse", "ph264_2")
        self.elements["mux_2"] = Gst.ElementFactory.make("mp4mux", "mux2")
        self.elements["filesink2"] = Gst.ElementFactory.make( "filesink", "filesink2")
         
        self.elements["recBin3"] = Gst.Bin.new("recoding bin 3")
        self.elements["fileQueue3"] = Gst.ElementFactory.make( "queue", "fileQueue3")
        self.elements["ph264_3"] = Gst.ElementFactory.make ("h264parse", "ph264_3")
        self.elements["mux_3"] = Gst.ElementFactory.make("mp4mux", "mux3")
        self.elements["filesink3"] = Gst.ElementFactory.make( "filesink", "filesink3")



        if any(self.elements[k] is None for k in self.elements.keys()):
            raise RuntimeError("one or more self.elements could not be created")

        self.log.debug("populate main pipeline")
        self.pipelines["main"].add(self.elements["src"])
        
        self.pipelines["main"].add(self.elements["prevQueue"])  
        self.pipelines["main"].add(self.elements["vfcaps"])
        self.pipelines["main"].add(self.elements["preview_sink"])
        
        self.pipelines["main"].add(self.elements["vidQueue"])  
        self.pipelines["main"].add(self.elements["vidcaps"])
        self.pipelines["main"].add(self.elements["t"])
        
        self.pipelines["main"].add(self.elements["srcQueue"])


        self.log.debug("link self.elements in main pipeline")
        self.log.debug("1. linking preview branch...")
        srcP2 = self.elements["src"].get_static_pad('vfsrc')
        tP2 = self.elements["prevQueue"].get_static_pad("sink")
        assert(srcP2.link(tP2) ==  Gst.PadLinkReturn.OK)
        assert(self.elements["prevQueue"].link(self.elements["vfcaps"]))
        assert(self.elements["vfcaps"].link(self.elements["preview_sink"]))
        
        
        self.log.debug("2. linking H264 branch until tee...")                        
        srcP = self.elements["src"].get_static_pad('vidsrc')
        tP = self.elements["vidQueue"].get_static_pad("sink")
        assert(srcP.link(tP) ==  Gst.PadLinkReturn.OK)                
        assert(self.elements["vidQueue"].link(self.elements["vidcaps"]))    
        assert(self.elements["vidcaps"].link(self.elements["t"]))#         
        
        
        self.log.debug("populate recBin1")          
        self.elements["recBin1"].add(self.elements["fileQueue1"])
        self.elements["recBin1"].add(self.elements["ph264_1"])
        self.elements["recBin1"].add(self.elements["mux_1"])
        self.elements["recBin1"].add(self.elements["filesink1"])
        
        self.log.debug("link elements in recBin1")   
        assert(self.elements["fileQueue1"].link(self.elements["ph264_1"])) 
        assert(self.elements["ph264_1"].link(self.elements["mux_1"])) 
        assert(self.elements["mux_1"].link(self.elements["filesink1"]))
        
        self.log.debug("create ghost pad for recBin1")
        self.elements["recBin1"].add_pad(
                                Gst.GhostPad.new("sink",
                                self.elements["fileQueue1"].get_static_pad("sink")))
        
        
        self.log.debug("populate recBin2")          
        self.elements["recBin2"].add(self.elements["fileQueue2"])
        self.elements["recBin2"].add(self.elements["ph264_2"])
        self.elements["recBin2"].add(self.elements["mux_2"])
        self.elements["recBin2"].add(self.elements["filesink2"])
        
        self.log.debug("link elements in recBin2")   
        assert(self.elements["fileQueue2"].link(self.elements["ph264_2"])) 
        assert(self.elements["ph264_2"].link(self.elements["mux_2"])) 
        assert(self.elements["mux_2"].link(self.elements["filesink2"]))
        
        self.log.debug("create ghost pad for recBin2")
        self.elements["recBin2"].add_pad(
                                Gst.GhostPad.new("sink",
                                self.elements["fileQueue2"].get_static_pad("sink")))
        
        
        self.log.debug("add recBin1 to main pipeline")
        self.pipelines["main"].add(self.elements["recBin1"])
          
          
        self.log.debug("link srcQueue --> recBin to tee")
        self.pads["tPad2"] = Gst.Element.get_request_pad(self.elements["t"], 'src_%u')
        self.pads["tPad2"].link(self.elements["srcQueue"].get_static_pad("sink"))  
        self.elements["srcQueue"].link(self.elements["recBin1"])  
           
         
        self.log.debug("set filesink1 location")   
        self.updateFilesinkLocation(self.elements["filesink1"], self.elements["mux_1"])


        self.log.debug("set uvch264 properties")   
        self.elements["src"].set_property("auto-start", True)
        self.elements["src"].set_property("fixed-framerate", True)
        self.elements["src"].set_property("async-handling", False)
        self.elements["src"].set_property("iframe-period", 30)
        self.elements["src"].set_property("initial-bitrate", 12000000)
#         self.elements["src"].set_property("usage-type", 3)
#         self.elements["src"].set_property("num-clock-samples", -1)
        self.elements["src"].set_property("device", self.device)
        
        self.log.debug("set caps")           
        caps = Gst.Caps.from_string("video/x-h264,width=1920,height=1080,framerate=30/1,profile=constrained-baseline")
        self.elements["vidcaps"].props.caps = caps
        caps2 = Gst.Caps.from_string('video/x-raw,width=320,height=240,framerate=15/1')
        self.elements["vfcaps"].props.caps = caps2
        
        
#         self.elements["mux_1"].set_property("dts-method", 2)
                
        
        self.debugBuffer = None
        
        self.log.debug("done")
        self.elementRefcounting()
        
        
        # register function that initiates swap of filename in Gtk mainloop #
        # make sure that that it will be called at the beginning of the next 
        # minute 
        if self.timeoutSec == 3600:
            GLib.timeout_add_seconds(self.timeoutSec - (localtime().tm_sec + 
                                     localtime().tm_min * 60), self.blockFirstFrame)            
        else:
            GLib.timeout_add_seconds(self.timeoutSec - localtime().tm_sec, self.blockFirstFrame)
        
#         GLib.timeout_add_seconds(60, self.requestKeyframe)
        
        
    def run(self):        
        self.log.debug("start pipeline")
        self.cnt = 0
        
        self.window.show_all()
        # You need to get the XID after window.show_all().  You shouldn't get it
        # in the on_sync_message() handler because threading issues will cause
        # segfaults there.
        
        Gst.debug_bin_to_dot_file_with_ts(self.pipelines["main"], Gst.DebugGraphDetails.ALL, "main_before" )
        self.xid = self.drawingarea.get_property('window').get_xid()
        self.pipelines["main"].set_state(Gst.State.PLAYING)
#         self.pipelines["catch"].set_state(Gst.State.PLAYING)
        Gtk.main()
        self.updateLight()

    def elementRefcounting(self):
        for k in self.elements.keys():
            self.log.debug("recount of {key}: {cnt}".format(key=k, cnt=sys.getrefcount(self.elements[k])))   
        
    def pipeline2Null(self, pipeline):
        self.log.debug("send EOS")
        pipeline.send_event(Gst.Event.new_eos())           
        bus = pipeline.get_bus()        
        msg = bus.timed_pop_filtered (Gst.CLOCK_TIME_NONE, Gst.MessageType.EOS | Gst.MessageType.ERROR)
        
        if msg.type == Gst.MessageType.ERROR:
            self.log.debug("bus message {0}".format(msg.parse_error()))
            Gst.debug_bin_to_dot_file_with_ts(self.pipelines["main"], Gst.DebugGraphDetails.ALL, "main" )
                
        self.log.debug("null pipeline")
        pipeline.set_state(Gst.State.NULL) 
        
    def updateFilesinkLocation(self, fs, mux=None):
        """
        Changes the *location* property of the filesink. Takes care of 
        generating the appropriate folders etc.
        
        Filename will be something like:
        'basedir/20130801/15/2013-08-01.15-59-27.mp4'
        
        or generic:
        
        'baseidr/yyyyMMdd/hh/yyyy-MM-dd.hh-mm-ss.mp4'
        Args:
            fs (Gst.filesink)
        """
        folder = os.path.join(self.baseDir, strftime("%Y%m%d", localtime()),
                              strftime("%H", localtime()))
        
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        rawPath = os.path.join(folder,
                                strftime("%Y-%m-%d.%H-%M-%S.{0}", localtime()))
        fs.set_property("location", rawPath.format('mp4'))
        if mux is not None:
            mux.set_property("moov-recovery-file", rawPath.format('moov'))
    
    def quit(self, window):
        self.pipeline2Null(self.pipelines["main"])            
        Gtk.main_quit()
        if self.exitByTimer:
            self.log.info("exit by timer")
        
        
    def kill(self):
        self.quit(self.window)

    def on_sync_message(self, bus, msg):
        if msg.get_structure().get_name() == 'prepare-window-handle':
            self.log.debug('prepare-window-handle')
            msg.src.set_property('force-aspect-ratio', True)
            msg.src.set_window_handle(self.xid)

    def on_error(self, bus, msg):
        print('on_error():', msg.parse_error())
        

    def on_button_clicked(self, widget):
        print "Hello World"
        #self.blockOnNextKeyframe()
        self.setAutoFocus(False)
        self.setAbsoluteFocus(30)
        self.setGain(1)
        self.setAutoExposure(1)
        self.setAbsoluteExposure(100)
        
        
        
    def generateRecBin1(self):      
        self.elementRefcounting()  
        self.elements["recBin1"] = Gst.Bin.new("recoding bin 1")
        self.elements["fileQueue1"] = Gst.ElementFactory.make( "queue", "fileQueue{0}".format(self.cnt))
        self.elements["ph264_1"] = Gst.ElementFactory.make ("h264parse", "ph264_{0}".format(self.cnt))
        self.elements["mux_1"] = Gst.ElementFactory.make("mp4mux", "mux{0}".format(self.cnt))
        self.elements["filesink1"] = Gst.ElementFactory.make( "filesink", "filesink{0}".format(self.cnt))


        self.log.debug("populate recBin1")          
        self.elements["recBin1"].add(self.elements["fileQueue1"])
        self.elements["recBin1"].add(self.elements["ph264_1"])
        self.elements["recBin1"].add(self.elements["mux_1"])
        self.elements["recBin1"].add(self.elements["filesink1"])
        
        self.log.debug("link elements in recBin1")   
        assert(self.elements["fileQueue1"].link(self.elements["ph264_1"])) 
        assert(self.elements["ph264_1"].link(self.elements["mux_1"])) 
        assert(self.elements["mux_1"].link(self.elements["filesink1"]))
        
        self.log.debug("create ghost pad for recBin1")
        self.elements["recBin1"].add_pad(
                                Gst.GhostPad.new("sink",
                                self.elements["fileQueue1"].get_static_pad("sink")))
        
    def generateRecBin2(self):
        self.elementRefcounting()
        self.elements["recBin2"] = Gst.Bin.new("recoding bin 2")
        self.elements["fileQueue2"] = Gst.ElementFactory.make( "queue", "fileQueue{0}".format(self.cnt))
        self.elements["ph264_2"] = Gst.ElementFactory.make ("h264parse", "ph264_{0}".format(self.cnt))
        self.elements["mux_2"] = Gst.ElementFactory.make("mp4mux", "mux{0}".format(self.cnt))
        self.elements["filesink2"] = Gst.ElementFactory.make( "filesink", "filesink{0}".format(self.cnt))


        self.log.debug("populate recBin2")          
        self.elements["recBin2"].add(self.elements["fileQueue2"])
        self.elements["recBin2"].add(self.elements["ph264_2"])
        self.elements["recBin2"].add(self.elements["mux_2"])
        self.elements["recBin2"].add(self.elements["filesink2"])
        
        self.log.debug("link elements in recBin2")   
        assert(self.elements["fileQueue2"].link(self.elements["ph264_2"])) 
        assert(self.elements["ph264_2"].link(self.elements["mux_2"])) 
        assert(self.elements["mux_2"].link(self.elements["filesink2"]))
        
        self.log.debug("create ghost pad for recBin2")
        self.elements["recBin2"].add_pad(
                                Gst.GhostPad.new("sink",
                                self.elements["fileQueue2"].get_static_pad("sink")))
        
    def blockFirstFrame(self):     
        """
        Helper function that registers :func:`blockOnNextKeyframe` to be
        called by the Gtk mainloop every 60 seconds
        
        This function should be called once at the beginning of a minute 
        to get a regular filename with seconds 00. 
        
        Returns:
            False (to unregister itself from a GLib.timout_add())
        """   
        if self.inFirstMinute:
            GLib.timeout_add_seconds(self.timeoutSec, self.blockOnNextKeyframe)
            
        self.blockOnNextKeyframe()
        return False
            
    def blockOnNextKeyframe(self):      
        if self.selfTermination:
            if self.cnt >= self.selfTermination:
                self.exitByTimer = True
                self.window.destroy()
            
        tp = self.elements["srcQueue"].get_static_pad("sink")    
#         tp = self.elements["queue_preview"].get_static_pad("sink")    
        self.pipelines['main'].send_event(GstVideo.video_event_new_upstream_force_key_unit(Gst.CLOCK_TIME_NONE, True, self.cnt))  
        tp.add_probe(Gst.PadProbeType.BUFFER, blockActiveQueuePad, self)
                
        self.updateLight()
        
        return True
    
    def requestKeyframe(self):
        print "request keyframe"        
        self.pipelines['main'].send_event(GstVideo.video_event_new_upstream_force_key_unit(Gst.CLOCK_TIME_NONE, True, self.cnt))
        
        return True  
    
    def resetBin(self, bin):         
        bin.set_state(Gst.State.NULL)    
         
        if bin == self.elements["recBin1"]:
            self.generateRecBin1()
        else:
            self.generateRecBin2()   
            
    
    def setAutoFocus(self, val):
        """
        set autofocus of device to `val`
        """
        cmd = "uvcdynctrl -d {device} -s 'Focus, Auto' {val}".format(\
                                            device=self.device, 
                                            val=val)
        p = sp.Popen(cmd,
             shell=True, stdout=sp.PIPE, stderr=sp.STDOUT)
        p.communicate()[0]
    
    def setAbsoluteFocus(self, val):
        """
        set absolute focus of device to `val`
        """
        cmd = "uvcdynctrl -d {device} -s 'Focus (absolute)' {val}".format(\
                                            device=self.device, 
                                            val=val)
        p = sp.Popen(cmd,
             shell=True, stdout=sp.PIPE, stderr=sp.STDOUT)
        p.communicate()[0]
        
    def setGain(self, val):
        """
        set gain of device to `val`
        """
        cmd = "uvcdynctrl -d {device} -s 'Gain' {val}".format(\
                                            device=self.device, 
                                            val=val)
        p = sp.Popen(cmd,
             shell=True, stdout=sp.PIPE, stderr=sp.STDOUT)
        p.communicate()[0]
        
    def setAutoExposure(self, val):
        """
        set auto exposure of device to `val`
        Args:
            val (int)
                    Manual Mode=1
                    Aperature Priority Mode=3
        """
        cmd = "uvcdynctrl -d {device} -s 'Exposure, Auto' {val}".format(\
                                            device=self.device, 
                                            val=val)
        p = sp.Popen(cmd,
             shell=True, stdout=sp.PIPE, stderr=sp.STDOUT)
        p.communicate()[0]
        
    def setAbsoluteExposure(self, val):
        """
        set gain of device to `val`
        """
        cmd = "uvcdynctrl -d {device} -s 'Exposure (Absolute)' {val}".format(\
                                            device=self.device, 
                                            val=val)
        p = sp.Popen(cmd,
             shell=True, stdout=sp.PIPE, stderr=sp.STDOUT)
        p.communicate()[0]
        
        
    def switchRelayOn(self, relay):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(('192.168.0.200', 17494))
        if relay == 0:
            val = 101
        elif relay == 1:
            val = 102
        elif relay == 2:
            val = 103
        elif relay == 3:
            val = 104
        elif relay == 4:
            val = 105
        elif relay == 5:
            val = 106
        elif relay == 6:
            val = 107
        elif relay == 7:
            val = 108
        else:
            raise ValueError('relay has to be an int in 0..7')
        s.send(chr(val))
        time.sleep(0.01)
        s.close()
        
    def switchRelayOff(self, relay):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(('192.168.0.200', 17494))
        if relay == 0:
            val = 111
        elif relay == 1:
            val = 112
        elif relay == 2:
            val = 113
        elif relay == 3:
            val = 114
        elif relay == 4:
            val = 115
        elif relay == 5:
            val = 116
        elif relay == 6:
            val = 117
        elif relay == 7:
            val = 118
        else:
            raise ValueError('relay has to be an int in 0..7')
        
        s.send(chr(val))
        time.sleep(0.01)
        s.close()
        
    def updateLight(self):
        now = dt.datetime.now()
        
        if not self.isSetToNightTime is None:
            if now.hour < 10 or now.hour > 21:
                if not self.isSetToNightTime:
                    self.setNight()
            else:
                if self.isSetToNightTime:
                    self.setDay()
                
    def setNight(self):
        try:
            self.switchRelayOn(self.relayPowerSwitch)
            self.switchRelayOn(self.relayLightSwitch)
            
            self.setAbsoluteExposure(self.nightExposure)
            self.setAbsoluteFocus(self.nightFocus)
            self.setGain(self.nightGain)
            self.isSetToNightTime = True
        except:
            pass
                
    def setDay(self):
        try:
            self.switchRelayOn(self.relayPowerSwitch)
            self.switchRelayOff(self.relayLightSwitch)
            
            self.setAbsoluteExposure(self.dayExposure)
            self.setAbsoluteFocus(self.dayFocus)
            self.setGain(self.dayGain)
            self.isSetToNightTime = False
        except:
            pass
            
    
def blockActiveQueuePad(pad, probeInfo, userData):   
    self = userData
    
    buffer = probeInfo.get_buffer()
    #if not buffer.flag_is_set(Gst.BufferFlags.DELTA_UNIT):
    if not (buffer.mini_object.flags & Gst.BufferFlags.DELTA_UNIT):
        pad.remove_probe(probeInfo.id)
        self.log.debug("found keyframe start blocking process") 
        self.log.debug("{0}".format(buffer.get_all_memory().size)) 
        
        # tee pad to active recording bin #
        Gst.debug_bin_to_dot_file_with_ts(self.pipelines["main"], Gst.DebugGraphDetails.ALL, "main_blockActiveQueuePad" )
        tp = self.elements["srcQueue"].get_static_pad("src")      
        tp.add_probe(Gst.PadProbeType.BLOCK_DOWNSTREAM, preparePipeline, self)
        return Gst.PadProbeReturn.DROP
    else:
        self.log.debug("no keyframe yet")  
        return Gst.PadProbeReturn.OK
        
        
def preparePipeline(pad, probeInfo, userData):
    self = userData
    self.log.debug("pad blocked")
    
    # remove padProbe
    pad.remove_probe(probeInfo.id)
    self.padProbes = [[pad, probeInfo]]
    
################################################################################

    self.cnt += 1
    # get pad of current recBin
    pC = pad.get_peer()
    # get current recBin (the one that is currently doing the recording)
    binC = pC.get_parent()
    
    # get next recBin (the one that will be linked to the video stream next)
    binN = None    
    fs = None
    if binC == self.elements["recBin1"]:
        self.log.debug("replace recBin1 by recBin2") 
 
        self.log.debug("prepare next recBin")   
        self.resetBin(self.elements["recBin2"])
        
        binN = self.elements["recBin2"]
        fs = self.elements["filesink2"]
        mux = self.elements["mux_2"]
        fqN = self.elements["fileQueue2"]
        fqC = self.elements["fileQueue1"]
    else:
        self.log.debug("replace recBin2 by recBin1")    
        self.log.debug("ref of recBin1: {0}".format(gc.get_referrers(self.elements["recBin1"])))
        
        self.log.debug("prepare next recBin")   
        self.resetBin(self.elements["recBin1"])
        
        binN = self.elements["recBin1"]
        fs = self.elements["filesink1"]
        mux = self.elements["mux_1"]
        fqN = self.elements["fileQueue1"]
        fqC = self.elements["fileQueue2"]       
    
        
    self.updateFilesinkLocation(fs, mux)
    self.log.debug("remove current recBin from main and prepare catch")
    self.elements["srcQueue"].unlink(fqC)  
    self.pipelines["main"].remove(binC)   

    Gst.debug_bin_to_dot_file_with_ts(self.pipelines["main"], Gst.DebugGraphDetails.ALL, "main-1" )
         
    self.log.debug("send EOS to current recBin")
    binC.send_event(Gst.Event.new_eos())  

    self.log.debug("prepare next recBin")    
    binN.set_state(Gst.State.NULL)
    self.log.debug("add and link next recBin to main")
    self.pipelines["main"].add(binN)   
    assert(self.elements["srcQueue"].link(binN))
        
    
    self.log.debug("change file location of next recBin")
    for pad in mux.pads:
        if pad.get_name().startswith("video"):
            pad.push_event(Gst.Event.new_reconfigure())
            
    binN.set_state(Gst.State.PLAYING)
    
    
################################################################################
    
    
    Gst.debug_bin_to_dot_file_with_ts(self.pipelines["catch"], Gst.DebugGraphDetails.ALL, "catch-2" )
    Gst.debug_bin_to_dot_file_with_ts(self.pipelines["main"], Gst.DebugGraphDetails.ALL, "main-2" )
    
    return Gst.PadProbeReturn.OK
    
def relinkPipeline(pad, probeInfo, userData):
    
    self = userData
    #if (probeInfo.type !=  Gst.EventType.EOS):
    if self.cnt < 2:
        self.cnt += 1
        self.log.debug("Event received, not EOS but {0}".format(probeInfo.type))
        return Gst.PadProbeReturn.OK;
    
    self.log.debug("EOS received, change file location")
    # remove padProbe
    pad.remove_probe(probeInfo.id)
    
    self.padProbes += [[pad, probeInfo]]
    
    self.elements["filesink1"].set_state(Gst.State.NULL) 
    self.elements["filesink1"].set_property("location", "/run/media/peter/home/tmp/webcam/test3.mp4")    
    self.elements["filesink1"].set_state(Gst.State.PLAYING) 
    
    Gst.debug_bin_to_dot_file_with_ts(self.pipelines["main"], Gst.DebugGraphDetails.ALL, "main_blocked" )
    
    return Gst.PadProbeReturn.OK
    
        
        

        
def on_new_demux_pad_preview(gstObj, pad):
    demux = pad.get_parent()
    pipeline = demux.get_parent()
    ph264 = pipeline.get_by_name('t')
    demux.link(ph264)
    
def link_many(elements, debug=True):
    if type(elements) == list:
        for i in range(len(elements) -1):
            if debug:
                assert(elements[i].link(elements[i+1]))
            else:
                elements[i].link(elements[i+1])
    else:
        raise ValueError("expect list of elements")
    
    
    
def startVC(args):
    
    mainloop = GObject.MainLoop()
    vC = pipelineSwap(args.baseDir, 
                  args.device, 
                  args.swapInterval, 
                  args.relayPowerSwitch, 
                  args.relayLightSwitch, 
                  args.dayFocus, 
                  args.dayExposure, 
                  args.dayGain, 
                  args.nightFocus, 
                  args.nightExposure, 
                  args.nightGain,
                  args.selfTermination)
    vC.run()
    del vC
    del mainloop
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(\
    formatter_class=argparse.RawDescriptionHelpFormatter,\
    description=textwrap.dedent(\
    """
    Program to capture days-long H264 encoded video from webcams and other 
    cameras that support the UVC driver spec and H264 on-chip encoding.
    
    To avoid massive data-loss in case of power-failure or other catastrophic 
    events, the program saves the video in smaller partititions (called chunks)
    of given length. The user can specify the length of the chunks with the 
    --swapInterval parameter.
    
    This program was developed to record continuously over several days while
    simulating day/night lighting of the scene. To change the lighting, a relay
    switch is controlled with the relay-module. The relay uses two switches 
    for each light setup. One switch to turn the light on and off and another
    switch to switch between day and night lighting setup.
    
    Furthermore the program uses the linux program uvcdynctrl to control camera
    parameters such as focus and exposure dynamically. In the example setup the
    program was tested with, an blueish and an IR light source were used to
    simulate day and night illumination. Because of the different wavelengths
    and intensity emitted from the ligth sources the focus and the exposure have
    to set differently for day and night.    
    """),
    epilog=textwrap.dedent(\
    """
    Written and tested by Peter Rennert in 2013 as part of his PhD project at
    the University College London.
    
    You can contact the author via p.rennert@cs.ucl.ac.uk
    
    I did my best to avoid errors and bugs, but I cannot privide any reliability
    with respect to software or hardware or data (including fidelity and potential
    data-loss), nor any issues it may cause with your experimental setup.
    
    <Licence missing>
    """))
    
    
    parser.add_argument('-b', '--baseDir', 
                help="path to the directory the files are saved to", 
                default="/run/media/peter/Elements/peter/data/tmp-20130801/")
    
    parser.add_argument('-d', '--device', 
                        help="camera",
                        default='/dev/video1')
    
    
    parser.add_argument('-lS', '--relayLightSwitch', 
                        help="relay port for light switch",
                        type=int, default=7)
    
    parser.add_argument('-pS', '--relayPowerSwitch', 
                        help="relay port to turn light on",
                        type=int, default=6)
    
    parser.add_argument('-dF', '--dayFocus', 
                        help="camera focus for day",
                        type=int, default=100)
    
    parser.add_argument('-dE', '--dayExposure', 
                        help="camera exposure for day",
                        type=int, default=98)
    
    parser.add_argument('-dG', '--dayGain', 
                        help="camera gain for day",
                        type=int, default=0)
    
    parser.add_argument('-nF', '--nightFocus', 
                        help="camera focus for night",
                        type=int, default=130)
    
    parser.add_argument('-nE', '--nightExposure', 
                        help="camera exposure for night",
                        type=int, default=98)
    
    parser.add_argument('-nG', '--nightGain', 
                        help="camera gain for night",
                        type=int, default=0)
    
    parser.add_argument('-sI', '--swapInterval', 
                        help="seconds to pass between swaps of file destinations",
                        type=int, default=60)
    
    parser.add_argument('-sT', '--selfTermination', 
                        help=textwrap.dedent(\
                        """after how many swaps the capture should stop and the program should terminate 
                        if set to 0, program will not shut down itself"""),
                        type=int, default=0)
    
    parser.add_argument('-dS', '--directStart', 
                        help="start capture straight after program start",
                        dest='directStart',action='store_true')
#     
    
    parser.set_defaults(directStart=False)
        
    args = parser.parse_args()
    
    startVC(args)
    
#     while(1):
#         startVC(args)
#         p = Process(target=startVC, args=(args,))            
#         p.start()
#         p.join()        
#         time.sleep(1)        
#         p.terminate()
#         del p


