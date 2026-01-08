import React from 'react';
import { Coins, TrendingUp, DollarSign, Activity, Wallet, Award } from 'lucide-react';
import StatCard from '../components/luminas/StatCard';
import AssetsPanel from '../components/luminas/AssetsPanel';
import { DashboardData } from '../types/nft';

const Dashboard: React.FC = () => {
  console.log('Dashboard page rendered');

  // Sample dashboard data with 10 NFTs
  const dashboardData: DashboardData = {
    platformStats: {
      totalNftsMinted: 10000,
      totalTradingVolume: 2450000,
      platformTotalRevenue: 122500,
      activeNftRate: 78.5
    },
    userStats: {
      nftsOwned: 15,
      totalEarnings: 45600,
      purchasedNfts: []
    },
    allNfts: [
      {
        tokenId: '#8848',
        ipfsCid: 'QmYwAPJzv5CZsnAzt8auVZRn5rdGYB2CwJ',
        currentPrice: 1250,
        isActive: true,
        salesCount: 12,
        totalRevenue: 15000,
        ownerAddress: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb6',
        lumosScore: 92,
        imageUrl: 'https://images.unsplash.com/photo-1618005198919-d3d4b5a92ead?w=400&h=400&fit=crop',
        name: 'Cosmic Gateway'
      },
      {
        tokenId: '#7721',
        ipfsCid: 'QmPKzq8TdKvEWbBBKZqLwV8kKxLzJHsFnP',
        currentPrice: 2100,
        isActive: true,
        salesCount: 8,
        totalRevenue: 16800,
        ownerAddress: '0x8Ba1f109551bD432803012645Ac136ddd64DBA72',
        lumosScore: 88,
        imageUrl: 'https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?w=400&h=400&fit=crop',
        name: 'Digital Aurora'
      },
      {
        tokenId: '#6534',
        ipfsCid: 'QmT5NvUtoM5nWFfrQdVrFtvGfKFmG7AHE1',
        currentPrice: 890,
        isActive: true,
        salesCount: 15,
        totalRevenue: 13350,
        ownerAddress: '0x3Cd751E6b0078Be393132286c442345e5DC49699',
        lumosScore: 85,
        imageUrl: 'https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?w=400&h=400&fit=crop',
        name: 'Neon Dreams'
      },
      {
        tokenId: '#5412',
        ipfsCid: 'QmRK3JbVXnW8mSWzTvGkLz4Jp9wHxLqMnB',
        currentPrice: 3200,
        isActive: true,
        salesCount: 5,
        totalRevenue: 16000,
        ownerAddress: '0x1aD91ee08f21bE3dE0BA2ba6918E714dA6B45836',
        lumosScore: 95,
        imageUrl: 'https://images.unsplash.com/photo-1618172193622-ae2d025f4032?w=400&h=400&fit=crop',
        name: 'Ethereal Vision'
      },
      {
        tokenId: '#4289',
        ipfsCid: 'QmXoypizjW3WknFiJnKLwHCnL72vedxjQk',
        currentPrice: 1580,
        isActive: false,
        salesCount: 20,
        totalRevenue: 31600,
        ownerAddress: '0x9fB29AAc15b9A4B7F17c3385939b007540f4d791',
        lumosScore: 76,
        imageUrl: 'https://images.unsplash.com/photo-1635322966219-b75ed372eb01?w=400&h=400&fit=crop',
        name: 'Quantum Flux'
      },
      {
        tokenId: '#3156',
        ipfsCid: 'QmQjK5hMNNjTkNYvZDdx8Ea7xFmRvVbLmH',
        currentPrice: 2750,
        isActive: true,
        salesCount: 9,
        totalRevenue: 24750,
        ownerAddress: '0x4B20993Bc481177ec7E8f571ceCaE8A9e22C02db',
        lumosScore: 90,
        imageUrl: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&h=400&fit=crop',
        name: 'Stellar Harmony'
      },
      {
        tokenId: '#2034',
        ipfsCid: 'QmUNLLsPACCz1vLxQVkXqqLX5R2X4fCTd',
        currentPrice: 950,
        isActive: true,
        salesCount: 18,
        totalRevenue: 17100,
        ownerAddress: '0x6C6Bc977E13Df9b0de53b251522280BB72383700',
        lumosScore: 82,
        imageUrl: 'https://images.unsplash.com/photo-1618172193763-c511deb635ca?w=400&h=400&fit=crop',
        name: 'Prism Light'
      },
      {
        tokenId: '#1923',
        ipfsCid: 'QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6K',
        currentPrice: 4100,
        isActive: true,
        salesCount: 3,
        totalRevenue: 12300,
        ownerAddress: '0x0E3A09dDA6B20aFbB34aC7cD4A6881493f3E7bf7',
        lumosScore: 97,
        imageUrl: 'https://images.unsplash.com/photo-1634193295627-1cdddf751ebf?w=400&h=400&fit=crop',
        name: 'Celestial Crown'
      },
      {
        tokenId: '#0812',
        ipfsCid: 'QmYHNYAaYK6JbmFzS7NjmvDLxdD1Hx6hTN',
        currentPrice: 1325,
        isActive: false,
        salesCount: 14,
        totalRevenue: 18550,
        ownerAddress: '0x14dC79964da2C08b23698B3D3cc7Ca32193d9955',
        lumosScore: 79,
        imageUrl: 'https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?w=400&h=400&fit=crop',
        name: 'Void Walker'
      },
      {
        tokenId: '#0145',
        ipfsCid: 'QmZchBnKFBjWHLvLhq4z5KQ9LkXj8qYw2M',
        currentPrice: 1890,
        isActive: true,
        salesCount: 11,
        totalRevenue: 20790,
        ownerAddress: '0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f',
        lumosScore: 86,
        imageUrl: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&h=400&fit=crop',
        name: 'Genesis Spark'
      }
    ]
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="w-full max-w-[1440px] mx-auto px-8 py-8 space-y-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-bold text-foreground bg-gradient-to-r from-primary to-yellow-500 bg-clip-text text-transparent mb-2">
            Lumina Assets Dashboard
          </h1>
          <p className="text-muted-foreground">NFT Product Management Platform</p>
        </div>

        {/* Platform Statistics */}
        <div>
          <h2 className=" font-bold text-foreground mb-4">Platform Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="Total NFTs Minted"
              value={dashboardData.platformStats.totalNftsMinted.toLocaleString()}
              icon={Coins}
              gradient="from-primary to-purple-600"
            />
            <StatCard
              title="Total Trading Volume"
              value={`${dashboardData.platformStats.totalTradingVolume.toLocaleString()} UTIL`}
              icon={TrendingUp}
              gradient="from-blue-500 to-cyan-500"
            />
            <StatCard
              title="Platform Total Revenue"
              value={`${dashboardData.platformStats.platformTotalRevenue.toLocaleString()} UTIL`}
              icon={DollarSign}
              gradient="from-green-500 to-emerald-500"
            />
            <StatCard
              title="Active NFT Rate"
              value={`${dashboardData.platformStats.activeNftRate}%`}
              icon={Activity}
              gradient="from-orange-500 to-red-500"
            />
          </div>
        </div>

        {/* User Personal Statistics */}
        <div>
          <h2 className=" font-semibold text-foreground mb-4">Your Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatCard
              title="NFTs Owned"
              value={dashboardData.userStats.nftsOwned}
              subtitle="In your collection"
              icon={Wallet}
              gradient="from-primary to-blue-500"
            />
            <StatCard
              title="Total Earnings"
              value={`${dashboardData.userStats.totalEarnings.toLocaleString()} UTIL`}
              subtitle="From NFT sales"
              icon={Award}
              gradient="from-green-500 to-emerald-600"
            />
            <StatCard
              title="Purchase History"
              value={dashboardData.userStats.purchasedNfts.length}
              subtitle="NFTs purchased"
              icon={TrendingUp}
              gradient="from-purple-500 to-pink-500"
            />
          </div>
        </div>

        {/* NFT Assets Grid */}
        <AssetsPanel 
          nfts={dashboardData.allNfts}
          title="All NFT Assets" 
        />
      </div>
    </div>
  );
};

export default Dashboard;