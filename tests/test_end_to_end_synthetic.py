import sys, os, tempfile; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); TMP = tempfile.gettempdir()  # local fix: was /mnt/project-files and /tmp
import numpy as np, pandas as pd, pvlib, shutil
from pathlib import Path
from gbtea import config as C
root=Path(TMP)/"fakedrive"; shutil.rmtree(root,ignore_errors=True)
C.ERA5_2000_2025=root/"e2000"; C.ERA5_2015_2025=root/"e2015"; C.MIDAS_DIR=root/"midas"; C.OUT=root/"out"
for d in (C.ERA5_2000_2025,C.ERA5_2015_2025,C.MIDAS_DIR): d.mkdir(parents=True)
C.OPTIMAL_SITES=Path(TMP)/"opt.csv"; C.MIDAS_STATIONS=C.MIDAS_DIR/"st.csv"
pd.DataFrame([dict(Zone_ID="Z10",GSP_Name="Staythorpe",Solar_Latitude=52.95,Solar_Longitude=-1.16,Solar_Site_Name="Nottingham",
 Wind_Latitude=52.95,Wind_Longitude=-1.16,Wind_Site_Name="Nottingham",Distance_GSP_Solar_km=24,Distance_GSP_Wind_km=24)]).to_csv(C.OPTIMAL_SITES,index=False)
idx=pd.date_range("2016-06-01 01:00","2016-07-01 00:00",freq="1h")
mid=pd.DatetimeIndex(idx,tz="UTC")-pd.Timedelta("30min")
loc=pvlib.location.Location(52.95,-1.16); cs=loc.get_clearsky(mid); sp=loc.get_solarposition(mid)
cosz=np.cos(np.radians(sp.zenith.values)).clip(0)
k=0.6; direct=cs.dni.values*cosz*0.5; diffuse=cs.ghi.values*k-direct; diffuse=np.clip(diffuse,0,None)
vals=dict(InfluxDirect=direct,InfluxDiffuse=diffuse,GHI=direct+diffuse,WindSpeed100m=np.full(len(idx),8.),WindRoughness=np.full(len(idx),.1),
  Albedo=np.full(len(idx),.2),Temperature=np.full(len(idx),288.),Dew_Temperature=np.full(len(idx),283.),InfluxTOA=np.full(len(idx),0.))
for v,a in vals.items():
    for folder,span,cols in ((C.ERA5_2000_2025,"2000_2025",["Z10_Nottingham_solar","Z10_Nottingham_wind"]),(C.ERA5_2015_2025,"2015_2025",[" ABERDARON "," ALDERGROVE "])):
        df=pd.DataFrame({"Datetime":idx.strftime("%Y-%m-%d %H:%M:%S"),**{c:a for c in cols},"Year":2016})
        df.to_csv(folder/f"ERA5_{v}_{span}.csv")
st=pd.DataFrame(dict(Name=[" ABERDARON "," ALDERGROVE "],Latitude=[52.8,54.66],Longitude=[-4.74,-6.22],Altitude=[95,63],Timezone="Europe/London"))
st.to_csv(C.MIDAS_STATIONS,index=False)
for f,a in [("final_ghi_2015_2025.csv",(direct+diffuse)*3.6*1.05),("final_wind_speed_2015_2025.csv",np.full(len(idx),11.)),
            ("final_air_temperature_2015_2025.csv",np.full(len(idx),15.)),("final_relative_humidity_2015_2025.csv",np.full(len(idx),70.)),
            ("final_station_pressure_2015_2025.csv",np.full(len(idx),1010.))]:
    pd.DataFrame({" ABERDARON ":a," ALDERGROVE ":a},index=pd.Index(idx,name="Datetime")).to_csv(C.MIDAS_DIR/f)
from gbtea import run
run._elevation=lambda a,b: 40.0
s=run.step_sites(); print(s[["site","era5_col","alt","duplicate_of"]])
run.step_era5_profiles(s)
v=run.step_validation(); print(v.filter(regex="station|years|_r$|_mbe$").T)
print(sorted(p.name for p in C.OUT.rglob("*.csv")))
