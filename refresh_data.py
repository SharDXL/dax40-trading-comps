import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import warnings, datetime
warnings.filterwarnings('ignore')

DAX40 = {
    'SAP.DE':('SAP SE','Technology'),'IFX.DE':('Infineon Technologies','Technology'),
    'SHL.DE':('Siemens Healthineers','Healthcare'),'SRT.DE':('Sartorius AG','Healthcare'),
    'MRK.DE':('Merck KGaA','Healthcare'),'BAYN.DE':('Bayer AG','Healthcare'),
    'FRE.DE':('Fresenius SE','Healthcare'),'QIA.DE':('Qiagen NV','Healthcare'),
    'SIE.DE':('Siemens AG','Industrials'),'ENR.DE':('Siemens Energy','Industrials'),
    'RHM.DE':('Rheinmetall AG','Industrials'),'MTX.DE':('MTU Aero Engines','Industrials'),
    'KGX.DE':('KION Group','Industrials'),'HEI.DE':('Heidelberg Materials','Industrials'),
    'BNR.DE':('Brenntag SE','Industrials'),'AIR.DE':('Airbus SE','Industrials'),
    'BMW.DE':('BMW AG','Automotive'),'MBG.DE':('Mercedes-Benz Group','Automotive'),
    'CON.DE':('Continental AG','Automotive'),'DTG.DE':('Daimler Truck','Automotive'),
    'PAH3.DE':('Porsche SE','Automotive'),'P911.DE':('Porsche AG','Automotive'),
    'VOW3.DE':('Volkswagen AG','Automotive'),
    'ALV.DE':('Allianz SE','Financials'),'MUV2.DE':('Munich Re','Financials'),
    'DBK.DE':('Deutsche Bank','Financials'),'CBK.DE':('Commerzbank','Financials'),
    'DB1.DE':('Deutsche Boerse','Financials'),'HNR1.DE':('Hannover Re','Financials'),
    'VNA.DE':('Vonovia SE','Financials'),
    'BAS.DE':('BASF SE','Chemicals'),'SY1.DE':('Symrise AG','Chemicals'),
    'BEI.DE':('Beiersdorf AG','Consumer'),'HEN3.DE':('Henkel AG','Consumer'),
    'ZAL.DE':('Zalando SE','Consumer'),'ADS.DE':('Adidas AG','Consumer'),
    'RWE.DE':('RWE AG','Energy'),'EOAN.DE':('E.ON SE','Energy'),
    'DTE.DE':('Deutsche Telekom','Telecom'),'DHL.DE':('Deutsche Post DHL','Logistics'),
}

records = []
failed = []
for ticker, (name, sector) in DAX40.items():
    try:
        info = yf.Ticker(ticker).info
        ev = info.get('enterpriseValue'); ebitda = info.get('ebitda')
        mktcap = info.get('marketCap'); pe = info.get('trailingPE'); rev = info.get('totalRevenue')
        ev_ebitda_direct = info.get('enterpriseToEbitda')
        ev_ebitda = round(ev_ebitda_direct,1) if ev_ebitda_direct else (round(ev/ebitda,1) if ev and ebitda and ebitda>0 else None)
        ev_rev = round(ev/rev,1) if ev and rev and rev>0 else None
        records.append({'Ticker':ticker,'Company':name,'Sector':sector,
            'EV (EUR bn)': round(ev/1e9,1) if ev else None,
            'EBITDA (EUR bn)': round(ebitda/1e9,1) if ebitda else None,
            'Revenue (EUR bn)': round(rev/1e9,1) if rev else None,
            'Mkt Cap (EUR bn)': round(mktcap/1e9,1) if mktcap else None,
            'EV/EBITDA (x)': ev_ebitda, 'EV/Revenue (x)': ev_rev,
            'P/E (x)': round(pe,1) if pe else None})
    except Exception as e:
        failed.append((ticker,str(e)))

df = pd.DataFrame(records)
flags = {'PAH3.DE':'N/M – holding co','ALV.DE':'N/M – insurer','MUV2.DE':'N/M – insurer',
    'HNR1.DE':'N/M – insurer','DBK.DE':'N/M – bank','CBK.DE':'N/M – bank','VNA.DE':'N/M – REIT',
    'BMW.DE':'EV adj. reqd','MBG.DE':'EV adj. reqd','VOW3.DE':'EV adj. reqd','DTG.DE':'EV adj. reqd','CON.DE':'EV adj. reqd'}
