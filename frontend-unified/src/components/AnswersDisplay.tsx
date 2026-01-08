import { CheckCircle2, FileText, Share2, ThumbsUp, ThumbsDown, Copy } from 'lucide-react';

const AnswerDisplay = () => {
  return (
    <div data-cmp="AnswerDisplay" className="bg-card rounded-2xl border border-border shadow-custom overflow-hidden">
      {/* Answer Header */}
      <div className="p-4 border-b border-border flex justify-between items-center bg-secondary/20">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
            <svg className="w-5 h-5 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 14a1 1 0 1 1 1-1 1 1 0 0 1-1 1zm1-4.37V13h-2v-1.37a2 2 0 0 1 1.25-1.92l.6-.21a2 2 0 0 0 1.15-1.93 2.15 2.15 0 0 0-4.3 0H8a4.15 4.15 0 0 1 8.3 0 4 4 0 0 1-2.3 3.84l-.59.2a.58.58 0 0 0-.41.59z"/>
            </svg>
          </div>
          <span className="font-semibold text-foreground">AI Answer</span>
        </div>
        <button className="text-xs font-medium text-primary hover:text-primary/80 flex items-center gap-1 border border-primary/20 bg-primary/5 px-3 py-1.5 rounded-full transition-colors">
          <FileText className="w-3 h-3" />
          View Metadata
        </button>
      </div>

      {/* Answer Content */}
      <div className="p-6">
        <div className="prose prose-sm md:prose-base dark:prose-invert max-w-none text-foreground/90">
          <p className="mb-4 leading-relaxed">
            Based on the analysis of the available knowledge graph nodes, 
            <span className="text-primary font-medium cursor-pointer hover:underline mx-1">[Node #892]</span> 
            and recent governance proposals, the new implementation of the consensus mechanism introduces a hybrid Proof-of-Stake model.
          </p>
          <p className="mb-4 leading-relaxed">
            This shift significantly reduces block validation time by approximately 45%, as detailed in the
            <span className="text-primary font-medium cursor-pointer hover:underline mx-1">[Technical Docs v2.1]</span>. 
            The updated protocol leverages sharding technology to parse transactions in parallel buckets rather than sequentially.
          </p>
          <ul className="list-disc pl-5 mb-4 space-y-1">
            <li>Reduced gas fees by ~30%</li>
            <li>Increased throughput to 15,000 TPS</li>
            <li>Enhanced security via verifiable delay functions</li>
          </ul>
          <p className="text-sm text-muted-foreground italic border-l-2 border-primary/30 pl-3">
            Note: This data is verified against the latest on-chain records from Block 18,293,441.
          </p>
        </div>
      </div>

      {/* Answer Actions */}
      <div className="px-6 py-3 border-t border-border bg-secondary/10 flex items-center justify-between">
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
          <span>Verified by 3 nodes</span>
        </div>
        <div className="flex items-center gap-2">
          <button className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-md transition-colors">
            <Copy className="w-4 h-4" />
          </button>
          <div className="h-4 w-px bg-border"></div>
          <button className="p-1.5 text-muted-foreground hover:text-green-600 hover:bg-green-50 rounded-md transition-colors">
            <ThumbsUp className="w-4 h-4" />
          </button>
          <button className="p-1.5 text-muted-foreground hover:text-red-600 hover:bg-red-50 rounded-md transition-colors">
            <ThumbsDown className="w-4 h-4" />
          </button>
          <div className="h-4 w-px bg-border"></div>
          <button className="p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-md transition-colors">
            <Share2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default AnswerDisplay;