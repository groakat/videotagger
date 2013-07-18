"""
uses:
http://bazaar.launchpad.net/~jderose/+junk/gst-examples/view/head:/webcam-1.0
"""

import time


# gstreamer imports
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, Gtk, GdkX11, GstVideo
print "Gstreamer version:", Gst.version()

GObject.threads_init()
Gst.init(None)

class pipelineSwap(object):
    
    def __init__(self):
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
        self.elements["src"] = Gst.ElementFactory.make("filesrc", "src")
        self.elements["srcQueue"] = Gst.ElementFactory.make( "queue", "srcQueue")
        self.elements["queue_preview"] = Gst.ElementFactory.make( "queue", "queue_preview")    
        self.elements["demux_preview"] = Gst.ElementFactory.make("qtdemux", "demux_preview")
        self.elements["ph264_preview"] = Gst.ElementFactory.make ("h264parse", "ph264_preview")
        self.elements["avdec_preview"] = Gst.ElementFactory.make("avdec_h264", "dec_preview")
        self.elements["preview_sink"] = Gst.ElementFactory.make( "autovideosink", "previewsink")
        
        self.elements["t"] = Gst.ElementFactory.make( "tee", "t")
        
        self.elements["recBin1"] = Gst.Bin.new("recoding bin 1")
        self.elements["fileQueue1"] = Gst.ElementFactory.make( "queue", "fileQueue1")
        self.elements["ph264_1"] = Gst.ElementFactory.make ("h264parse", "ph264_1")
        self.elements["mux_1"] = Gst.ElementFactory.make("mp4mux", "mux_1")
        self.elements["filesink1"] = Gst.ElementFactory.make( "filesink", "file_sink1")
        
        self.elements["fakesrc"] = Gst.ElementFactory.make( "fakesrc", "fakesrc")
        self.elements["fakesink"] = Gst.ElementFactory.make( "fakesink", "fakesink")
        
        self.elements["recBin2"] = Gst.Bin.new("recoding bin 2")
        self.elements["fileQueue2"] = Gst.ElementFactory.make( "queue", "fileQueue2")
        self.elements["ph264_2"] = Gst.ElementFactory.make ("h264parse", "ph264_2")
        self.elements["mux_2"] = Gst.ElementFactory.make("mp4mux", "mux_2")
        self.elements["filesink2"] = Gst.ElementFactory.make("filesink", "file_sink2")



        if any(self.elements[k] is None for k in self.elements.keys()):
            raise RuntimeError("one or more self.elements could not be created")

        
        self.log.debug("populate main pipeline")
        self.pipelines["main"].add(self.elements["src"])
        self.pipelines["main"].add(self.elements["demux_preview"])
        self.pipelines["main"].add(self.elements["srcQueue"])
        self.pipelines["main"].add(self.elements["t"])
        
        self.pipelines["main"].add(self.elements["queue_preview"])
        self.pipelines["main"].add(self.elements["ph264_preview"])
        self.pipelines["main"].add(self.elements["avdec_preview"])
        self.pipelines["main"].add(self.elements["preview_sink"])
        
        
        self.log.debug("link self.elements in main pipeline")
        
        assert(self.elements["src"].link(self.elements["demux_preview"]))
        self.elements["demux_preview"].connect("pad-added", on_new_demux_pad_preview)   
        
        tPad1 = Gst.Element.get_request_pad(self.elements["t"], 'src_%u')
        tPad1.link(self.elements["queue_preview"].get_static_pad("sink"))
        assert(self.elements["queue_preview"].link(self.elements["ph264_preview"]))
        assert(self.elements["ph264_preview"].link(self.elements["avdec_preview"]))
        assert(self.elements["avdec_preview"].link(self.elements["preview_sink"]))
        
        
        
        self.elements["recBin1"].add(self.elements["fileQueue1"])
        self.elements["recBin1"].add(self.elements["ph264_1"])
        self.elements["recBin1"].add(self.elements["mux_1"])
        self.elements["recBin1"].add(self.elements["filesink1"])
        
        assert(self.elements["fileQueue1"].link(self.elements["ph264_1"])) 
        assert(self.elements["ph264_1"].link(self.elements["mux_1"])) 
        assert(self.elements["mux_1"].link(self.elements["filesink1"]))
        
        self.elements["recBin1"].add_pad(
                                Gst.GhostPad.new("sink",
                                self.elements["fileQueue1"].get_static_pad("sink")))
        
        self.pipelines["main"].add(self.elements["recBin1"])
        
        
        self.pads["tPad2"] = Gst.Element.get_request_pad(self.elements["t"], 'src_%u')
        self.pads["tPad2"].link(self.elements["srcQueue"].get_static_pad("sink"))  
        self.elements["srcQueue"].link(self.elements["recBin1"])  
        
        self.pipelines["catch"].add(self.elements["fakesrc"])
        self.pipelines["catch"].add(self.elements["fakesink"])
        assert(self.elements["fakesrc"].link(self.elements["fakesink"]))
        
