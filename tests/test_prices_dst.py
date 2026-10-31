import sys, os, tempfile; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); TMP = tempfile.gettempdir()  # local fix: was /mnt/project-files and /tmp
import pandas as pd, numpy as np
from gbtea import prices
# synthetic MIP file: 2024-03-30..04-01 (spring DST 31 Mar = 46 periods) and 2024-10-27 (50 periods)
rows=[]
for d,n in [("30-Mar-24",48),("31-Mar-24",46),("01-Apr-24",48),("26-Oct-24",48),("27-Oct-24",50),("28-Oct-24",48)]:
    for k in range(n): rows.append((d, float(k+1)))  # price = settlement period number
pd.DataFrame(rows,columns=["Date","Market_Index_Price_GBP_MWh"]).to_csv(os.path.join(TMP, "mip.csv"),index=False)
h,rep=prices.load_mip(os.path.join(TMP, "mip.csv"))
print(rep)
# On 31 Mar 2024 local midnight = 00:00 UTC (GMT). SP1-2 -> hour ending 01:00 UTC mean 1.5
print(h["2024-03-31 00:00":"2024-03-31 03:00"])
# On 1 Apr local midnight BST = 31 Mar 23:00 UTC; SP1,2 -> hour ending 1 Apr 00:00 UTC = 1.5
print(h["2024-03-31 22:00":"2024-04-01 01:00"])
# Oct 27: local midnight BST = 26 Oct 23:00 UTC; 50 periods end 27 Oct 24:00 UTC
print(h["2024-10-26 22:00":"2024-10-27 01:00"]); print(h["2024-10-27 23:00":"2024-10-28 01:00"])
