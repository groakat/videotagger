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
#         self.pipelines["catch"] = Gst.Pipeline()
        
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


        # gst-launch-1.0 filesrc location="/run/media/peter/home/tmp/webcam/Video 66.mp4" ! qtdemux ! h264parse ! avdec_h264 ! xvimagesink
        self.elements = dict()
        self.elements["src"] = Gst.ElementFactory.make("filesrc", "src")
        self.elements["queue_preview"] = Gst.ElementFactory.make( "queue", "queue_preview")    
        self.elements["demux"] = Gst.ElementFactory.make("qtdemux", "demux")
        self.elements["ph264_1"] = Gst.ElementFactory.make ("h264parse", "ph264_1")
        self.elements["avdec"] = Gst.ElementFactory.make("avdec_h264", "dec")
        self.elements["preview_sink"] = Gst.ElementFactory.make( "autovideosink", "previewsink")
        
        
#         self.elements["filesink1"] = Gst.ElementFactory.make( "filesink", "file_sink1")
#         self.elements["filesink2"] = Gst.ElementFactory.make( "filesink", "file_sink2")
#         self.elements["queue_0"] = Gst.ElementFactory.make( "queue", "queue_0")
#         self.elements["queue_1"] = Gst.ElementFactory.make( "queue", "queue_1")
#         self.elements["queue_2"] = Gst.ElementFactory.make( "queue", "queue_2")
#         self.elements["mp4mux1"] = Gst.ElementFactory.make ( "mp4mux", "mux_1")
#         self.elements["mp4mux2"] = Gst.ElementFactory.make( "mp4mux", "mux_2")
#         self.elements["ph264_1"] = Gst.ElementFactory.make ("h264parse", "ph264_1")
#         self.elements["ph264_2"] = Gst.ElementFactory.make( "h264parse", "ph264_2")
#         self.elements["identity1"] = Gst.ElementFactory.make("identity", "identity_1")
#         self.elements["identity2"] = Gst.ElementFactory.make( "identity", "identity_2")
#         self.elements["audio1"] = Gst.ElementFactory.make( "audiotestsrc", "audio1")
#         self.elements["audio2"] = Gst.ElementFactory.make( "audiotestsrc", "audio2")
#         self.elements["aenc1"] = Gst.ElementFactory.make( "faac", "encodebin1")
#         self.elements["aenc2"] = Gst.ElementFactory.make( "faac", "encodebin2")
        #~ self.elements["jpegFakesink"] = Gst.ElementFactory.make( "fakesink", "jpegFakesink")

#         self.elements["fakesrc"] = Gst.ElementFactory.make( "fakesrc", "fakesrc")
#         self.elements["fakesink"] = Gst.ElementFactory.make( "fakesink", "fakesink")
#         self.elements["queue_catch"] = Gst.ElementFactory.make( "queue", "queue_catch")
#         self.elements["mainFakesink"] = Gst.ElementFactory.make( "fakesink", "mainFakesink")

#         self.elements["t"] = Gst.ElementFactory.make( "tee", "teee")


        if any(self.elements[k] is None for k in self.elements.keys()):
            raise RuntimeError("one or more self.elements could not be created")

        
        self.log.debug("populate main pipeline")
        self.pipelines["main"].add(self.elements["src"])
        self.pipelines["main"].add(self.elements["queue_preview"])
        self.pipelines["main"].add(self.elements["demux"])
        self.pipelines["main"].add(self.elements["ph264_1"])
        self.pipelines["main"].add(self.elements["avdec"])
        self.pipelines["main"].add(self.elements["preview_sink"])
        
        self.log.debug("link self.elements in main pipeline")
        
        assert(self.elements["src"].link(self.elements["demux"]))
#         assert(self.elements["demux"].link(self.elements["ph264_1"]))
        
        self.elements["demux"].connect("pad-added", on_new_decoded_pad)
        assert(self.elements["ph264_1"].link(self.elements["queue_preview"]))
        assert(self.elements["queue_preview"].link(self.elements["avdec"]))
        assert(self.elements["avdec"].link(self.elements["preview_sink"]))
        
        self.log.debug("set filesink location")
        self.elements["src"].set_property("location", "/run/media/peter/home/tmp/webcam/Video 66.mp4")
                
                
        #~ self.log.debug("sleep to wait")
        #~ time.sleep(10)      
        
        
        self.log.debug("done")
        
    def run(self):        
        self.log.debug("start pipeline")
        self.window.show_all()
        # You need to get the XID after window.show_all().  You shouldn't get it
        # in the on_sync_message() handler because threading issues will cause
        # segfaults there.
        self.xid = self.drawingarea.get_property('window').get_xid()
        self.pipelines["main"].set_state(Gst.State.PLAYING)
        Gtk.main()

        
    def quit(self, window):
        self.log.debug("null pipeline")
        
        self.pipelines["main"].set_state(Gst.State.NULL)     
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
        

        
def on_new_decoded_pad(gstObj, pad):
    print "on_new_decoded_pad!", gstObj, pad
    demux = pad.get_parent()
    pipeline = demux.get_parent()
    ph264 = pipeline.get_by_name('ph264_1')
    demux.link(ph264)
#     pipeline.set_state(Gst.State.PAUSED)
    
if __name__ == "__main__":
    vC = pipelineSwap()
    vC.run()