#         self.pipelines["catch"].add(self.elements["fileQueue2"])
#         self.pipelines["catch"].add(self.elements["ph264_2"])
#         self.pipelines["catch"].add(self.elements["mux_2"])
#         self.pipelines["catch"].add(self.elements["filesink2"])
        
                
#         tPad2 = Gst.Element.get_request_pad(self.elements["t"], 'src_%u')
#         tPad2.link(self.elements["fileQueue1"].get_static_pad("sink"))  
#         assert(self.elements["fileQueue1"].link(self.elements["ph264_1"])) 
#         assert(self.elements["ph264_1"].link(self.elements["mux_1"])) 
#         self.log.debug("link mp4mux")     
#         assert(self.elements["mux_1"].link(self.elements["filesink1"]))  
        
#         assert(self.elements["fakesrc"].link(self.elements["fileQueue2"]))
#         assert(self.elements["fileQueue2"].link(self.elements["ph264_2"]))
#         assert(self.elements["ph264_2"].link(self.elements["mux_2"]))
#         assert(self.elements["mux_2"].link(self.elements["filesink2"]))
        
        
        self.log.debug("set filesink location")
        self.elements["src"].set_property("location", "/run/media/peter/home/tmp/webcam/Video 66.mp4")
        self.elements["filesink1"].set_property("location", "/run/media/peter/home/tmp/webcam/test1.mp4")
        self.elements["filesink2"].set_property("location", "/run/media/peter/home/tmp/webcam/test2.mp4")
                
        
        self.log.debug("done")
        
    def run(self):        
        self.log.debug("start pipeline")
        self.window.show_all()
        # You need to get the XID after window.show_all().  You shouldn't get it
        # in the on_sync_message() handler because threading issues will cause
        # segfaults there.
        self.xid = self.drawingarea.get_property('window').get_xid()
        self.pipelines["main"].set_state(Gst.State.PLAYING)
        self.pipelines["catch"].set_state(Gst.State.PLAYING)
        Gtk.main()

    def pipeline2Null(self, pipeline):
        self.log.debug("send EOS")
        pipeline.send_event(Gst.Event.new_eos())           
        bus = pipeline.get_bus()        
        msg = bus.timed_pop_filtered (Gst.CLOCK_TIME_NONE, Gst.MessageType.EOS | Gst.MessageType.ERROR)
        
        if msg.type == Gst.MessageType.ERROR:
            self.log.debug("bus message {0}".format(msg.parse_error()))
            Gst.debug_bin_to_dot_file_with_ts(self.pipelines["main"], Gst.DebugGraphDetails.ALL, "main" )
            Gst.debug_bin_to_dot_file_with_ts(self.pipelines["catch"], Gst.DebugGraphDetails.ALL, "catch" )
                
        self.log.debug("null pipeline")
        pipeline.set_state(Gst.State.NULL) 
    
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
        self.blockActiveQueuePad()
        
    def blockActiveQueuePad(self):   
        self.log.debug("start blocking process")     
        # tee pad to active recording bin
        Gst.debug_bin_to_dot_file_with_ts(self.pipelines["main"], Gst.DebugGraphDetails.ALL, "main_before" )
        tp = self.elements["srcQueue"].get_static_pad("src")      
        tp.add_probe(Gst.PadProbeType.BLOCK_DOWNSTREAM, preparePipeline, self)
        
def preparePipeline(pad, probeInfo, userData):
    self = userData
    self.log.debug("pad blocked")
    # remove padProbe
    pad.remove_probe(probeInfo.id)
    self.padProbes = [[pad, probeInfo]]
    
################################################################################
    self.pipelines["main"].remove(self.elements["recBin1"])   
#     
# #     self.elements["recBin1"].set_state(Gst.State.PAUSED)
    self.pipelines["catch"].set_state(Gst.State.PAUSED)
 
    self.elements["fakesrc"].unlink(self.elements["fakesink"])
#     self.elements["fakesink"].set_state(Gst.State.NULL)
    self.pipelines["catch"].remove(self.elements["fakesink"])
    self.pipelines["catch"].add(self.elements["recBin1"])
    assert(self.elements["fakesrc"].link(self.elements["recBin1"]))
    self.pipelines["catch"].set_state(Gst.State.PLAYING)
    Gst.debug_bin_to_dot_file_with_ts(self.pipelines["catch"], Gst.DebugGraphDetails.ALL, "catch" )
    Gst.debug_bin_to_dot_file_with_ts(self.pipelines["main"], Gst.DebugGraphDetails.ALL, "main" )
     
