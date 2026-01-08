export interface NFT {
  tokenId: string;
  ipfsCid: string;
  currentPrice: number;
  isActive: boolean;
  salesCount: number;
  totalRevenue: number;
  ownerAddress: string;
  lumosScore: number;
  imageUrl?: string;
  name?: string;
}

export interface PlatformStats {
  totalNftsMinted: number;
  totalTradingVolume: number;
  platformTotalRevenue: number;
  activeNftRate: number;
}

export interface UserStats {
  nftsOwned: number;
  totalEarnings: number;
  purchasedNfts: NFT[];
}

export interface DashboardData {
  platformStats: PlatformStats;
  userStats: UserStats;
  allNfts: NFT[];
}