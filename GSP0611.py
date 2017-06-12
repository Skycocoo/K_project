# -*- coding: utf-8 -*-
"""
Created on Sun Jun 11 16:25:26 2017

@author: Dawnknight
"""

import cPickle,h5py
import numpy as np
import glob,os
from scipy.stats import pearsonr
from numpy.linalg import eig
from numpy.linalg import norm

#src_path = 'I:/AllData_0327/unified data array/'
src_path = './data/unified data array/'
Mfolder  = 'Unified_MData/'
Kfolder  = 'Unified_KData/'
Rfolder  = 'reliability/'

Mfile = glob.glob(os.path.join(src_path+Mfolder,'*.pkl'))

Jnum   = 6   # joint number
Tnum   = 1   # time interval
sigma  = 20
Rel_th = 0.7

distmtx    = np.zeros((Jnum*Tnum,Jnum*Tnum,len(Mfile)))
distmtx3   = np.zeros((Jnum*Tnum,Jnum*Tnum,3,len(Mfile)))
adjmtx     = np.zeros((Jnum*Tnum,Jnum*Tnum))
adjmtx_th  = np.zeros((Jnum*Tnum,Jnum*Tnum))
thmtx      = np.zeros((Jnum*Tnum,Jnum*Tnum))
degmtx     = np.zeros((Jnum*Tnum,Jnum*Tnum))
degmtx_x   = np.zeros((Jnum*Tnum,Jnum*Tnum))
degmtx_y   = np.zeros((Jnum*Tnum,Jnum*Tnum))
degmtx_z   = np.zeros((Jnum*Tnum,Jnum*Tnum))
degmtx_th  = np.zeros((Jnum*Tnum,Jnum*Tnum))
degmtx_xth = np.zeros((Jnum*Tnum,Jnum*Tnum))
degmtx_yth = np.zeros((Jnum*Tnum,Jnum*Tnum))
degmtx_zth = np.zeros((Jnum*Tnum,Jnum*Tnum))
Lapmtx     = np.zeros((Jnum*Tnum,Jnum*Tnum))
Lapmtx_th  = np.zeros((Jnum*Tnum,Jnum*Tnum))
L          = np.zeros((Jnum*Tnum))
Cidx       = np.arange(Jnum*Tnum)  #column idx
Ridx       = np.arange(Jnum*Tnum)  #row idx



thmtx[0,1] = 1
thmtx[1,2] = 1
thmtx[3,4] = 1
thmtx[4,5] = 1    
for i in range(Jnum):
    thmtx[i,i::Jnum] = 1



corrmtx3 = np.zeros([Jnum*Tnum,Jnum*Tnum,3,len(Mfile)])
corrmtx = np.zeros([Jnum*Tnum,Jnum*Tnum])

for midx,mfile in enumerate(Mfile):
    print mfile
    data = cPickle.load(file(mfile,'rb'))[12:30]
    data = data.reshape(-1,3,data.shape[1])
    if  Tnum != 1:   
        M = data[:,:,:-(Tnum-1)]
        for i in range(1,Tnum):
            M = np.vstack([M,np.roll(data,-i,axis = 2)[:,:,:-(Tnum-1)]])
    else:
        M = data    
    ### calculate correlation between joints
    for i in range(Jnum*Tnum-1):
        for j in range(i+1,Jnum*Tnum):
            corrmtx3[i,j,0,midx] = pearsonr(data[i,0,:],data[j,0,:])[0]
            corrmtx3[i,j,1,midx] = pearsonr(data[i,1,:],data[j,1,:])[0]
            corrmtx3[i,j,2,midx] = pearsonr(data[i,2,:],data[j,2,:])[0]
    ### calculate distant's weight between joints
    for idx in range(1,Jnum*Tnum/2+1):   # precisely should be np.round((Jnum*Tnum-1)/2.).astype('int')+1
        
        curRidx = np.roll(Ridx,-idx) 
        Diff = M - np.roll(M,-idx,axis = 0)
        Diff_abs = abs(Diff)
        L2   = np.mean((np.sum(Diff**2,axis = 1))**0.5,axis = 1)
        W    = np.exp(-L2/sigma**2)
        W_abs = np.mean(np.exp(-Diff_abs/sigma**2),axis = 2)
        for Lidx,(i,j) in enumerate(zip(Cidx,curRidx)):
            col = min(i,j)
            row = max(i,j)
            distmtx[col,row,midx]    = W[Lidx]
            distmtx3[col,row,0,midx] = W_abs[Lidx,0]
            distmtx3[col,row,1,midx] = W_abs[Lidx,1]
            distmtx3[col,row,2,midx] = W_abs[Lidx,2]


