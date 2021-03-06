#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 10 16:05:45 2020

@author: jenny
"""

# %%
# import python modules
from pymatreader import read_mat
import numpy as np
import scipy.signal as signal
from scipy import linalg
from scipy.io import savemat
from matplotlib import pyplot as plt
from scipy.fftpack import fft2
from scipy.fftpack import fft
from scipy import signal
#%%
# import lab modules
import timeop
import diffusion
#%%
#def getSSVEPfreq(photocell):
        # get photocell signals

def getSSVEP(data,sr,window,ssvep_freq,goodtrials,goodchans):
    #create empty dictionary for output
    SSVEP = dict();
    #some renaming
    startsamp = window[0]
    endsamp = window[1]
    epochlength = data.shape[0]
    nchan = data.shape[1]
    ntrial = data.shape[2]
    # average erp.
    erp = np.mean(data[:, :, goodtrials], axis=2)    
    # FFT the ERPs
    # remove the mean
    erpmean = np.tile(np.mean(erp, axis=0), [epochlength, 1])
    erp = erp - erpmean
    #take fft over prescribed window    
    erpf = fft(erp[startsamp:endsamp, :], axis=0)/(endsamp-startsamp) # raw fft     
    binwidth = int((endsamp-startsamp)/sr)
    u,s,vh = linalg.svd(erpf[(ssvep_freq-1)*binwidth:(ssvep_freq+1)*binwidth+1,goodchans])
    snr = 2*np.abs(u[1,:])/(np.abs(u[0,:]+u[2,:]))
    snrflagsignal = 1
    if np.max(snr) < 1:
        print('Warning NO SSVEP detected at stimulus frequency')
        snrflagsignal = 0
    
    weights = np.zeros((nchan,1),dtype=complex)

	# This is an optimal set of weights to estimate 30 hz signal. 
    weights[goodchans,0] = np.matrix.transpose(vh[0,:])

	# lets test it on the same interval using weighted electrode vs. original
    erpproject = np.matmul(erpf, weights)
     
    # Now use the weights to loop through indivial trials 
    trialestimate = np.zeros((endsamp-startsamp,ntrial),dtype=complex)

    for trial in goodtrials: 
        trialdata = np.squeeze(data[startsamp:endsamp,:,trial])
        trialfft = fft(trialdata,axis=0)
        trialproject = np.matmul(trialfft,weights)
        trialestimate[:,trial] = trialproject[:,0] #new coefficients
   
    SSVEP['goodtrials'] = goodtrials
    SSVEP['goodchannels'] = goodchans
    SSVEP['sr'] = sr;
    SSVEP['ssvep_freq'] = ssvep_freq
    SSVEP['samplerange'] = window
    SSVEP['erp_fft'] = erpf
    SSVEP['svdspectrum'] = u
    SSVEP['svdchan'] = vh[0:2,:]
    SSVEP['snr'] = snr
    SSVEP['snrflag'] = snrflagsignal
    SSVEP['projectspectrum'] = erpproject
    SSVEP['singletrial'] = trialestimate
    SSVEP['weights'] = weights
    return SSVEP
    

#%%
# globals
def SSVEP_task3(subID):
    currentSub = subID[0:4]
    print('Current Subject: ', currentSub)
    pcdict = read_mat(path + subID + '_task3_photocells.mat')
    datadict = read_mat(path + subID + '_task3_final.mat')
    behavdict = read_mat(path + subID[0:4] + '_behavior_final.mat')

    data = np.array(datadict['data'])

    artifact = np.array(datadict['artifact'])
    sr = np.array(datadict['sr'])
    beh_ind = np.array(behavdict['trials'])

    # open up indices
    artifact0 = artifact.sum(axis=0)
    artifact1 = artifact.sum(axis=1)

    # identify goodtrials and good channels.
    goodtrials = np.squeeze(np.array(np.where(artifact0 < 20)))
    goodchans = np.squeeze(np.array(np.where(artifact1 < 40)))

    # BehEEG_int = list(set(beh_ind) & set(goodtrials))
    finalgoodtrials = np.array(diffusion.compLists(beh_ind, goodtrials))
    # finalgoodtrials = np.array(BehEEG_int)
    


    p = pcdict['photostim']
    n = pcdict['photonoise']
    photocell_ssvep = dict()
    # FFT the photocells stimulus
    

    window = [1250,2250]
    
    stimulus_ssvep = getSSVEP(data,sr,window,30,finalgoodtrials,goodchans)
    noise_ssvep = getSSVEP(data,sr,window,40,finalgoodtrials,goodchans)
    
    yfp = fft(p[1250:2250,:], axis=0)
    yfn = fft(n[1250:2250,:], axis=0)
    photocell_ssvep['stim'] = p
    photocell_ssvep['noise'] = n
    SSVEP['stim_fft'] = yfp
    SSVEP['noise_fft'] = yfn

    
    return stimulus_ssvep, noise_ssvep, photocell_ssvep
#%%
#JENNY - YOU NEED TO MAKE USE OF SOME OF THE STUFF HERE.  SPECIFICALLY, diffusion.choose_subs selects
#a subset of 36 subjects, and sets aside 12 subjects for model testing.  Also, dont know how you want to 
#save the three ssvep structures for each subject. 
#Finally, to do the time-frequency analysis, I dont think a wavelet will work, because we need to precisely align 
#to external events and align windows across frequencies.  But well have to try it.  I think FFT of 100 ms windows amd 
#possibly Hilbert Transform will work.  First we should try it on average ERP.  
#I think it will be almost impossible to do the time course on single trials.  But it might work to contrast subjects
# or to contrast quantiles of RT. 
#LASTLY, YOU need to make a separate script that makes any plots you need. 
#debug = True
#lvlAnalysis = 1
#path = '/home/jenny/pdmattention/task3/'
#subIDs = diffusion.choose_subs(lvlAnalysis, path)
#subIDs.remove('s181_ses1_')
#subIDs.remove('s223_ses1_')
#subIDs2 = ['s181_ses1']
#
#for subID in subIDs2:
#    ssvep_stimulus,ssvep_noise, ssvep_photocell = SSVEP_task3(subID)
#    outname = path+subID+'_stimulus_SSVEP.mat'
#    savemat(outname,)            

#%%





    #    This is just trying to  fft each channel
    #    trialestimate = np.zeros((4000,129,360))
    #    for trial in finalgoodtrials: 
    #        trialdata = np.squeeze(data[:,:,trial])
    #        trialdata = trialdata * np.transpose(weightsn)
    #        trialestimate[:,:,trial] = trialdata[:,:]
    #    
    #    # find the onset of noise for each trial
    #    noise = pcdict['photonoise']
    #    noisetrialestimate = np.zeros((1000,129,360))
    #    for i in finalgoodtrials:
    #        firstind = np.argmax(noise[:, i] > 0)
    #        lastind = firstind + 1000
    #        noisetrialestimate[:,:,i] = trialestimate[firstind:lastind,:,i]
        
    #
    #        # FFT the photocells
    #    plt.subplot(322)
    #    for x in range(0,numtrials):
    #        y = p[1250:2249,x]
    #        N = len(y)
    #        yf = fft(y)
    #        xf = np.linspace(0.0, sr/2, N//2)
    #        plt.plot(xf[0:100], 2/N * np.abs(yf[0:100]))
    #    plt.grid()
    #    plt.title('Photocell Stimulus')
    #
    #        # FFT the noise
    #    noisesignals = []
    #    plt.subplot(324)
    #    for x in range(0,numtrials):
    #        firstind = np.argmax(n[:,x]>0)
    #        lastind = firstind + 1500
    #        noisesignal = n[firstind:lastind,x]
    #        N = len(noisesignal)
    #        yn = fft(noisesignal)
    #        xn = np.linspace(0.0, sr/2, N//2)
    #        plt.plot(xn[0:100], 2/N * np.abs(yn[0:100]))
    #    plt.grid()
    #    plt.title('Photocell Noise')
    #
    #        # FFT the for erp
    #    plt.subplot(326)
    #    for x in range(0,129):
    #        y = erp[1250:2249,x]
    #        N = len(y)
    #        yf = fft(y)
    #        xf = np.linspace(0.0, sr/2, N//2)
    #        plt.plot(xf[0:60], 2/N * np.abs(yf[0:60]))
    #        plt.title('ERP')
    #    plt.grid()


# %%
# globals
SSVEP = getSSVEP(subID)

#%%
## %% Plots
#
 #photocell stimulus 

 plt.figure()
 plt.subplot(411)
 npc = len(yfp)
 xfp = np.linspace(0.0, sr / 2, npc // 2)
 plt.plot(xfp[0:100], 2 / npc * np.abs(yfp[0:100, :]))
 plt.title('Photocell Stimulus using fft')
 plt.xticks(np.arange(min(xfp[0:100]), max(xfp[0:100]) + 1, 10))

 #photocell noise

 plt.subplot(412)
 nn = len(noisesignal)
 xn = np.linspace(0.0, sr / 2, nn // 2)
 plt.plot(xn[0:100], 2 / nn * np.abs(yfn[0:100]))
 plt.title('Photocell Noise fft')
 plt.xticks(np.arange(min(xn[0:100]), max(xn[0:100]) + 1, 10))

    
 #ERP after stim
 plt.subplot(413)
 nerp = len(yferp)
 xf = np.linspace(0.0, sr / 2, (nerp // 2 + 1))
 xfplot = xf[8*int(len(xf)/nyquist):51*int(len(xf)/nyquist)]
 yfplot = yferp[8*int(len(xf)/nyquist):51*int(len(xf)/nyquist)]
 plt.plot(xfplot, (2 * np.abs(yfplot)) ** 2)
 plt.title('ERP (matched with onset of stimulus) for %i ms' % nerp)
 plt.xticks(np.arange(min(xf[0:60]), max(xf[0:60]) + 1, 10))    

 #ERP after noise
plt.subplot(414)
nerpn = len(erpnoise)  
xferpn = np.linspace(0.0, sr / 2, nerpn // 2 +1)
xferpnplot = xferpn[8*int(len(xferpn)/nyquist):51*int(len(xferpn)/nyquist)]
yferpnplot = yferpn[8*int(len(xferpn)/nyquist):51*int(len(xferpn)/nyquist)]
plt.plot(xferpnplot, (2 * np.abs(yferpnplot)) ** 2)
plt.title('ERP fft(matched with onset of noise) for %i ms' % erpdur)
plt.xticks(np.arange(min(xferpn[0:60]), max(xferpn[0:60]) + 1, 10))
                            
plt.tight_layout()
plt.show
#
#    # optimal channel to detect noise (40Hz)
#    # 35Hz-45Hz bin (1000ms)    
#    ferpn = fft(erpnoise, axis=0) # raw fft
#    binwidth = int((len(erpnoise)/2 + 1)/nyquist)
#    ferpn = ferpn[35*binwidth:45*binwidth +1]
#    u,s,vh = linalg.svd(ferpn[:,goodchan])
#    
#    weightsn = np.zeros((129,1),dtype=complex)
#
#	# This is an optimal set of weights to estimate 35-45hz signal. 
#    weightsn[goodchan,0] = np.matrix.transpose(vh[0,:])
#
#	# lets test it on the same interval using weighted electrode vs. original
#    plt.figure()
#    plt.subplot(311)
#    yftest = fft(erpnoise, axis=0) 
#    erpnoisetest = np.matmul(yftest,weightsn)
#    xferpn = np.linspace(0.0, nyquist, nerpn // 2 +1)
#    plt.plot(xferpn[8:51], (2/len(erpnoise) * np.abs(erpnoisetest[8:51]) ** 2))
#    plt.title('Testing the weighted channels on the ERP post-noise')
#    
#        
#    plt.subplot(312)
#    yerp = fft(erpnoise, axis=0) 
#    xferpn = np.linspace(0.0, nyquist, nerpn // 2 +1)
#    plt.plot(xferpn[8:51], (2/len(erpnoise) * np.abs(yerp[8:51]) ** 2))
#    plt.title('Original unweighted ERP')
# 
#    Testing   
#   plt.figure()
#    plt.subplot(311)
#    xf = np.linspace(0.0, nyquist, nerp // 2 +1)
#    plt.plot(xf[8:51], (2/len(erptest) * np.abs(erptest[8:51]) ** 2))
#    plt.title('Testing the weighted channels on the ERP post-stimulus')
#    
#        
#    plt.subplot(312)
#    yferp = fft(y, axis=0) 
#    plt.plot(xf[8:51], (2/len(erptest) * np.abs(yferp[8:51]) ** 2))
#    plt.title('Original Unweighted ERP')
#
#    
#    # fft the trial estimate 1000ms after noise (25-35hz bins used)
#    plt.subplot(313)
#    plt.plot(xf[25:51], (2/1000 * np.abs(trialestimatestim[25:51,0:10]) ** 2))
#    plt.title('trial estimate for stim signals after fft using 25Hz-35Hz')
    
   
#    # Now use the weights to loop through indivial trials 
#    noise = pcdict['photonoise']
#    trialestimate = np.zeros((1000,360),dtype=complex)
#    for trial in finalgoodtrials: 
#        trialdata = np.squeeze(data[:,:,trial])
#        firstind = np.argmax(n[:, trial] > 0)
#        lastind = firstind + 1000
#        trialdata = trialdata[firstind:lastind,:]
#        trialfft = fft(trialdata, axis = 0)
#        trialweighted = np.matmul(trialfft,weightsn)
#        trialestimate[:,trial] = trialweighted[:,0] #new time series
#    
#    # fft the trial estimate 1000ms after noise (35-45hz bins)
#    plt.subplot(313)
#    xferpn = np.linspace(0.0, nyquist, nerp // 2 +1)
#    plt.plot(xferpn[20:51], (2/1000 * np.abs(trialestimate[20:51,:]) ** 2))
#    plt.title('trial estimate for noise signals after fft using 35Hz-45Hz')
#    
#    plt.tight_layout()
#    plt.show
