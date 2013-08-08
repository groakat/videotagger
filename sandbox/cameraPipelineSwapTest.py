"""
uses:
http://bazaar.launchpad.net/~jderose/+junk/gst-examples/view/head:/webcam-1.0
"""

import time,sys

from time import localtime, strftime
import os

import gc

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
    
    def __init__(self):
        self.baseDir = "/run/media/peter/Elements/peter/data/tmp-20130801/"
        self.inFirstMinute = True
        
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

        self.mainloop = GObject.MainLoop()
        
        # create gtk interface
        self.log.debug("create Gtk interface")
        self.window = Gtk.Window()
        self.window.connect('destroy', self.quit)
        self.window.set_default_size(800, 450)
        
        self.box = Gtk.Box(homogeneous=False, spacing=6)
        self.window.add(self.box)
        
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
#         self.elements["src"].set_property("num-clock-samples", -1)
        self.elements["src"].set_property("device", "/dev/video1")
        
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
        GLib.timeout_add_seconds(60 - localtime().tm_sec, self.blockFirstFrame)
        
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
        self.blockOnNextKeyframe()    
        
        
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
            GLib.timeout_add_seconds(60, self.blockOnNextKeyframe)
            
        self.blockOnNextKeyframe()
        return False
            
    def blockOnNextKeyframe(self):       
            
        tp = self.elements["srcQueue"].get_static_pad("sink")    
#         tp = self.elements["queue_preview"].get_static_pad("sink")    
        self.pipelines['main'].send_event(GstVideo.video_event_new_upstream_force_key_unit(Gst.CLOCK_TIME_NONE, True, self.cnt))  
        tp.add_probe(Gst.PadProbeType.BUFFER, blockActiveQueuePad, self)
                
        return True
    
    def resetBin(self, bin):         
        bin.set_state(Gst.State.NULL)    
        
        if bin == self.elements["recBin1"]:
            self.generateRecBin1()
        else:
            self.generateRecBin2()        
        
    
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
    
    
if __name__ == "__main__":
    vC = pipelineSwap()
    vC.run()