corrmtx3[0,3,2,:][np.isnan(corrmtx3[0,3,2,:])] = 1  # L and R should in Z axis's correlation
corrmtx3[np.isnan(corrmtx3)] = 0
corrmtx3[corrmtx3<.1] = 0

corrmtx[:] = np.mean(np.sum(corrmtx3**2,axis=2)**0.5,axis = 2)        
corrmtx_x  = np.mean(corrmtx3,axis = 3)[:,:,0]
corrmtx_y  = np.mean(corrmtx3,axis = 3)[:,:,1]
corrmtx_z  = np.mean(corrmtx3,axis = 3)[:,:,2]
   
adjmtx[:]    = np.mean(distmtx,axis=2)+ corrmtx
adjmtx_x     = np.mean(distmtx3,axis=3)[:,:,0]+ corrmtx_x
adjmtx_y     = np.mean(distmtx3,axis=3)[:,:,1]+ corrmtx_y
adjmtx_z     = np.mean(distmtx3,axis=3)[:,:,2]+ corrmtx_z

adjmtx_th[:]  = adjmtx*thmtx
adjmtx_xth = adjmtx_x*thmtx
adjmtx_yth = adjmtx_y*thmtx
adjmtx_zth = adjmtx_z*thmtx


adjmtx[:] = adjmtx + adjmtx.T
adjmtx_x  = adjmtx_x + adjmtx_x.T
adjmtx_y  = adjmtx_y + adjmtx_y.T
adjmtx_z  = adjmtx_z + adjmtx_z.T

adjmtx_th[:] = adjmtx_th + adjmtx_th.T
adjmtx_xth   = adjmtx_xth + adjmtx_xth.T
adjmtx_xth   = adjmtx_yth + adjmtx_yth.T
adjmtx_xth   = adjmtx_zth + adjmtx_zth.T
        

for i in range(Jnum*Tnum):
    degmtx[i,i]    = sum(adjmtx[i,:])
    degmtx_x[i,i]  = sum(adjmtx_x[i,:])
    degmtx_y[i,i]  = sum(adjmtx_z[i,:])
    degmtx_z[i,i]  = sum(adjmtx_y[i,:])

    degmtx_th[i,i]  = sum(adjmtx_th[i,:]) 
    degmtx_xth[i,i] = sum(adjmtx_xth[i,:])
    degmtx_yth[i,i] = sum(adjmtx_yth[i,:])
    degmtx_zth[i,i] = sum(adjmtx_zth[i,:])    
    
    
Lapmtx[:]    = degmtx - adjmtx    
Lapmtx_x     = degmtx_x - adjmtx_x
Lapmtx_y     = degmtx_y - adjmtx_y
Lapmtx_z     = degmtx_z - adjmtx_z

Lapmtx_th[:] = degmtx_th - adjmtx_th  
Lapmtx_xth   = degmtx_xth - adjmtx_xth  
Lapmtx_yth   = degmtx_yth - adjmtx_yth    
Lapmtx_zth   = degmtx_zth - adjmtx_zth
    
Eval,Evec         = eig(Lapmtx)
Eval_x,Evec_x     = eig(Lapmtx_x)
Eval_y,Evec_y     = eig(Lapmtx_y)
Eval_z,Evec_z     = eig(Lapmtx_z)

Eval_th,Evec_th   = eig(Lapmtx_th)   
Eval_xth,Evec_xth = eig(Lapmtx_xth)
Eval_yth,Evec_yth = eig(Lapmtx_yth)
Eval_zth,Evec_zth = eig(Lapmtx_zth)    
    

Rel_th = 0.7