df['Data Flag'] = df['Ticker'].map(flags).fillna('OK')

print(f"Loaded {len(df)}/{len(DAX40)} companies. Failed: {failed}")

out_csv = f'dax40_trading_comps_{datetime.date.today():%Y%m}.csv'
    # remove older dated exports so only the latest is kept
import glob, os
for f in glob.glob('dax40_trading_comps_*.csv'):
    if f != out_csv:
        os.remove(f)
df.to_csv(out_csv, index=False)
print(f"Saved {out_csv}, {len(df)} rows")

df_clean = df[df['Data Flag']=='OK'].copy()
sector_medians = df_clean.groupby('Sector')['EV/EBITDA (x)'].median().sort_values(ascending=True)

fig, ax = plt.subplots(figsize=(10,6))
bars = ax.barh(sector_medians.index, sector_medians.values, color='steelblue', edgecolor='white')
for bar,val in zip(bars, sector_medians.values):
    ax.text(val+0.2, bar.get_y()+bar.get_height()/2, f'{val:.1f}x', va='center', fontsize=10, fontweight='bold')
ax.set_xlabel('Median EV/EBITDA (x)', fontsize=11)
ax.set_title('DAX 40 — Sector Median EV/EBITDA\n(Financials, REITs & captive-finance OEMs excluded)', fontsize=13, fontweight='bold', pad=15)
ax.axvline(df_clean['EV/EBITDA (x)'].median(), color='red', linestyle='--', linewidth=1.2, label='Overall median')
ax.legend(); ax.set_xlim(0, sector_medians.max()+4); ax.spines[['top','right']].set_visible(False)
plt.tight_layout(); plt.savefig('dax40_sector_medians.png', dpi=150, bbox_inches='tight'); plt.close()
print("Sector medians chart saved")

df_scatter = df_clean.dropna(subset=['EV/EBITDA (x)','P/E (x)']).copy()
sector_colors = {'Technology':'#2196F3','Healthcare':'#4CAF50','Industrials':'#FF9800','Consumer':'#9C27B0',
    'Chemicals':'#F44336','Energy':'#795548','Telecom':'#607D8B','Logistics':'#00BCD4','Automotive':'#FF5722'}
fig, ax = plt.subplots(figsize=(12,8))
for sector, group in df_scatter.groupby('Sector'):
    color = sector_colors.get(sector,'grey')
    ax.scatter(group['P/E (x)'], group['EV/EBITDA (x)'], color=color, s=80, label=sector, zorder=3)
    for _, row in group.iterrows():
        ax.annotate(row['Company'], (row['P/E (x)'], row['EV/EBITDA (x)']), textcoords='offset points', xytext=(6,4), fontsize=7.5, color='#333333')
med_pe = df_scatter['P/E (x)'].median(); med_evebitda = df_scatter['EV/EBITDA (x)'].median()
ax.axvline(med_pe, color='grey', linestyle='--', linewidth=0.9, alpha=0.7)
ax.axhline(med_evebitda, color='grey', linestyle='--', linewidth=0.9, alpha=0.7)
ax.set_xlabel('P/E (x)', fontsize=11); ax.set_ylabel('EV/EBITDA (x)', fontsize=11)
ax.set_title('DAX 40 — EV/EBITDA vs P/E\nClean comps universe, July 2026', fontsize=13, fontweight='bold', pad=15)
ax.legend(loc='upper right', fontsize=8, framealpha=0.5); ax.spines[['top','right']].set_visible(False)
plt.tight_layout(); plt.savefig('dax40_scatter.png', dpi=150, bbox_inches='tight'); plt.close()
print("Scatter chart saved")

# Print summary stats for README/conclusion
print("\n--- Sector medians ---")
print(sector_medians.to_string())
print("\n--- Cheapest 5 by EV/EBITDA ---")
print(df_clean.nsmallest(5,'EV/EBITDA (x)')[['Company','Sector','EV/EBITDA (x)']].to_string(index=False))
print("\n--- Most expensive 5 by EV/EBITDA ---")
print(df_clean.nlargest(5,'EV/EBITDA (x)')[['Company','Sector','EV/EBITDA (x)']].to_string(index=False))
