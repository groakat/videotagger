import matplotlib as mpl  
import matplotlib.pyplot as plt
import numpy as np
import cPickle as pickle

class FrameDataVisualizationTree:
    def __init__(self):
        self.resetAllSamples()
        
    
    def resetAllSamples(self):
        self.tree = dict()    
        
        
    def save(self, filename):
        with open(filename, "wb") as f:
            pickle.dump(self.tree, f)
            
    def load(self, filename):
        with open(filename, "rb") as f:
            self.tree = pickle.load(f) 
    
    def generateRandomSequence(self, dayRng, hourRng, minuteRng, frameRng):
        for day in dayRng:
            for hour in hourRng:
                for minute in minuteRng:
                    minMax = np.random.rand(1)[0]
                    for frame in frameRng:
                        if np.random.rand(1)[0] > 0.9:
                            data = 0.999999
                        else:
                            data = np.random.rand(1)[0] * minMax
                        self.addSample(day, hour, minute, frame, data)
                        
    
    
    def verifyStructureExists(self, day, hour, minute, frame):                              
        if day not in self.tree.keys():
            self.tree[day] = dict()
            self.tree[day]['max'] = -np.Inf
            self.tree[day]['mean'] = 0
            self.tree[day]['sampleN'] = 0
            
        if hour not in self.tree[day].keys():
            self.tree[day][hour] = dict()
            self.tree[day][hour]['max'] = -np.Inf
            self.tree[day][hour]['mean'] = 0
            self.tree[day][hour]['sampleN'] = 0
            
        if minute not in self.tree[day][hour].keys():
            self.tree[day][hour][minute] = dict()
            self.tree[day][hour][minute]['max'] = -np.Inf
            self.tree[day][hour][minute]['mean'] = 0
            self.tree[day][hour][minute]['sampleN'] = 0
        
        
    def updateMax(self, day, hour, minute, data):
#         data = self.tree[day][hour][minute][frame]  
            
        if self.tree[day][hour][minute]['max'] < data:
            self.tree[day][hour][minute]['max'] = data
                
            if self.tree[day][hour]['max'] < data:
                self.tree[day][hour]['max'] = data
            
                if self.tree[day]['max'] < data:
                    self.tree[day]['max'] = data
        
    
    def incrementMean(self, prevMean, data, n):
        return prevMean + (1.0/n) * (data - prevMean)
    
    
    def addSampleToStumpMean(self, stump, data):
        stump['mean'] = self.incrementMean(stump['mean'], 
                                           data,
                                           stump['sampleN'] + 1)
        stump['sampleN'] += 1
        
    
    def addSampleToMean(self, day, hour, minute, data):
        self.addSampleToStumpMean(self.tree[day][hour][minute], data)
        self.addSampleToStumpMean(self.tree[day][hour], data)
        self.addSampleToStumpMean(self.tree[day], data)
    
        
    def addSample(self, day, hour, minute, frame, data):
        self.verifyStructureExists(day, hour, minute, frame)
        # using try, except because its much fast than looking up the keys
        try:
            oldData = self.tree[day][hour][minute][frame]
            self.replaceSample(day, hour, minute, frame, data, oldData)
        except KeyError:
            self.insertSample(day, hour, minute, frame, data)
            
            
    def insertSample(self, day, hour, minute, frame, data):
        self.tree[day][hour][minute][frame] = data
        self.updateMax(day, hour, minute, data)
        self.addSampleToMean(day, hour, minute, data)
        
    
    def replaceSample(self,day, hour, minute, frame, data, oldData):
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
        self.plotData['days']['weight'] = []
        self.plotData['days']['tick'] = []
        for key in sorted(self.tree.keys()):
            if key in ['max', 'mean', 'sampleN']:
                continue
                
            self.plotData['days']['data'] += [self.tree[key]['max']]
            self.plotData['days']['weight'] += [self.tree[key]['mean']]
            self.plotData['days']['tick'] += [key]
            
            
    def generatePlotDataHours(self, day, hour, minute, frame):
        self.plotData['hours'] = dict()
        self.plotData['hours']['data'] = []
        self.plotData['hours']['weight'] = []
        self.plotData['hours']['tick'] = []
        for key in sorted(self.tree[day].keys()):
            if key in ['max', 'mean', 'sampleN']:
                continue
                
            self.plotData['hours']['data'] += [self.tree[day][key]['max']]
            self.plotData['hours']['weight'] += [self.tree[day][key]['mean']]
            self.plotData['hours']['tick'] += [key]    
            
            
    def generatePlotDataMinutes(self, day, hour, minute, frame):
        self.plotData['minutes'] = dict()
        self.plotData['minutes']['data'] = []
        self.plotData['minutes']['weight'] = []
        self.plotData['minutes']['tick'] = []
        for key in sorted(self.tree[day][hour].keys()):
            if key in ['max', 'mean', 'sampleN']:
                continue
                
            self.plotData['minutes']['data'] += \
                                            [self.tree[day][hour][key]['max']]
            self.plotData['minutes']['weight'] += \
                                            [self.tree[day][hour][key]['mean']]
            self.plotData['minutes']['tick'] += [key]
            
            
    def generatePlotDataFrames(self, day, hour, minute, frame, 
                               frameResolution=1):
        self.plotData['frames'] = dict()
        self.plotData['frames']['data'] = []
        self.plotData['frames']['weight'] = []
        self.plotData['frames']['tick'] = []
        cnt = 0
        for key in sorted(self.tree[day][hour][minute].keys()):
            if key in ['max', 'mean', 'sampleN']:
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
                self.plotData['frames']['weight'] += [tmpVal]
                self.plotData['frames']['tick'] += [tmpKeys]
                cnt = 0
                
        if cnt != 0:
            tmpVal /= cnt
            self.plotData['frames']['data'] += [tmpVal]
            self.plotData['frames']['weight'] += [tmpVal]
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
        
                   
    def plotColorCodedBar(self, data, ax, weight=None):
        if weight is None:
            weight = data
            
        fig = plt.figure(ax.get_figure().number)
        plt.cla()     
        cm = mpl.colors.LinearSegmentedColormap('my_colormap',self.cdict, 256)
        for i in range(len(data)):
            ax.bar(i, data[i], 1, color=cm(weight[i]), edgecolor=(0,0,0,0))
        ax.set_axis_off()
        plt.ylim(0, 1)
    
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
        weight = self.fdvTree.plotData['days']['weight']
        self.plotColorCodedBar(data, ax, weight)   
        
        ax = self.figs['hours'].axes[0]
        data = self.fdvTree.plotData['hours']['data']
        weight = self.fdvTree.plotData['hours']['weight']
        self.plotColorCodedBar(data, ax, weight)
        
        ax = self.figs['minutes'].axes[0]
        data = self.fdvTree.plotData['minutes']['data']
        weight = self.fdvTree.plotData['minutes']['weight']
        self.plotColorCodedBar(data, ax, weight)
        
        ax = self.figs['frames'].axes[0]
        data = self.fdvTree.plotData['frames']['data']
        self.plotColorCodedBar(data, ax)
        
        
        