for Kfile,Rfile in zip(glob.glob(os.path.join(src_path+Kfolder,'*ex4.pkl')),glob.glob(os.path.join(src_path+Rfolder,'*ex4.pkl'))):
    print Kfile
    Kdata = cPickle.load(file(Kfile,'rb'))[12:30,:]
    Rdata = cPickle.load(file(Rfile,'rb'))[4:10,:]
    unrelidx = np.where(np.sum((Rdata<Rel_th)*1,0)!=0)[0]   # frames which have unreliable  joints
    corKdata = np.zeros(Kdata.shape)
    corKdata += Kdata 
    
    for idx in unrelidx:
        x_coef = []
        y_coef = []
        z_coef = []    

        for i in range(Jnum*Tnum):
            x_coef.append(sum(Kdata[0::3,idx]*Evec_xth[:,i])/norm(Evec_xth[:,i]))   
            y_coef.append(sum(Kdata[1::3,idx]*Evec_yth[:,i])/norm(Evec_yth[:,i]))
            z_coef.append(sum(Kdata[2::3,idx]*Evec_zth[:,i])/norm(Evec_zth[:,i]))
        
        
        gamma = 0
        fx = np.zeros(6)
        fy = np.zeros(6)
        fz = np.zeros(6)
        
        for i in range(Jnum*Tnum):
            fx += (1/(1+gamma*Eval_xth)*x_coef)[i]*Evec_xth[:,i]
            fy += (1/(1+gamma*Eval_yth)*y_coef)[i]*Evec_yth[:,i]
            fz += (1/(1+gamma*Eval_zth)*z_coef)[i]*Evec_zth[:,i]    
          
        corKdata[0::3,idx] = fx
        corKdata[1::3,idx] = fy
        corKdata[2::3,idx] = fz

    fname ='./data/GSP/original/' +Kfile.split('\\')[-1][:-3]+'h5'
    f = h5py.File(fname,'w')
    f.create_dataset('data',data = corKdata)
    f.close()



  
Mdata = cPickle.load(file(src_path+Mfolder+'Andy_2016-12-15 04.15.27 PM_ex4_FPS30_motion_unified.pkl','rb'))[12:30,:]    
Kdata = cPickle.load(file(src_path+Kfolder+'Andy_data201612151615_unified_ex4.pkl','rb'))[12:30,:]
Rdata = cPickle.load(file(src_path+Rfolder+'Andy_data201612151615_Rel_ex4.pkl','rb'))[4:10]

    
idx = 127
x_coef = []
y_coef = []
z_coef = []


wn_x = 0
wn_y = 0
wn_z = 0

for i in range(6):
    wn_x +=  sum(((0.9*Evec_x)[:,i])**2)
    wn_y +=  sum(((0.9*Evec_y)[:,i])**2)
    wn_z +=  sum(((0.9*Evec_z)[:,i])**2)

for i in range(Jnum*Tnum):
    x_coef.append(sum(Kdata[0::3,idx]*Evec_x[:,i]*.9**2)/norm(Evec_x[:,i])/wn_x)   
    y_coef.append(sum(Kdata[1::3,idx]*Evec_y[:,i]*.9**2)/norm(Evec_y[:,i])/wn_y)
    z_coef.append(sum(Kdata[2::3,idx]*Evec_z[:,i]*.9**2)/norm(Evec_z[:,i])/wn_z)


gamma = 0.01
fx = np.zeros(6)
fy = np.zeros(6)
fz = np.zeros(6)

for i in range(Jnum*Tnum):
    fx += (1/(1+gamma*Eval_x)*x_coef)[i]*Evec_x[:,i]
    fy += (1/(1+gamma*Eval_y)*y_coef)[i]*Evec_y[:,i]
    fz += (1/(1+gamma*Eval_z)*z_coef)[i]*Evec_z[:,i]





#for i in range(Jnum*Tnum):
#    x_coef.append(sum(Kdata[0::3,idx]*Evec_x[:,i])/norm(Evec_x[:,i]))   
#    y_coef.append(sum(Kdata[1::3,idx]*Evec_y[:,i])/norm(Evec_y[:,i]))
#    z_coef.append(sum(Kdata[2::3,idx]*Evec_z[:,i])/norm(Evec_z[:,i]))
#
#
#gamma = 0.01
#fx = np.zeros(6)
#fy = np.zeros(6)
#fz = np.zeros(6)
#
#for i in range(Jnum*Tnum):
#    fx += (1/(1+gamma*Eval_x)*x_coef)[i]*Evec_x[:,i]
#    fy += (1/(1+gamma*Eval_y)*y_coef)[i]*Evec_y[:,i]
#    fz += (1/(1+gamma*Eval_z)*z_coef)[i]*Evec_z[:,i]
    
    
#import h5py
#f = h5py.File('evec.h5','w')
#f.create_dataset('data_x',data=Evec_x)    
#f.create_dataset('data_y',data=Evec_y)
#f.create_dataset('data_z',data=Evec_z)    
#f.close()    
    
    
    
    
    
    
    
    
    
    
    