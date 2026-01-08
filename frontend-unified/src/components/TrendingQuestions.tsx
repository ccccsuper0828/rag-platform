import { TrendingUp, MessageCircle } from 'lucide-react';

const TrendingQuestions = () => {
  const trending = [
    { text: "How does the new consensus mechanism improve transaction speed?", count: "2.4k" },
    { text: "Explain the difference between zk-Rollups and Optimistic Rollups", count: "1.8k" },
    { text: "What are the requirements for becoming a DAO validator?", count: "1.2k" },
  ];

  return (
    <div data-cmp="TrendingQuestions" className="mt-8">
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
        <TrendingUp className="w-4 h-4" />
        Trending Questions
      </h3>
      <div className="grid gap-3">
        {trending.map((q, i) => (
          <button 
            key={i}
            className="text-left bg-card hover:bg-secondary border border-border hover:border-primary/30 p-3 rounded-xl transition-all group"
          >
            <div className="flex justify-between items-start gap-4">
              <p className="text-sm text-foreground font-medium group-hover:text-primary transition-colors">
                {q.text}
              </p>
              <div className="flex items-center gap-1 text-xs text-muted-foreground whitespace-nowrap bg-secondary px-1.5 py-0.5 rounded">
                <MessageCircle className="w-3 h-3" />
                {q.count}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default TrendingQuestions;