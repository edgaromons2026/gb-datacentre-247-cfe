import pandas as pd, numpy as np, matplotlib as mpl
mpl.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import cartopy.crs as ccrs, cartopy.io.shapereader as shp, cartopy.feature as cf
mpl.rcParams.update({'font.family':'DejaVu Sans','font.size':7,'axes.edgecolor':'#c3c2b7','axes.labelcolor':'#0b0b0b','xtick.color':'#52514e','ytick.color':'#52514e','axes.titlesize':7.5,'axes.titleweight':'bold','savefig.dpi':600})
MM=1/25.4
Z=pd.read_csv('zones_summary.csv'); Z['wind']*=0.86; Y=pd.read_csv('annual_cf.csv'); R=pd.read_csv('droughts.csv')
# unique supply combos
Z['combo']=Z.solar_dup+'|'+Z.wind_dup
grp=Z.groupby('combo').agg(zones=('zone',lambda s:'/'.join(sorted(s,key=lambda x:(len(x),x)))),lat=('lat','first'),lon=('lon','first'),wlat=('wlat','first'),wlon=('wlon','first'),pv=('pv_fixed','first'),wind=('wind','first'),first=('zone','first')).sort_values('lat',ascending=False)
seqB=LinearSegmentedColormap.from_list('b',['#cde2fb','#86b6ef','#3987e5','#1c5cab','#0d366b'])
seqO=LinearSegmentedColormap.from_list('o',['#fde3d5','#f6a882','#eb6834','#b8481c','#7a2c0d'])
div=LinearSegmentedColormap.from_list('d',['#184f95','#5598e7','#f0efec','#e66767','#a32a2a'])
# ---------- Fig 1 ----------
def sites(sitecol,la,lo,val):
    g=Z.groupby(sitecol).agg(zones=('zone',lambda s:'/'.join(sorted(s,key=lambda x:(len(x),x)))),lat=(la,'first'),lon=(lo,'first'),v=(val,'first')).reset_index()
    return g
OFF={'Z1_2/Z1_3/Z1_4':(-6,4,'right'),'Z2/Z1_1':(6,2,'left'),'Z15':(6,3,'left'),'Z14/Z16':(6,-7,'left'),'Z14/Z15/Z16':(6,-3,'left'),'Z13/Z17':(-6,-6,'right'),'Z3/Z4':(6,-2,'left'),'Z4/Z5':(-6,-2,'right'),'Z12':(-6,0,'right')}
fig,axs=plt.subplots(1,2,figsize=(177*MM,120*MM),subplot_kw={'projection':ccrs.epsg(27700)})
land=cf.NaturalEarthFeature('cultural','admin_0_countries','10m')
for ax,(g,cm,title) in zip(axs,[(sites('solar_dup','lat','lon','pv_fixed'),seqO,'a  Fixed-tilt PV'),(sites('wind_dup','wlat','wlon','wind'),seqB,'b  Wind (V126, 100 m hub, 14% losses)')]):
    ax.set_extent([-7.8,2.2,49.8,60.0],ccrs.PlateCarree())
    ax.add_feature(land,facecolor='#f0efec',edgecolor='#898781',linewidth=0.3)
    ax.spines['geo'].set_edgecolor('#c3c2b7')
    sc=ax.scatter(g.lon,g.lat,c=g.v,cmap=cm,s=46,edgecolor='#fcfcfb',linewidth=1.0,transform=ccrs.PlateCarree(),zorder=3)
    for _,r in g.iterrows():
        dx,dy,ha=OFF.get(r.zones,(6,-2,'left'))
        ax.annotate(r.zones,(r.lon,r.lat),xycoords=ccrs.PlateCarree()._as_mpl_transform(ax),xytext=(dx,dy),textcoords='offset points',fontsize=5.5,color='#52514e',ha=ha)
    ax.set_title(title,loc='left')
    cb=fig.colorbar(sc,ax=ax,orientation='horizontal',fraction=0.04,pad=0.03); cb.set_label('Mean capacity factor, 2000–2024',fontsize=6.5); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=6)
fig.savefig('figs/Fig1_map.tif',bbox_inches='tight',pil_kwargs={'compression':'tiff_lzw'},dpi=300); fig.savefig('figs/Fig1_map.png',bbox_inches='tight',dpi=200)
# ---------- Fig 3 ----------
Y=Y.merge(Z[['zone','combo']],on='zone'); first=grp.set_index('first')
Yu=Y[Y.zone.isin(first.index)]
order=list(first.index)
lab=[first.loc[z,'zones'] for z in order]
fig=plt.figure(figsize=(177*MM,150*MM)); gs=fig.add_gridspec(3,2,width_ratios=[40,1],height_ratios=[1,1,0.8],hspace=0.45,wspace=0.03)
for i,(col,t) in enumerate([('wind','a  Wind capacity factor, anomaly from each zone’s 2000–2024 mean'),('pv_fixed','b  Fixed-tilt PV capacity factor, anomaly from each zone’s 2000–2024 mean')]):
    M=Yu.pivot(index='zone',columns='year',values=col).loc[order]
    A=(M.sub(M.mean(axis=1),axis=0)).div(M.mean(axis=1),axis=0)*100
    ax=fig.add_subplot(gs[i,0]); lim=np.nanmax(np.abs(A.values))
    im=ax.imshow(A.values,cmap=div,norm=TwoSlopeNorm(0,-lim,lim),aspect='auto')
    ax.set_yticks(range(len(order))); ax.set_yticklabels(lab,fontsize=5.8)
    ax.set_xticks(range(0,25,2)); ax.set_xticklabels(M.columns[::2],fontsize=6)
    ax.set_title(t,loc='left'); ax.tick_params(length=0)
    for s in ax.spines.values(): s.set_visible(False)
    cax=fig.add_subplot(gs[i,1]); cb=fig.colorbar(im,cax=cax); cb.set_label('% of mean',fontsize=6); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=5.5)
ax=fig.add_subplot(gs[2,0]); Ru=R[R.zone.isin(order)]
st=Ru.groupby('year').longest_low_days.agg(['median','min','max'])
ax.vlines(st.index,st['min'],st['max'],color='#86b6ef',linewidth=2)
ax.plot(st.index,st['median'],'o',color='#1c5cab',ms=4,mec='#fcfcfb',mew=1)
w=st['max'].idxmax(); ax.annotate(f'{w}: up to {int(st.loc[w,"max"])} days',(w,st.loc[w,'max']),xytext=(6,-2),textcoords='offset points',fontsize=6,color='#0b0b0b')
ax.set_xlim(1999.3,2024.7); ax.set_ylim(0,None); ax.set_ylabel('Longest spell (days)',fontsize=6.5)
ax.set_title('c  Longest run of days with wind–PV output below 30% of its mean: median (dot) and range across zones',loc='left')
ax.grid(axis='y',color='#e1e0d9',linewidth=0.5); ax.set_axisbelow(True)
for s in ['top','right']: ax.spines[s].set_visible(False)
ax.set_xticks(range(2000,2025,2)); ax.yaxis.set_major_locator(mpl.ticker.MaxNLocator(integer=True))
fig.savefig('figs/Fig3_variability.tif',bbox_inches='tight',pil_kwargs={'compression':'tiff_lzw'},dpi=300); fig.savefig('figs/Fig3_variability.png',bbox_inches='tight',dpi=200)
print(grp[['zones','pv','wind']].round(3).to_string()); print(st.to_string())
