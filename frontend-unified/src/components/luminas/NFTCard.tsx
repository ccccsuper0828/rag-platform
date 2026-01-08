import React from 'react';
import { ExternalLink, TrendingUp, User, DollarSign } from 'lucide-react';
import { NFT } from '../../types/nft';

interface NFTCardProps {
  nft?: NFT;
}

const NFTCard: React.FC<NFTCardProps> = ({
  nft = {
    tokenId: '#0000',
    ipfsCid: 'QmExample...',
    currentPrice: 0,
    isActive: false,
    salesCount: 0,
    totalRevenue: 0,
    ownerAddress: '0x0000...0000',
    lumosScore: 0,
    imageUrl: 'https://images.unsplash.com/photo-1618005198919-d3d4b5a92ead?w=400&h=400&fit=crop',
    name: 'NFT Item'
  }
}) => {
  console.log('NFTCard rendered:', nft.tokenId);

  const handleIPFSClick = () => {
    window.open(`https://ipfs.io/ipfs/${nft.ipfsCid}`, '_blank');
  };

  const truncateAddress = (address: string) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  return (
    <div 
      data-cmp="NFTCard" 
      className="bg-card rounded-xl overflow-hidden shadow-custom border border-border hover:shadow-lg transition-all hover:scale-[1.02]"
    >
      {/* NFT Image */}
      <div className="relative aspect-square bg-muted">
        <img 
          src={nft.imageUrl} 
          alt={nft.name || `NFT ${nft.tokenId}`}
          className="w-full h-full object-cover"
        />
        {/* Lumos Score Badge */}
        <div className="absolute top-3 right-3 bg-gradient-to-br from-primary to-yellow-500 text-primary-foreground px-3 py-1.5 rounded-lg shadow-lg">
          <div className="flex items-center space-x-1">
            <TrendingUp size={14} />
            <span className="text-sm font-bold">Lumos: {nft.lumosScore}</span>
          </div>
        </div>
        {/* Status Badge */}
        <div className="absolute top-3 left-3">
          {nft.isActive ? (
            <div className="bg-green-500 text-white px-3 py-1 rounded-full text-xs font-semibold flex items-center space-x-1">
              <span>✅</span>
              <span>Active</span>
            </div>
          ) : (
            <div className="bg-muted-foreground/50 text-white px-3 py-1 rounded-full text-xs font-semibold flex items-center space-x-1">
              <span>⚪</span>
              <span>Inactive</span>
            </div>
          )}
        </div>
      </div>

      {/* NFT Details */}
      <div className="p-5 space-y-3">
        {/* Token ID */}
        <div>
          <h3 className="text-base font-semibold text-foreground">{nft.name || `NFT ${nft.tokenId}`}</h3>
          <p className="text-sm text-muted-foreground">Token ID: {nft.tokenId}</p>
        </div>

        {/* IPFS CID */}
        <div className="flex items-center justify-between p-2 bg-muted rounded-lg">
          <span className="text-xs font-mono text-muted-foreground truncate flex-1">
            {nft.ipfsCid.length > 20 ? `${nft.ipfsCid.slice(0, 20)}...` : nft.ipfsCid}
          </span>
          <button
            onClick={handleIPFSClick}
            className="ml-2 p-1 hover:bg-primary/10 rounded transition-colors"
            title="View on IPFS"
          >
            <ExternalLink size={16} className="text-primary" />
          </button>
        </div>

        {/* Current Price */}
        <div className="flex items-center justify-between p-3 bg-gradient-to-r from-primary/10 to-blue-500/10 rounded-lg">
          <div className="flex items-center space-x-2">
            <DollarSign size={18} className="text-primary" />
            <span className="text-sm font-medium text-foreground">Current Price</span>
          </div>
          <span className="text-base font-semibold text-primary">{nft.currentPrice} UTIL</span>
        </div>

        {/* Sales Statistics */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-muted rounded-lg">
            <p className="text-xs text-muted-foreground mb-1">Sales Count</p>
            <p className="text-base font-semibold text-foreground">{nft.salesCount}</p>
          </div>
          <div className="p-3 bg-muted rounded-lg">
            <p className="text-xs text-muted-foreground mb-1">Total Revenue</p>
            <p className="text-base font-semibold text-primary">{nft.totalRevenue} UTIL</p>
          </div>
        </div>

        {/* Owner Address */}
        <div className="flex items-center space-x-2 p-2 bg-muted rounded-lg">
          <User size={16} className="text-muted-foreground" />
          <span className="text-xs font-mono text-muted-foreground">
            Owner: {truncateAddress(nft.ownerAddress)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default NFTCard;