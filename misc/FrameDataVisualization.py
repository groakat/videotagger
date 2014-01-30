import matplotlib as mpl  
import matplotlib.pyplot as plt
import numpy as np

class FrameDataVisualizationTree:
    def __init__(self):
        self.resetAllSamples()
        
    
    def resetAllSamples(self):
        self.tree = dict()    
        
    
    def generateRandomSequence(self, dayRng, hourRng, minuteRng, frameRng):
        for day in dayRng:
            for hour in hourRng:
                for minute in minuteRng:
                    minMax = np.random.rand(1)[0]
                    for frame in frameRng:
                        data = np.random.rand(1)[0] * minMax
                        self.addSample(day, hour, minute, frame, data)
                        
    
    
    def verifyStructureExists(self, day, hour, minute, frame):                              
        if day not in self.tree.keys():
            self.tree[day] = dict()
            self.tree[day]['max'] = -np.Inf
            
        if hour not in self.tree[day].keys():
            self.tree[day][hour] = dict()
            self.tree[day][hour]['max'] = -np.Inf
            
        if minute not in self.tree[day][hour].keys():
            self.tree[day][hour][minute] = dict()
            self.tree[day][hour][minute]['max'] = -np.Inf
        
        
    def updateMax(self, day, hour, minute, data):
#         data = self.tree[day][hour][minute][frame]  
            
        if self.tree[day][hour][minute]['max'] < data:
            self.tree[day][hour][minute]['max'] = data
                
            if self.tree[day][hour]['max'] < data:
                self.tree[day][hour]['max'] = data
            
                if self.tree[day]['max'] < data:
                    self.tree[day]['max'] = data
        
        
    def addSample(self, day, hour, minute, frame, data):
        self.verifyStructureExists(day, hour, minute, frame)
        
        if frame in self.tree[day][hour][minute].keys():
            self.replaceSample(day, hour, minute, frame, data)
        else:     
            self.insertSample(day, hour, minute, frame, data)
            
            
    def insertSample(self, day, hour, minute, frame, data):
        self.tree[day][hour][minute][frame] = data
        self.updateMax(day, hour, minute, data) 
        
    
    def replaceSample(self,day, hour, minute, frame, data):
        oldData = self.tree[day][hour][minute][frame]    
        self.tree[day][hour][minute][frame] = data
        
        if oldData == self.tree[day][hour][minute]['max']: 
            newMax = np.max([self.tree[day][hour][minute][k] \
                        for k in self.tree[day][hour][minute].keys()])
            self.updateMax(day, hour, minute, newMax)
        else:
            self.updateMax(day, hour, minute, data)
            
        
    def generateConfidencePlotData(self, day, hour, minute, frame, frameResolution=1):
        self.plotData = dict()
        self.generatePlotDataDays(day, hour, minute, frame)
        self.generatePlotDataHours(day, hour, minute, frame)
        self.generatePlotDataMinutes(day, hour, minute, frame)
        self.generatePlotDataFrames(day, hour, minute, frame, frameResolution)
        
        
    def generatePlotDataDays(self, day, hour, minute, frame):
        self.plotData['days'] = dict()
        self.plotData['days']['data'] = []
        self.plotData['days']['tick'] = []
        for key in sorted(self.tree.keys()):
            if key == 'max':
                continue
                
            self.plotData['days']['data'] += [self.tree[key]['max']]
            self.plotData['days']['tick'] += [key]
            
            
    def generatePlotDataHours(self, day, hour, minute, frame):
        self.plotData['hours'] = dict()
        self.plotData['hours']['data'] = []
        self.plotData['hours']['tick'] = []
        for key in sorted(self.tree[day].keys()):
            if key == 'max':
                continue
                
            self.plotData['hours']['data'] += [self.tree[day][key]['max']]
            self.plotData['hours']['tick'] += [key]    
            
            
    def generatePlotDataMinutes(self, day, hour, minute, frame):
        self.plotData['minutes'] = dict()
        self.plotData['minutes']['data'] = []
        self.plotData['minutes']['tick'] = []
        for key in sorted(self.tree[day][hour].keys()):
            if key == 'max':
                continue
                
            self.plotData['minutes']['data'] += [self.tree[day][hour][key]['max']]
            self.plotData['minutes']['tick'] += [key]
            
            
    def generatePlotDataFrames(self, day, hour, minute, frame, frameResolution=1):
        self.plotData['frames'] = dict()
        self.plotData['frames']['data'] = []
        self.plotData['frames']['tick'] = []
        cnt = 0
        for key in sorted(self.tree[day][hour][minute].keys()):
            if key == 'max':
                continue
            
            if cnt == 0:               
                tmpVal = 0
                tmpKeys = []
            
            if cnt < frameResolution:
                tmpVal += self.tree[day][hour][minute][key]
                tmpKeys += [key]
                cnt += 1
            else:
                tmpVal /= frameResolution
                self.plotData['frames']['data'] += [tmpVal]
                self.plotData['frames']['tick'] += [tmpKeys]
                cnt = 0
                
        if cnt != 0:
            tmpVal /= cnt
            self.plotData['frames']['data'] += [tmpVal]
            self.plotData['frames']['tick'] += [tmpKeys]
            
            
        