#     self.pipelines["catch"].set_state(Gst.State.PLAYING) 
    #self.pipeline2Null(self.pipelines["catch"])
    
    
    self.elements["recBin1"].send_event(Gst.Event.new_eos())  
#     
#     self.log.debug("change file location")
#     self.elements["filesink1"].set_property("location", "/run/media/peter/home/tmp/webcam/test3.mp4")
#  
#     self.log.debug("set catch to playing again")
#     self.pipelines["catch"].set_state(Gst.State.PLAYING)
#      
#     self.log.debug("removing recBin1 from catch")
#     self.pipelines["catch"].remove(self.elements["recBin1"])
#  
#     self.log.debug("adding recBin1 to main")
#     self.pipelines["main"].add(self.elements["recBin1"])
#     self.log.debug("linking")
#     assert(self.pads["srcQueue"].link(self.elements["recBin1"]))
    
    self.elements["recBin2"].add(self.elements["fileQueue2"])
    self.elements["recBin2"].add(self.elements["ph264_2"])
    self.elements["recBin2"].add(self.elements["mux_2"])
    self.elements["recBin2"].add(self.elements["filesink2"])
    
    assert(self.elements["fileQueue2"].link(self.elements["ph264_2"])) 
    assert(self.elements["ph264_2"].link(self.elements["mux_2"])) 
    assert(self.elements["mux_2"].link(self.elements["filesink2"]))
    
    self.elements["recBin2"].add_pad(
                            Gst.GhostPad.new("sink",
                            self.elements["fileQueue2"].get_static_pad("sink")))
    
    self.pipelines["main"].add(self.elements["recBin2"])
    
    
    self.log.debug("change file location")
    self.elements["filesink2"].set_property("location", "/run/media/peter/home/tmp/webcam/test3.mp4")
    
    
    self.elements["srcQueue"].link(self.elements["recBin2"])  
    self.elements["recBin2"].set_state(Gst.State.PLAYING)
    
    
    
    Gst.debug_bin_to_dot_file_with_ts(self.pipelines["catch"], Gst.DebugGraphDetails.ALL, "catch" )
    Gst.debug_bin_to_dot_file_with_ts(self.pipelines["main"], Gst.DebugGraphDetails.ALL, "main" )
    
    ########################################################################### TODO: blockpad has to be a source
    
#     # install new probe for EOS
    self.elements["filesink1"].get_static_pad("sink").add_probe(Gst.PadProbeType.EVENT_DOWNSTREAM, relinkPipeline, self)
     
    # send EOS
#     self.cnt = 0 
#     pad.get_peer().send_event(Gst.Event.new_eos())   
#     Gst.debug_bin_to_dot_file_with_ts(self.pipelines["main"], Gst.DebugGraphDetails.ALL, "main_blocked" )
    
    
    
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
    
    
         
#     self.elements["recBin1"].send_event(Gst.Event.new_eos())  
#     bus = self.elements["recBin1"].get_bus()        
#     msg = bus.timed_pop_filtered (Gst.CLOCK_TIME_NONE, Gst.MessageType.EOS | Gst.MessageType.ERROR)
#      
#     if msg.type == Gst.MessageType.ERROR:
#         self.log.debug("bus message {0}".format(msg.parse_error()))
#         Gst.debug_bin_to_dot_file_with_ts(self.pipelines["main"], Gst.DebugGraphDetails.ALL, "main" )
#         Gst.debug_bin_to_dot_file_with_ts(self.pipelines["catch"], Gst.DebugGraphDetails.ALL, "catch" )
#      
    self.elements["filesink1"].set_state(Gst.State.NULL) 
    self.elements["filesink1"].set_property("location", "/run/media/peter/home/tmp/webcam/test3.mp4")    
    self.elements["filesink1"].set_state(Gst.State.PLAYING) 
    
    Gst.debug_bin_to_dot_file_with_ts(self.pipelines["main"], Gst.DebugGraphDetails.ALL, "main_blocked" )
    
    
#     for [p, pInfo] in self.padProbes:
#         p.remove_probe(pInfo.id)        
    
    return Gst.PadProbeReturn.OK
    
#     self.log.debug("swapping pipeline")
#     # active queue pad
#     aqp = self.elements["fileQueue1"].get_static_pad("sink")
#     # passive queue pad
#     pqp = self.elements["fileQueue2"].get_static_pad("sink")
#     # tee pad
#     tp = aqp.get_peer()
#     # fakesrc pad
#     fp = pqp.get_peer()
        
        

        
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


