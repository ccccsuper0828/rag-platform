import React from 'react';
import NFTCard from './NFTCard';
import { NFT } from '../../types/nft';

interface AssetsPanelProps {
  nfts?: NFT[];
  title?: string;
}

const AssetsPanel: React.FC<AssetsPanelProps> = ({
  nfts = [],
  title = 'Lumina Assets'
}) => {
  console.log('AssetsPanel rendered with', nfts.length, 'NFTs');

  return (
    <div data-cmp="AssetsPanel" className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className=" font-semibold text-foreground mb-4">{title}</h2>
        <span className="text-muted-foreground">{nfts.length} Items</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {nfts.map((nft) => (
          <NFTCard key={nft.tokenId} nft={nft} />
        ))}
      </div>

      {nfts.length === 0 && (
        <div className="text-center py-12 bg-card rounded-lg border border-border">
          <p className="text-muted-foreground">No NFTs to display</p>
        </div>
      )}
    </div>
  );
};

export default AssetsPanel;