import { Sparkles, TrendingUp, Gem } from 'lucide-react';
import { Area, AreaChart, ResponsiveContainer, Tooltip, YAxis } from 'recharts';

const data = [
  { value: 6.5 }, { value: 7.2 }, { value: 7.8 }, { value: 7.5 }, 
  { value: 8.2 }, { value: 8.0 }, { value: 8.5 }
];

const LumosPanel = () => {
  return (
    <div data-cmp="LumosPanel" className="bg-gradient-to-br from-card to-secondary/50 rounded-2xl border border-border p-5 shadow-custom relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none"></div>
      
      <div className="flex items-start justify-between mb-6 relative z-10">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-5 h-5 text-yellow-500 fill-yellow-500" />
            <h3 className="font-semibold text-foreground">LUMOS Score</h3>
          </div>
          <p className="text-sm text-muted-foreground">Conversation Value Spark</p>
        </div>
        <div className="flex flex-col items-end">
          <span className="text-3xl font-bold text-foreground">8.5<span className="text-lg text-muted-foreground font-normal">/10</span></span>
          <div className="flex items-center gap-1 text-xs text-green-600 font-medium bg-green-50 px-1.5 py-0.5 rounded">
            <TrendingUp className="w-3 h-3" />
            <span>+12% Trend</span>
          </div>
        </div>
      </div>

      <div className="h-24 w-full mb-6 relative z-10 -mx-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.2}/>
                <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <YAxis hide domain={['dataMin - 1', 'dataMax + 1']} />
            <Tooltip 
              contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '12px' }}
              itemStyle={{ color: 'var(--primary)' }}
              cursor={{ stroke: 'var(--border)', strokeWidth: 1 }}
            />
            <Area 
              type="monotone" 
              dataKey="value" 
              stroke="var(--primary)" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorValue)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between gap-4 relative z-10 border-t border-border pt-4">
        <div className="text-xs text-muted-foreground">
          <span className="block font-medium text-foreground">Next Milestone</span>
          <span>9.0 score unlocks Tier 2 items</span>
        </div>
        <button className="flex items-center gap-2 bg-foreground text-background hover:bg-foreground/90 px-4 py-2 rounded-lg font-medium text-sm transition-all shadow-lg active:scale-95">
          <Gem className="w-4 h-4" />
          Mint NFT
        </button>
      </div>
    </div>
  );
};

export default LumosPanel;