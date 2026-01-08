import { ExternalLink, BookOpen, Clock } from 'lucide-react';

const CitationsList = () => {
  const citations = [
    {
      id: 1,
      title: "Understanding Blockchain Consensus Mechanisms",
      source: "Knowledge Graph Node #892",
      trust: "High Verified",
      time: "2h ago"
    },
    {
      id: 2,
      title: "DeepSeek Model Architecture Documentation v2.1",
      source: "Technical Docs",
      trust: "Official",
      time: "1d ago"
    },
    {
      id: 3,
      title: "DAO Governance Proposal: Q3 Allocation",
      source: "Governance Forum",
      trust: "Community",
      time: "3d ago"
    }
  ];

  return (
    <div data-cmp="CitationsList" className="bg-card rounded-2xl border border-border overflow-hidden shadow-sm h-full flex flex-col">
      <div className="p-4 border-b border-border bg-secondary/30 flex justify-between items-center">
        <h3 className="font-semibold text-foreground flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-primary" />
          Citations
        </h3>
        <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">
          {citations.length} Sources
        </span>
      </div>
      
      <div className="p-2 space-y-1 flex-1 overflow-y-auto">
        {citations.map((item) => (
          <div 
            key={item.id} 
            className="group p-3 rounded-xl hover:bg-secondary transition-colors border border-transparent hover:border-border cursor-pointer"
          >
            <div className="flex justify-between items-start mb-1">
              <h4 className="text-sm font-medium text-foreground line-clamp-1 group-hover:text-primary transition-colors">
                {item.title}
              </h4>
              <ExternalLink className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground font-medium bg-secondary px-1.5 py-0.5 rounded group-hover:bg-white transition-colors">
                {item.source}
              </span>
              <div className="flex items-center gap-2 text-muted-foreground">
                <span className="text-green-600 font-medium">{item.trust}</span>
                <span className="w-1 h-1 bg-muted-foreground rounded-full"></span>
                <span className="flex items-center gap-0.5">
                  <Clock className="w-3 h-3" /> {item.time}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="p-3 border-t border-border bg-secondary/10">
        <button className="w-full py-2 text-sm text-primary font-medium hover:bg-primary/5 rounded-lg transition-colors">
          Show More Sources
        </button>
      </div>
    </div>
  );
};

export default CitationsList;