class FrameDataView:    
    def __init__(self, figs=None, fdvTree=None, frameResolution=1):
        """
        figs (dict):
                {'days': figure representing visualization for days,
                 'hours': figure representing visualization for hours,
                 'minutes': figure representing visualization for minutes,
                 'frames': figure representing visualization for frames}
                 
                 if None, figures will be created automatically
                 
        frameResolution (int):
                    used for summarization in plots of the frames
                    
        """
        if fdvTree == None:
            self.fdvTree = FrameDataVisualizationTree()
        else:
            self.fdvTree = fdvTree
            
        if figs == None:
            self.configureFigures()
        else:
            self.figs = figs           
        
        self.frameResolution = 1
        self.initializeColours()
        
        self.cbDays = dict()
        self.cbHours = dict()
        self.cbMinutes = dict()
        self.cbFrames = dict()
        
        self.day = None
        self.hour = None
        self.minute = None
        self.frame= None
        
    def configureFigures(self):
        
        self.figs = dict()
        
        self.figs['days'] = self.createFigure()
        self.figs['hours'] = self.createFigure()
        self.figs['minutes'] = self.createFigure()
        self.figs['frames'] = self.createFigure()        
        
    def initializeColours(self):
        # color dict for bar plots
        self.cdict = {'red': ((0.0, 1, 1),
                             (0.5, 1, 1),
                             (1.0, 0.7, 0.7)),
                     'green': ((0.0, 1, 1),
                               (0.5, 0.5, 0.5),
                               (1.0, 0, 0)),
                     'blue': ((0.0, 1, 1),
                              (0.5, 0.5, 0.5),
                              (1.0, 0, 0))} 
        
    def createFigure(self):
        figSize = (10, 0.2)
        fig = plt.figure(figsize=figSize, dpi=72, 
                     facecolor=(1,1,1), edgecolor=(0,0,0), frameon=False)
        ax = fig.add_subplot(111)        
        ax.set_axis_off()
        
        return fig
    
        
    def linkFigureDays(self, fig):
        self.figs['days'] = fig
