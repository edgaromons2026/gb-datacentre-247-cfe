import pandas as pd, numpy as np
D='/mnt/user-data/uploads/corrected_v1/'
s=pd.read_csv(D+'sites_with_altitude.csv')
z=s.pivot_table(index='zone',columns='tech',values='site',aggfunc='first').reset_index()
dup=s.pivot_table(index='zone',columns='tech',values='duplicate_of',aggfunc='first')
loc=s.pivot_table(index='zone',columns='tech',values=['lat','lon'],aggfunc='first')
gsp=s.groupby('zone').gsp.first()
def rd(p,c):
    d=pd.read_csv(p,index_col=0,usecols=['time_utc']+c); d.index=pd.to_datetime(d.index,utc=True); return d
cache={}
rows=[];yr=[];dr=[]
for _,r in z.iterrows():
    ps=dup.loc[r.zone,'solar']; ws=dup.loc[r.zone,'wind']
    # wind file: use the zone's own wind site name; mapping to staged file by duplicate
    pk=ps.replace('_solar',''); wk=ws.replace('_solar','').replace('_wind','')
    pvf=D+f'pv/{pk}_solar_pv_cf_2000_2025.csv'
    wf=D+f'wind/{wk}_wind_wind_cf_2000_2025.csv'
    if pvf not in cache: cache[pvf]=rd(pvf,['pv_cf_fixed','pv_cf_single_axis'])
    if wf not in cache: cache[wf]=rd(wf,['wind_cf_v126_100m'])
    d=cache[pvf].join(cache[wf],how='inner'); d=d[d.index.year<=2024]
    a=d.groupby(d.index.year).mean()
    for y,v in a.iterrows(): yr.append(dict(zone=r.zone,year=y,pv_fixed=v.pv_cf_fixed,pv_track=v.pv_cf_single_axis,wind=v.wind_cf_v126_100m))
    p=0.5*d.wind_cf_v126_100m/d.wind_cf_v126_100m.mean()+0.5*d.pv_cf_fixed/d.pv_cf_fixed.mean()
    day=p.resample('1D').mean(); low=(day<0.3)
    for y in range(2000,2025):
        l=low[low.index.year==y].astype(int).values; best=cur=0
        for x in l: cur=cur+1 if x else 0; best=max(best,cur)
        dr.append(dict(zone=r.zone,year=y,longest_low_days=best,low_days=int(l.sum())))
    rows.append(dict(zone=r.zone,gsp=gsp[r.zone],solar_site=r.solar,wind_site=r.wind,lat=loc.loc[r.zone,('lat','solar')],lon=loc.loc[r.zone,('lon','solar')],wlat=loc.loc[r.zone,('lat','wind')],wlon=loc.loc[r.zone,('lon','wind')],
      pv_fixed=a.pv_cf_fixed.mean(),pv_track=a.pv_cf_single_axis.mean(),wind=a.wind_cf_v126_100m.mean(),wind_min=a.wind_cf_v126_100m.min(),wind_max=a.wind_cf_v126_100m.max(),pv_min=a.pv_cf_fixed.min(),pv_max=a.pv_cf_fixed.max(),solar_dup=ps,wind_dup=ws))
Z=pd.DataFrame(rows); Y=pd.DataFrame(yr); R=pd.DataFrame(dr)
Z.to_csv('zones_summary.csv',index=False); Y.to_csv('annual_cf.csv',index=False); R.to_csv('droughts.csv',index=False)
pd.set_option('display.width',250)
print(Z[['zone','gsp','solar_site','wind_site','pv_fixed','pv_track','wind','wind_min','wind_max']].round(3).to_string())
print(R.groupby('zone').longest_low_days.agg(['median','max']).T.to_string())
l=pd.read_csv(D+'load/Z10_Nottingham_solar_load_kw_2000_2025.csv',index_col=0); print('load mean kW',l.load_kw.mean(), l.load_kw.max(), l.load_kw.min())
