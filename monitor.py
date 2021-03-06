# -*- coding: utf-8 -*-
"""
Created on Fri Apr  8 11:43:23 2016

@author: sagnac
"""

import sys
from PyQt4 import QtCore,QtGui,uic
import pyqtgraph as pg
import numpy as np

from scipy.optimize import curve_fit

#import os
#if 'LD_LIBRARY_PATH' in os.environ.keys():
#    os.environ['LD_LIBRARY_PATH'] = '/home/sagnac/Quantum/ttag/python/:'+os.environ['LD_LIBRARY_PATH']
#else:
#    os.environ['LD_LIBRARY_PATH'] = '/home/sagnac/Quantum/ttag/python/'
        

sys.path.append('/home/sagnac/Quantum/ttag/python/')
import ttag

qtCreatorFile = 'monitor.ui'

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class Monitor(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        pg.setConfigOption('background', 'w')      # sets background to white                                                 
        pg.setConfigOption('foreground', 'k')      # sets axis color to black 

        self.setupUi(self)
        self.btnStart.clicked.connect(self.Start)
        self.tabWidget.currentChanged.connect(self.SetupView)
        
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.UpdateView)
        
        self.curTab = self.tabWidget.currentIndex()
        self.SetupView(self.curTab)

        self.pltMonitor.setMouseEnabled(x=False,y=False)  
        self.pltAlign.setMouseEnabled(x=False,y=False)  
        self.pltDelay.setMouseEnabled(x=False,y=False)  
        self.pltSingle.setMouseEnabled(x=False,y=False)  
        self.pltCoinc.setMouseEnabled(x=False,y=False)  
        self.pltSingleVis.setMouseEnabled(x=False,y=False)  
        self.pltCoincVis.setMouseEnabled(x=False,y=False)  

        self.inAcq = False

        self.getParameters()
        
    def SetupView(self,index):
        self.curTab = index
        if self.curTab == 0:
            # three state view
            self.txtDelay5.setEnabled(True)
            self.txtDelay6.setEnabled(True)
            # parameters
            self.NumCh = 6
        elif self.curTab == 1:
            # visibility view
            self.txtDelay5.setEnabled(False)
            self.txtDelay6.setEnabled(False)
            # parameters
            self.NumCh = 4
        
    def getParameters(self):
        self.bufNum = int(self.txtBufferNo.text())
        self.delay = np.array([float(self.txtDelay1.text()), float(self.txtDelay2.text()),
                               float(self.txtDelay3.text()),float(self.txtDelay4.text())])
        if self.curTab==0:
            self.delay = np.concatenate( (self.delay,np.array([float(self.txtDelay5.text()),float(self.txtDelay6.text())])) ) 
        
        self.delay = self.delay*1e-9
        
        self.exptime = float(self.txtExp.text())/1000
        self.pause = float(self.txtPause.text())
        self.coincWindow = float(self.txtWindow.text())*1e-9
        
        self.delayRange = float(self.txtRange.text())*1e-9
        
    def Start(self):
        if not self.inAcq:
            self.inAcq = True
            self.txtPause.setEnabled(False)
            self.txtBufferNo.setEnabled(False)
            self.btnStart.setStyleSheet('background-color: red')
            self.btnStart.setText('Stop')

            self.getParameters()
            self.timer.start(self.pause)

            self.ttagBuf = ttag.TTBuffer(self.bufNum)            
            
        else:
            self.timer.stop()
            self.inAcq = False    
            self.txtPause.setEnabled(True)
            self.txtBufferNo.setEnabled(True)
            self.btnStart.setStyleSheet('')
            self.btnStart.setText('Start')   
    
    def UpdateView(self):
        QtGui.qApp.processEvents()
        self.getParameters()
        self.getData()
        self.Monitor()
        self.Align()
        self.CoincView()
        self.SingleView()
        self.UpdateResults()
        self.DelayFunc()
    
    def getData(self):
        self.singles = self.ttagBuf.singles(self.exptime)
        self.coincidences = self.ttagBuf.coincidences(self.exptime,self.coincWindow,-self.delay)
		

    def Monitor(self):
        chs = np.arange(self.NumCh)
        singles = self.singles[:self.NumCh]
        if self.curTab == 0:
            xdict = {0:str(singles[0]),1:str(singles[1]),
                     2:str(singles[2]),3:str(singles[3]),
                     4:str(singles[4]),5:str(singles[5])}
        elif self.curTab == 1:
            xdict = {0:str(singles[0]),1:str(singles[1]),
                     2:str(singles[2]),3:str(singles[3])}
        ax = self.pltMonitor.getAxis('bottom')
        bg = pg.BarGraphItem(x=chs, height=singles, width=0.7, brush='b')
        self.pltMonitor.clear()
        ax.setTicks([xdict.items(), []])
        self.pltMonitor.addItem(bg)

    def Align(self):
        chs=np.arange(3)
        if self.curTab == 0:
            c1 = np.sum(self.singles[0:3])
            c2 = np.sum(self.singles[3:6])
            c12 = np.sum(self.coincidences[0:3,3:6])
        elif self.curTab == 1:
            c1 = np.sum(self.singles[0:2])
            c2 = np.sum(self.singles[2:4])
            c12 = np.sum(self.coincidences[0:2,2:4])
        xdict = {0:str(c1),1:str(c2),2:str(c12)}
        C = np.array([c1,c2,c12])
        ax = self.pltAlign.getAxis('bottom')
        bg = pg.BarGraphItem(x=chs, height=C, width=0.7, brush='b')
        self.pltAlign.clear()
        ax.setTicks([xdict.items(),[]])
        self.pltAlign.addItem(bg)

    def CoincView(self):
        if self.curTab == 0:
            chGood = np.array([1,2,4,5,7,8])
            chErr = np.array([0,3,6])
            count = self.coincidences[0:3,3:6].flatten()
            pltFig = self.pltCoinc
        elif self.curTab == 1:
            chGood = np.array([0,3])
            chErr = np.array([1,2])
            count = self.coincidences[0:2,2:4].flatten()
            pltFig = self.pltCoincVis
        xdict = dict(enumerate(count))
        bgGood = pg.BarGraphItem(x=chGood,height=count[chGood],width=0.7,brush='b')
        bgErr = pg.BarGraphItem(x=chErr,height=count[chErr],width=0.7,brush='r')
        ax = pltFig.getAxis('bottom')
        pltFig.clear()
        ax.setTicks([xdict.items(), []])
        pltFig.addItem(bgGood)
        pltFig.addItem(bgErr)

    def SingleView(self):
        chs = np.arange(self.NumCh)
        if self.curTab == 0:
            count = np.concatenate( (np.sum(self.coincidences[0:3,3:6],axis=1), np.sum(self.coincidences[0:3,3:6],axis=0)) )
            pltFig = self.pltSingle
        elif self.curTab == 1:
            count = np.concatenate( (np.sum(self.coincidences[0:2,2:4],axis=1), np.sum(self.coincidences[0:2,2:4],axis=0)) )
            pltFig = self.pltSingleVis
        xdict = dict(enumerate(count))
        bg = pg.BarGraphItem(x=chs,height=count,width=0.7,brush='b')
        ax = pltFig.getAxis('bottom')
        pltFig.clear()
        ax.setTicks([xdict.items(), []])
        pltFig.addItem(bg)

    def UpdateResults(self):
        if self.curTab == 0:
            rate = np.sum(self.coincidences[0:3,3:6])/self.exptime
            # print rate and QBER
            self.lblRate.setText("{:.2f}".format(rate).rstrip('00').rstrip('.'))
            if rate != 0:
                qber = np.sum(np.diag(self.coincidences[0:3,3:6]))/(rate*self.exptime)
                self.lblQBER.setText("{:.4f}".format(qber))
            else:
                self.lblQBER.setText('###')
        elif self.curTab == 1:
            if np.sum(self.coincidences[0:2,2:4]):
                visRaw = 1 - 2*(self.coincidences[0,2]+self.coincidences[1,3])/np.sum(self.coincidences[0:2,2:4])
                self.lblVis.setText("{:.4f}".format(visRaw))
            else:
                self.lblVis.setText("###")
            C_acc = np.maximum( np.array( [self.singles[0]*self.singles[2:4],self.singles[1]*self.singles[2:4]] ), np.zeros( (2,2) ) )*2*self.coincWindow/self.exptime
            C_noacc = np.maximum( self.coincidences[0:2,2:4] - C_acc, np.zeros( (2,2) ) )
            if np.sum(C_noacc):
                visNet = 1 - 2*(C_noacc[0,0]+C_noacc[1,1])/np.sum(C_noacc)
                self.lblVisNet.setText("{:.4f}".format(visNet))
            else:
                self.lblVisNet.setText("###")





    def DelayFunc(self):
        # data analysed the old way to get delay range plot
        lastTag = np.max(self.ttagBuf.rawtags)
        firstTag = (lastTag - np.int(np.ceil(self.exptime/self.ttagBuf.resolution))).astype(np.uint64)
        rawPos = np.nonzero(np.bitwise_and(self.ttagBuf.rawtags>firstTag,self.ttagBuf.rawtags<lastTag))[0]
        rawTags = self.ttagBuf.rawtags[rawPos]
        rawChan = self.ttagBuf.rawchannels[rawPos]
        rawAll = np.vstack( (rawTags,rawChan) )
        newAll = np.sort(rawAll,axis=0)
        newTags = rawAll[0]
        newChan = rawAll[1]
        # filter data to plot
        selDelay = self.cmbChannels.currentIndex()
        if selDelay > 8:
            selTags = newTags
            selChan = newChan
        else:
            if self.curTab == 0:
                ch1 = np.array([0,0,0,1,1,1,2,2,2])
                ch2 = np.array([3,4,5,3,4,5,3,4,5])
            elif self.curTab == 1:
                ch1 = np.array([0,0,0,1,1,1,-1,-1,-1])
                ch2 = np.array([2,3,-1,2,3,-1,2,3,-1])
            selPos = np.nonzero( np.bitwise_or(newChan == ch1[selDelay],newChan == ch2[selDelay]) )[0]
            selTags = newTags[selPos]
            selChan = newChan[selPos]
        # add delays to tags
        selTags = selTags + np.around(self.delay[selChan]/self.ttagBuf.resolution).astype(np.int64)
        # compute delay histogram
        delayEdges = np.arange( -np.around(self.delayRange/self.ttagBuf.resolution).astype(np.int32) , np.around(self.delayRange/self.ttagBuf.resolution).astype(np.int32), 2 )

        selTags = selTags.astype(np.int64)
        selChan = selChan.astype(np.int8)

        if selDelay > 8:
            if self.curTab == 0:
                chMap = np.array([0,0,0,1,1,1])
            elif self.curTab == 1:
                chMap = np.array([0,0,1,1])
            selChan = chMap[selChan]

        t12diff = np.diff(selTags)
        chdiff = np.diff(selChan)

        t12diff = t12diff[chdiff!=0]*np.sign(chdiff[chdiff!=0])

        count,bins = np.histogram(t12diff,bins=delayEdges,range=(np.amin(delayEdges),np.amax(delayEdges)))
        binCenter = (bins[1:]+bins[:-1])/2
        delays = binCenter * self.ttagBuf.resolution * 1e9

        bg = pg.BarGraphItem(x=delays,height=count,width=0.1,brush='b')
        self.pltDelay.clear()
        
        # fit results if the fit box is checked
        if self.chkFit.isChecked():
            gaussian = lambda x,A,x0,s: A*np.exp(-(x-x0)**2/(2*s**2))
            p0 = [np.max(count),delays[np.argmax(count)],0.3]
            popt,perr = curve_fit(gaussian,delays,count,p0=p0)
            x = np.linspace(np.amin(delays),np.amax(delays),1000)
            yfit = gaussian(x,*popt)
            self.pltDelay.plot(x,yfit,pen='r')
            self.lblMean.setText("{:.4f}".format(popt[1]))
            self.lblStd.setText("{:.4f}".format(popt[2]))

        self.pltDelay.addItem(bg)
		

            
            
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = Monitor()
    window.show()
    sys.exit(app.exec_())