#         for event in [  'button_press_event',
#                         'button_release_event',
#                         'draw_event',
#                         'key_press_event',
#                         'key_release_event',
#                         'motion_notify_event', 
#                         'pick_event' ,
#                         'resize_event',
#                         'scroll_event',
#                         'figure_enter_event',
#                         'figure_leave_event',
#                         'axes_enter_event',
#                         'axes_leave_event']:
#             self.figs['days'].canvas.mpl_connect(event, self.callbackWrapperDays)
    
        
    def linkFigureHours(self, fig):
        self.figs['hours'] = fig
    
        
    def linkFigureMinutes(self, fig):
        self.figs['minutes'] = fig
    
        
    def linkFigureFrames(self, fig):
        self.figs['frames'] = fig
        
            
    def getFigureHandles(self):
        return self.figs
    
                   
    def registerMPLCallback(self, figKey, event, callbackFunction):
        """
        figKey (String):
                    'days', 'hours', 'minutes' or 'frames'
                    
        event (String):
            any of the matplotlib figure events:
                'button_press_event'    MouseEvent - mouse button is pressed
                'button_release_event'    MouseEvent - mouse button is released
                'draw_event'    DrawEvent - canvas draw
                'key_press_event'    KeyEvent - key is pressed
                'key_release_event'    KeyEvent - key is released
                'motion_notify_event'    MouseEvent - mouse motion
                'pick_event'    PickEvent - an object in the canvas is selected
                'resize_event'    ResizeEvent - figure canvas is resized
                'scroll_event'    MouseEvent - mouse scroll wheel is rolled
                'figure_enter_event'    LocationEvent - mouse enters a new figure
                'figure_leave_event'    LocationEvent - mouse leaves a figure
                'axes_enter_event'    LocationEvent - mouse enters a new axes
                'axes_leave_event'    LocationEvent - mouse leaves an axes
                
        callbackFunction (function pointer):
            function to be called by the callback
            function should take four arguments which are
                callbackFunction(day, hour, minute, frame)
        """
        
        if figKey not in self.figs.keys():
            raise ValueError("figKey has to be 'days', 'hours', 'minutes' or 'frames'")
        
        if figKey == 'days':
            if event not in self.cbDays.keys():
                self.cbDays[event] = []
                self.figs[figKey].canvas.mpl_connect(event, 
                                                     self.callbackWrapperDays)
            self.cbDays[event] += [callbackFunction]
        
        if figKey == 'hours':
            if event not in self.cbHours.keys():
                self.cbHours[event] = []
                self.figs[figKey].canvas.mpl_connect(event, 
                                                     self.callbackWrapperHours)
            self.cbHours[event] += [callbackFunction]
        
        if figKey == 'minutes':
            if event not in self.cbMinutes.keys():
                self.cbMinutes[event] = []
                self.figs[figKey].canvas.mpl_connect(event, 
                                                    self.callbackWrapperMinutes)
            self.cbMinutes[event] += [callbackFunction]
        
        if figKey == 'frames':
            if event not in self.cbFrames.keys():
                self.cbFrames[event] = []
                self.figs[figKey].canvas.mpl_connect(event, 
                                                     self.callbackWrapperFrames)
            self.cbFrames[event] += [callbackFunction]
    
    
    def callbackWrapperDays(self, event):
        print 'DAY: button={0}, x={1}, y={2}, xdata={3}, ydata={4}, name={5}'.format(
                    event.button, event.x, event.y, event.xdata, event.ydata,
                    event.name)
        
        if event.name in self.cbDays.keys():
            for cb in self.cbDays[event.name]:
                cb(np.floor(event.xdata), None, None, None)
    
    
    def callbackWrapperHours(self, event):
        print 'HOURS: button={0}, x={1}, y={2}, xdata={3}, ydata={4}, name={5}'.format(
                    event.button, event.x, event.y, event.xdata, event.ydata,
                    event.name)
        
        if event.name in self.cbHours.keys():
            for cb in self.cbHours[event.name]:
                cb(self.day, np.floor(event.xdata), None, None)
    
    
    def callbackWrapperMinutes(self, event):
        print 'MINUTES: button={0}, x={1}, y={2}, xdata={3}, ydata={4}, name={5}'.format(
                    event.button, event.x, event.y, event.xdata, event.ydata,
                    event.name)
        
        if event.name in self.cbMinutes.keys():
            for cb in self.cbMinutes[event.name]:
                cb(self.day, self.hour,  np.floor(event.xdata), None)
    
    
    def callbackWrapperFrames(self, event):
        print 'FRAME: button={0}, x={1}, y={2}, xdata={3}, ydata={4}, name={5}'.format(
                    event.button, event.x, event.y, event.xdata, event.ydata,
                    event.name)
        frame = np.floor(event.xdata) * self.frameResolution
        
        if event.name in self.cbFrames.keys():
            for cb in self.cbFrames[event.name]:
                cb(self.day, self.hour,  self.minute, frame)
        
                   
    def plotColorCodedBar(self, data, ax):
        fig = plt.figure(ax.get_figure().number)
        plt.cla()     
        cm = mpl.colors.LinearSegmentedColormap('my_colormap',self.cdict, 256)
        cnt = 0
        for datum in data:
            ax.bar(cnt, datum, 1, color=cm(datum), edgecolor=(0,0,0,0))
            cnt += 1
        ax.set_axis_off()
    
    def plotConfidence(self, day, hour, minute, frame, frameResolution=None):
        """
        frameResolution (int):
                    if None, standard (constructor) frameResolution will be
                    used for generateConfidenceData
        """
        if frameResolution is not None:
            self.frameResolution = frameResolution
            
        self.day = day
        self.hour = hour
        self.minute = minute
            
        self.fdvTree.generateConfidencePlotData(day, hour, minute, frame, 
                                                self.frameResolution)
            
        ax = self.figs['days'].axes[0]
        data = self.fdvTree.plotData['days']['data']
        self.plotColorCodedBar(data, ax)   
        
        ax = self.figs['hours'].axes[0]
        data = self.fdvTree.plotData['hours']['data']
        self.plotColorCodedBar(data, ax)
        
        ax = self.figs['minutes'].axes[0]
        data = self.fdvTree.plotData['minutes']['data']
        self.plotColorCodedBar(data, ax)
        
        ax = self.figs['frames'].axes[0]
        data = self.fdvTree.plotData['frames']['data']
        self.plotColorCodedBar(data, ax)
        
        
        